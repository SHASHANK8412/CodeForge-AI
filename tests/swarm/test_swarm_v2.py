"""
Swarm Intelligence v2: contract-aware integration and bounded, evidence-based repair.

Fast tests run the real plan / harness.mjs / evaluation / classification / repair code on the test-only
LocalRuntime (fixed sample code, host uvicorn + host node; it reports itself as not isolated, so the isolation
gate is declared not required for those engines). The genuine tests at the end run the production DockerRuntime:
the backend in the Chaos sandbox's internal network and the generated client in node:20-slim.
"""

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from backend.swarm import findings, interfaces, runtime as rt
from backend.swarm.models import Contract, Endpoint
from backend.swarm.service import SwarmEngine, SwarmError, SwarmStore, _hash
from tests.swarm.local_runtime import LocalRuntime
from tests.swarm.sample import (BACKEND_V2, BACKEND_V2_INSECURE, BACKEND_V2_LIST, BACKEND_V2_MISSING_FIELD,
                                BACKEND_V2_STATUS_200, BACKEND_V2_TEXT, BACKEND_V2_WRONG_TYPE, CLIENT_V2, CLIENT_V2_STRING_QTY,
                                CLIENT_V2_THROWS, CLIENT_V2_WRONG, CONTRACT, CONTRACT_V2, staged_agents, write_sample)


@pytest.fixture
def project(tmp_path):
    return write_sample(tmp_path / "shop")


def autopilot(tmp_path):
    from backend.evolution.autopilot.service import AutopilotService
    from backend.evolution.autopilot.store import AutopilotStore
    return AutopilotService(AutopilotStore(tmp_path / "autopilot"), background=False)


def engine(tmp_path, gen, runtime=LocalRuntime, require_isolation=False):
    ap = autopilot(tmp_path)
    return SwarmEngine(SwarmStore(tmp_path / "swarm"), background=False, generate=gen, runtime=runtime,
                       require_isolation=require_isolation, autopilot=ap), ap


def mission(eng, project, contract=CONTRACT_V2, settings=None):
    m = eng.create("p1", "u1", "orders API and its frontend client", contract, settings=settings)
    eng.run("p1", project, "u1", m.id, approved=True)
    return eng.store.get("p1", "missions", m.id)


def contract_run(tmp_path, backend, client, contract=CONTRACT_V2, runtime=None):
    """One integration-testing run of the given components (no agents), and its findings."""
    ws = write_sample(tmp_path / "ws")
    files = {"backend/main.py": backend, "frontend/src/api/client.js": client}
    for rel, content in files.items():
        (ws / rel).parent.mkdir(parents=True, exist_ok=True)
        (ws / rel).write_text(content, encoding="utf-8")
    c = contract.model_dump()
    run = rt.run_contract_tests(runtime or LocalRuntime(), ws, files, c, interfaces.routes({"backend/main.py": backend}),
                                interfaces.client_exports({"frontend/src/api/client.js": client}), require_isolation=False)
    run["id"] = "rt_test"
    return run, findings.from_runtime("swm_t", 1, run, {"backend_artifact": "art_b", "frontend_artifact": "art_f"})


def check(run, cid):
    return next(c for c in run["checks"] if c["id"] == cid)


def tree_digest(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob("*") if p.is_file()}


# 1 request-schema mismatch ------------------------------------------------------------------------------------------
def test_request_schema_mismatch_is_detected_at_runtime(tmp_path):
    run, fs = contract_run(tmp_path, BACKEND_V2, CLIENT_V2_STRING_QTY)
    c = check(run, "client:createOrder")
    assert c["status"] == "failed" and "quantity: '1' is not of type 'integer'" in c["observed"]
    sent = json.loads(c["requests"][0]["body"])
    assert sent == {"item": "example-item", "quantity": "1"}                    # what actually went over the wire
    f = next(x for x in fs if x.evidence.get("check") == "client:createOrder")
    assert (f.category, f.responsible, f.status, f.basis, f.confidence) == ("request_contract_mismatch", "frontend", "verified", "runtime", "high")
    assert check(run, "e0:valid")["status"] == "passed"                          # the backend itself conforms


# 2 response-schema mismatch -----------------------------------------------------------------------------------------
def test_response_schema_mismatch_is_detected(tmp_path):
    run, fs = contract_run(tmp_path, BACKEND_V2_LIST, CLIENT_V2)
    c = check(run, "e1:valid")
    assert c["status"] == "failed" and any("is not of type 'object'" in p["detail"] for p in c["problems"])
    f = next(x for x in fs if x.evidence.get("check") == "e1:valid")
    assert (f.category, f.responsible, f.status) == ("response_schema_mismatch", "backend", "verified")


# 3 incorrect HTTP status ---------------------------------------------------------------------------------------------
def test_incorrect_status_code_is_detected_and_runtime_decides(tmp_path):
    run, fs = contract_run(tmp_path, BACKEND_V2_STATUS_200, CLIENT_V2)
    c = check(run, "e0:valid")
    assert c["status"] == "failed" and c["problems"][0]["category"] == "http_status_mismatch" and "status 200" in c["observed"]
    f = next(x for x in fs if x.evidence.get("check") == "e0:valid")
    assert f.responsible == "backend" and f.status == "verified" and f.expected.startswith("status 201")
    props = findings.properties(CONTRACT_V2.model_dump(), interfaces.routes({"backend/main.py": BACKEND_V2_STATUS_200}),
                                run["declared"], run["checks"])["POST /api/orders"]["success_status"]
    assert props == {"contract": ["201"], "static": 200, "declared": ["200", "422"], "verified": 200, "decided_by": "runtime"}


# 4 incorrect content type --------------------------------------------------------------------------------------------
def test_incorrect_content_type_is_detected(tmp_path):
    run, fs = contract_run(tmp_path, BACKEND_V2_TEXT, CLIENT_V2)
    c = check(run, "e1:valid")
    assert c["status"] == "failed" and any("content type 'text/plain" in p["detail"] for p in c["problems"])
    assert any(f.category == "response_schema_mismatch" and f.responsible == "backend" for f in fs)


# 5 missing required response fields ----------------------------------------------------------------------------------
def test_missing_required_response_field_is_detected(tmp_path):
    run, _ = contract_run(tmp_path, BACKEND_V2_MISSING_FIELD, CLIENT_V2)
    assert any("'quantity' is a required property" in p["detail"] for p in check(run, "e1:valid")["problems"])
    assert check(run, "e0:valid")["status"] == "passed"


# 6 invalid response field types -------------------------------------------------------------------------------------
def test_invalid_response_field_type_is_detected(tmp_path):
    run, _ = contract_run(tmp_path, BACKEND_V2_WRONG_TYPE, CLIENT_V2)
    assert any("id: '1' is not of type 'integer'" in p["detail"] for p in check(run, "e0:valid")["problems"])


# 7 frontend-to-backend contract incompatibility -------------------------------------------------------------------------
def test_frontend_backend_incompatibility_is_found_statically_and_verified_at_runtime(tmp_path):
    run, fs = contract_run(tmp_path, BACKEND_V2, CLIENT_V2_WRONG)
    c = check(run, "client:createOrder")
    assert c["requests"][0]["path"] == "/api/order" and c["requests"][0]["status"] == 404
    assert "not in the contract (nearest contract operation: POST /api/orders)" in c["observed"]
    assert "'quantity' is a required property" in c["observed"]
    f = next(x for x in fs if x.evidence.get("check") == "client:createOrder")
    assert f.responsible == "frontend" and f.status == "verified"
    calls = interfaces.match(interfaces.client_calls({"c.js": CLIENT_V2_WRONG}), interfaces.routes({"backend/main.py": BACKEND_V2}))
    static = findings.from_static("swm_t", 1, CONTRACT_V2.model_dump(), interfaces.routes({"backend/main.py": BACKEND_V2}), calls, {})
    assert any(s.category == "request_contract_mismatch" and s.status == "unverified" and s.basis == "static" for s in static)
    # a client that throws on a conforming response is a frontend integration error
    run2, fs2 = contract_run(tmp_path / "b", BACKEND_V2, CLIENT_V2_THROWS)
    assert any(f.category == "frontend_integration_error" and f.responsible == "frontend" for f in fs2)


# 8 correct responsibility assignment --------------------------------------------------------------------------------------
def test_only_the_responsible_component_is_repaired(tmp_path, project):
    gen = staged_agents(backend=(BACKEND_V2_STATUS_200, BACKEND_V2))
    eng, _ = engine(tmp_path, gen)
    m = mission(eng, project)
    assert m.outcome == "SUCCEEDED", (m.error, [(f.category, f.observed) for f in m.findings if f.status != "repaired"])
    assert gen.calls == {"backend": 2, "frontend": 1}
    c = m.conflicts[0]
    assert c.decision["selected"] == "p_backend" and c.status == "resolved"
    assert any(p.violates for p in c.proposals if p.id == "p_client")
    first = [f for f in m.findings if f.round == 1 and f.basis == "runtime"]
    assert first and {f.responsible for f in first if f.status == "repaired"} == {"backend"}
    assert "status 200" in gen.prompts["backend"][1] and "e0:valid" in gen.prompts["backend"][1]   # evidence in the request


# 9 ambiguous responsibility -> a person ------------------------------------------------------------------------------------
def test_both_components_departing_goes_to_human_review_with_an_autopilot_plan(tmp_path, project):
    gen = staged_agents(backend=(BACKEND_V2_STATUS_200,), client=(CLIENT_V2_STRING_QTY,))
    eng, ap = engine(tmp_path, gen)
    m = mission(eng, project)
    assert m.status == "awaiting_decision" and m.outcome == "NEEDS_HUMAN_REVIEW" and m.phase == "AUTOPILOT_REVIEW"
    assert gen.calls == {"backend": 1, "frontend": 1}                            # nothing was repaired automatically
    c = m.conflicts[-1]
    assert c.status == "escalated" and "both components" in c.decision["reason"]
    assert {p.id for p in c.proposals} == {"p_client", "p_backend", "p_both"}
    assert {f.status for f in m.findings if f.round == 1 and f.basis == "runtime"} == {"needs_human_review"}
    plan = ap.store.get("p1", "plans", m.delivery["autopilot_plan_id"])
    assert plan.status.value == "awaiting_approval" and all(t.strategy == "manual" and not t.contents for t in plan.tasks)
    assert m.autopilot_review["unresolved_findings"] and m.autopilot_review["project_modified"] is False


def test_escalation_finishes_its_review_before_run_returns(tmp_path, project):
    """Regression: the escalating task wrote the review plan after flipping the status, and run() could return
    before the plan existed (found as a flaky failure of the test above). A slow review makes it deterministic."""
    import time as _time
    gen = staged_agents(backend=(BACKEND_V2_STATUS_200,), client=(CLIENT_V2_STRING_QTY,))
    eng, ap = engine(tmp_path, gen)
    original = eng._review

    def slow_review(project_id, mission_id):
        _time.sleep(1.5)
        return original(project_id, mission_id)
    eng._review = slow_review
    m = mission(eng, project)
    assert m.outcome == "NEEDS_HUMAN_REVIEW" and m.delivery.get("autopilot_plan_id")
    assert ap.store.get("p1", "plans", m.delivery["autopilot_plan_id"]).status.value == "awaiting_approval"
    assert next(t for t in m.tasks if t.id == "t5").status == "awaiting_review"


# 10 successful repair --------------------------------------------------------------------------------------------------------
def test_successful_repair_cycle(tmp_path, project):
    gen = staged_agents(client=(CLIENT_V2_WRONG, CLIENT_V2))
    eng, ap = engine(tmp_path, gen)
    m = mission(eng, project)
    assert m.outcome == "SUCCEEDED" and m.status == "completed", m.error
    assert len(m.repairs) == 1
    r = m.repairs[0]
    assert (r.component, r.requested_by, r.author, r.outcome) == ("frontend", "integration_agent", "frontend_agent", "succeeded")
    assert r.changed_files == ["frontend/src/api/client.js"] and r.artifact_before and r.artifact_after and r.completed_at
    assert r.validation["mismatches_remaining"] == [] and set(r.validation["runtime_counts"]) == {"passed"}
    assert all(v == "passed" for v in r.validation["gates_after_repair"].values())
    assert "POST /api/order" in r.request and "Follow the contract exactly" in r.request
    assert any(f.status == "repaired" and f.repair_attempt == r.id for f in m.findings)
    phases = [p["phase"] for p in m.phase_history]
    order = ["CONTRACT_READY", "PARALLEL_GENERATION", "STATIC_VALIDATION", "INTEGRATION_TESTING", "FAILURE_CLASSIFICATION",
             "REPAIR_REQUIRED", "REVALIDATION", "SECURITY_VERIFICATION", "AUTOPILOT_REVIEW"]
    firsts = [phases.index(x) for x in order]                                  # every phase, in lifecycle order
    assert firsts == sorted(firsts) and phases[-1] == "AUTOPILOT_REVIEW", phases
    gates = {g.name: g for g in m.gates}
    assert gates["runtime contract tests"].status == "passed" and gates["isolation and cleanup"].status == "not_applicable"
    assert not gates["isolation and cleanup"].mandatory and "test harness" in gates["isolation and cleanup"].detail


# 11 failed repair ------------------------------------------------------------------------------------------------------------
def test_failed_repair_stops_for_a_person(tmp_path, project):
    gen = staged_agents(client=(CLIENT_V2_WRONG,))                              # the repair does not fix it
    eng, _ = engine(tmp_path, gen)
    m = mission(eng, project)
    assert m.outcome == "NEEDS_HUMAN_REVIEW" and gen.calls["frontend"] == 2
    r = m.repairs[0]
    assert r.outcome == "failed" and r.validation["mismatches_remaining"]
    assert any(f.status == "repair_failed" for f in m.findings if f.round == 2)
    assert "automatic repair" in m.conflicts[-1].decision["reason"]


# 12 repair-attempt limits ----------------------------------------------------------------------------------------------------
def test_one_automatic_repair_per_mismatch_even_with_more_rounds_allowed(tmp_path, project):
    gen = staged_agents(client=(CLIENT_V2_WRONG,))
    eng, _ = engine(tmp_path, gen)
    m = mission(eng, project, settings={"max_repair_rounds": 3})
    assert gen.calls["frontend"] == 2 and len(m.repairs) == 1 and m.outcome == "NEEDS_HUMAN_REVIEW"
    gen0 = staged_agents(client=(CLIENT_V2_WRONG, CLIENT_V2))
    eng0, _ = engine(tmp_path / "zero", gen0)
    m0 = mission(eng0, project, settings={"max_repair_rounds": 0})
    assert gen0.calls["frontend"] == 1 and not m0.repairs and m0.outcome == "NEEDS_HUMAN_REVIEW"


# 13 artifact version preservation --------------------------------------------------------------------------------------------
def test_repairs_create_new_versions_and_keep_the_old_ones(tmp_path, project):
    gen = staged_agents(client=(CLIENT_V2_WRONG, CLIENT_V2))
    eng, _ = engine(tmp_path, gen)
    m = mission(eng, project)
    versions = [a for a in m.artifacts if a.task_id == "t3" and a.kind == "source_files"]
    assert len(versions) == 2 and versions[1].supersedes == versions[0].id
    assert versions[0].content["files"]["frontend/src/api/client.js"] == CLIENT_V2_WRONG       # never overwritten
    assert versions[1].content["files"]["frontend/src/api/client.js"] == CLIENT_V2
    calls = [a for a in m.artifacts if a.task_id == "t3" and a.kind == "client_calls"]
    assert len(calls) == 2 and calls[0].content["items"][0]["path"] == "/api/order"         # behaviour re-extracted
    assert m.autopilot_review["frontend_version"]["version"] == 2
    assert m.autopilot_review["frontend_version"]["artifact"] == versions[1].id


# 14 provenance integrity ---------------------------------------------------------------------------------------------------
def test_provenance_is_complete_and_hashes_match(tmp_path, project):
    gen = staged_agents(client=(CLIENT_V2_WRONG, CLIENT_V2))
    eng, _ = engine(tmp_path, gen)
    m = mission(eng, project)
    agent_of = {t.id: t.agent for t in m.tasks}
    for a in m.artifacts:
        assert a.content_hash == _hash(a.content) and a.revision == m.base_revision
        assert a.creator == agent_of[a.task_id], (a.kind, a.creator, a.task_id)
    rounds = m.runtime
    assert [r["round"] for r in rounds] == [1, 2]
    v1, v2 = [a.id for a in m.artifacts if a.task_id == "t3" and a.kind == "source_files"]
    assert rounds[0]["artifacts"]["frontend_artifact"] == v1 and rounds[1]["artifacts"]["frontend_artifact"] == v2
    assert m.contract.revision() == m.autopilot_review["contract_version"]


# 15 security re-check after repair -----------------------------------------------------------------------------------------
def test_security_is_checked_again_after_a_repair(tmp_path, project):
    gen = staged_agents(backend=(BACKEND_V2_STATUS_200, BACKEND_V2_INSECURE))     # the repair fixes the status, adds a vuln
    eng, ap = engine(tmp_path, gen)
    m = mission(eng, project)
    sec = next(g for g in m.gates if g.name.startswith("security"))
    assert sec.status == "failed" and sec.evidence["rechecked_after_repairs"] == [m.repairs[0].id]
    assert m.outcome == "FAILED" and m.repairs[0].outcome == "succeeded"           # the mismatch was repaired ...
    assert m.repairs[0].validation["security_after_repair"] == "failed"            # ... but the security gate failed
    sf = [f for f in m.findings if f.category == "security_violation"]
    assert sf and sf[0].status == "needs_human_review" and "not verified" in sf[0].recommended_correction
    assert m.delivery.get("kind") == "review" and not any(t.contents for t in ap.store.get("p1", "plans", m.delivery["autopilot_plan_id"]).tasks)


# 16 Docker timeout and cleanup -----------------------------------------------------------------------------------------------
class FakeDocker:
    """Records docker invocations; the node harness container hangs (TimeoutExpired)."""

    def __init__(self, hang=True):
        self.calls, self.removed, self.hang = [], False, hang

    def __call__(self, *args, timeout=60):
        self.calls.append(args)
        out = ""
        if args[:2] == ("ps", "-a"):
            out = "" if self.removed else "c1\nc2\n"
        if args[:2] == ("rm", "-f") and "c1" in args:
            self.removed = True
        if args and args[0] == "run" and "node" in args and self.hang:
            raise subprocess.TimeoutExpired(args, timeout)
        if args[:2] == ("network", "ls"):
            out = ""
        return subprocess.CompletedProcess(args, 0, out, "")


def test_docker_timeout_is_reported_and_everything_is_cleaned_up(tmp_path, monkeypatch):
    import backend.chaos.sandbox as sb
    import backend.execution.docker_test_sandbox as dts
    fake = FakeDocker()
    monkeypatch.setattr(sb, "_docker", fake)
    monkeypatch.setattr(dts, "docker_available", lambda: True)
    monkeypatch.setattr(sb.Sandbox, "wait_healthy", lambda self, target, budget: 0.5)
    run, fs = contract_run(tmp_path, BACKEND_V2, CLIENT_V2, runtime=rt.DockerRuntime(exec_timeout_s=5))
    assert run["status"] == "timeout" and "exceeded 5s" in run["error"] and run["checks"] == []
    flat = [" ".join(a) for a in fake.calls]
    assert any(a.startswith("network create --internal") for a in flat)
    node = next(a for a in fake.calls if a[0] == "run" and "node" in a)
    assert "--cap-drop" in node and "--read-only" in node and "--network" in node and node[node.index("timeout") + 1] == "5"
    assert any(a.startswith("rm -f c1 c2") for a in flat) and any(a.startswith("network rm") for a in flat)
    assert run["cleanup"]["verified"] is True
    assert [(f.category, f.status) for f in fs] == [("test_infrastructure_failure", "blocked")]


def test_without_docker_the_mission_is_blocked_not_skipped(tmp_path, project, monkeypatch):
    import backend.execution.docker_test_sandbox as dts
    monkeypatch.setattr(dts, "docker_available", lambda: False)
    eng, ap = engine(tmp_path, staged_agents(), runtime=rt.DockerRuntime, require_isolation=True)
    m = mission(eng, project)
    assert m.status == "blocked" and m.outcome == "BLOCKED"
    assert m.runtime[-1]["status"] == "blocked" and m.runtime[-1]["checks"] == []
    assert next(t for t in m.tasks if t.id == "t5").status == "blocked" and next(t for t in m.tasks if t.id == "t6").status == "blocked"
    assert any(f.category == "test_infrastructure_failure" and f.status == "blocked" for f in m.findings)
    assert not m.delivery and "Docker" in " ".join(m.autopilot_review["proposed_actions"])


# 17 flaky-test classification --------------------------------------------------------------------------------------------------
def test_a_check_that_passes_only_on_rerun_is_flaky_not_passed(tmp_path, project):
    def tamper(raw, call_no):
        if call_no == 1:                                    # the first execution sees a server error
            for d in raw["direct"]:
                if d["id"] == "e1:valid":
                    d["status"], d["body"] = 500, "Internal Server Error"
        return raw
    run, fs = contract_run(tmp_path, BACKEND_V2, CLIENT_V2, runtime=LocalRuntime(tamper=tamper))
    c = check(run, "e1:valid")
    assert run["rerun"] is True and c["status"] == "flaky" and c["rerun"]["status"] == "passed"
    f = next(x for x in fs if x.evidence.get("check") == "e1:valid")
    assert f.status == "unresolved" and f.responsible is None and "flaky" in f.observed
    eng, _ = engine(tmp_path / "m", staged_agents(), runtime=lambda: LocalRuntime(tamper=tamper))
    m = mission(eng, project)
    assert m.outcome == "NEEDS_HUMAN_REVIEW" and not m.repairs                    # never treated as a pass


# 18 Autopilot approval requirements ------------------------------------------------------------------------------------------------
def test_success_produces_an_autopilot_plan_awaiting_approval_and_nothing_else(tmp_path, project):
    eng, ap = engine(tmp_path, staged_agents())
    with pytest.raises(SwarmError, match="approve"):
        eng.run("p1", project, "u1", eng.create("p1", "u1", "orders", CONTRACT_V2).id, approved=False)
    m = mission(eng, project)
    assert m.outcome == "SUCCEEDED"
    plan = ap.store.get("p1", "plans", m.delivery["autopilot_plan_id"])
    assert plan.status.value == "awaiting_approval" and plan.origin == "swarm" and plan.origin_ref == m.id
    assert plan.tasks[0].strategy == "write_files" and "frontend/src/api/client.js" in plan.tasks[0].contents
    review = m.autopilot_review
    for k in ("objective", "contract_version", "backend_version", "frontend_version", "contract_validation", "generated_tests",
              "integration_tests", "security", "repair_history", "unresolved_findings", "evidence_refs", "proposed_actions",
              "approval_status"):
        assert k in review, k
    assert review["project_modified"] is False and review["deployed"] is False and plan.id in review["approval_status"]
    assert eng.deliver("p1", "u1", m.id).delivery["autopilot_plan_id"] == plan.id          # no second plan
    assert len(ap.store.list("p1", "plans")) == 1


# 19 no direct writes to the user's project ------------------------------------------------------------------------------------------
def test_the_project_is_never_written(tmp_path, project):
    before = tree_digest(project)
    for i, gen in enumerate((staged_agents(client=(CLIENT_V2_WRONG, CLIENT_V2)), staged_agents(client=(CLIENT_V2_WRONG,)))):
        eng, _ = engine(tmp_path / str(i), gen)
        mission(eng, project)
        assert tree_digest(project) == before


# 20 regression: v1 contracts and the existing behaviour --------------------------------------------------------------------------
def test_v1_contracts_are_upgraded_and_v1_missions_still_work(tmp_path, project):
    e = Endpoint(method="POST", path="/api/x/{x_id}", request_fields=["a", "b"], response_fields=["id"])
    assert e.request_schema == {"type": "object", "properties": {"a": {}, "b": {}}, "required": ["a", "b"]}
    assert e.responses["200"]["schema"]["required"] == ["id"] and e.path_params == {"x_id": {}} and "422" in e.errors
    assert Endpoint(**e.model_dump()) == e                                         # the upgrade is idempotent
    v2 = Endpoint(method="GET", path="/y", responses={"201": {"content_type": "application/json", "schema": {"type": "object"}}})
    assert v2.response_fields == [] and v2.request_schema is None
    with pytest.raises(ValueError):
        Endpoint(method="GET", path="/y", auth="cookie")
    bad = Contract(endpoints=[Endpoint(method="GET", path="/z", responses={"abc": {"schema": {"type": "nope"}}})])
    errors = SwarmEngine._validate("contract", bad.model_dump())
    assert any("invalid status code" in x for x in errors) and any("not a valid JSON Schema" in x for x in errors)
    # the v1 sample contract (field names only) runs end to end, with runtime evidence
    from tests.swarm.sample import scripted_agents
    eng, _ = engine(tmp_path, scripted_agents())
    m = mission(eng, project, contract=CONTRACT)
    assert m.outcome == "SUCCEEDED" and m.runtime[-1]["counts"] == {"passed": 7}
    assert {c["id"] for c in m.runtime[-1]["checks"]} == {
        "e0:valid", "e0:missing_required_field", "e0:malformed_body", "e1:valid",
        "e1:invalid_path_param",                    # order_id type is open in v1: the backend's declared int is used
        "client:createOrder", "client:getOrder"}
    assert "open property types filled from the backend's declared model" in " ".join(m.runtime[0]["plan"]["hints"])


def test_api_exposes_findings_repairs_and_the_report(tmp_path, project, monkeypatch):
    import backend.routes.export as export
    import backend.swarm.routes as routes
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from backend.auth.dependencies import get_current_user
    from backend.generation.store import global_generation_store
    eng, _ = engine(tmp_path, staged_agents(client=(CLIENT_V2_WRONG, CLIENT_V2)))
    monkeypatch.setattr(routes, "global_swarm_engine", eng)
    monkeypatch.setattr(global_generation_store, "get", lambda gid, default=None: {"generation_id": "g", "user_id": "alice",
                        "status": "completed", "project_path": str(project)} if gid == "g" else default)
    monkeypatch.setattr(export, "_safe_project_dir", lambda p: project if p == str(project) else None)
    app = FastAPI()
    app.include_router(routes.swarm_router)
    app.dependency_overrides[get_current_user] = lambda: {"id": "alice"}
    api = TestClient(app)
    base = "/api/projects/g/swarm/missions"
    m = api.post(base, json={"objective": "orders API v2", "contract": CONTRACT_V2.model_dump()}).json()["mission"]
    assert api.post(f"{base}/{m['id']}/run", json={"approved": True}).status_code == 202
    done = api.get(f"{base}/{m['id']}").json()["mission"]
    assert done["outcome"] == "SUCCEEDED" and done["repairs"] and done["findings"] and done["runtime"]
    md = api.get(f"{base}/{m['id']}/report").text
    assert "Repair history" in md and "SUCCEEDED" in md and "rt_" in md
    js = api.get(f"{base}/{m['id']}/report?format=json").json()
    assert js["autopilot_review"]["outcome"] == "SUCCEEDED"
    assert api.post(base, json={"objective": "bad contract", "contract": {"endpoints": [{"method": "GET", "path": "/a",
                                                                                         "auth": "magic"}]}}).status_code == 422


def test_the_page_shows_v2_results():
    root = Path(__file__).resolve().parents[2] / "frontend" / "src"
    page = (root / "pages" / "SwarmPage.jsx").read_text(encoding="utf-8")
    for text in ("Findings", "Repair history", "runtime contract", "Autopilot review", "phase_history", "outcome"):
        assert text in page, text
    assert "/report" in (root / "services" / "swarm.js").read_text(encoding="utf-8")


# genuine: Docker ------------------------------------------------------------------------------------------------------------------
def _docker_ok():
    try:
        from backend.execution.docker_test_sandbox import docker_available
        return docker_available()
    except Exception:
        return False


@pytest.mark.skipif(not _docker_ok(), reason="Docker is not available: the genuine v2 mission was NOT run")
def test_genuine_contract_aware_mission_in_docker(tmp_path, project, monkeypatch):
    """The backend first answers POST with 200 (the contract says 201). In Docker: the runtime contract tests
    find it, the Backend Agent repairs it once with the evidence, the re-run in a fresh isolated environment
    passes, isolation and cleanup are inspected from Docker, and the result is an Autopilot plan awaiting
    approval."""
    from backend.chaos.sandbox import LABEL, _docker
    monkeypatch.setenv("AIFORGE_TEST_SANDBOX", "docker")
    gen = staged_agents(backend=(BACKEND_V2_STATUS_200, BACKEND_V2))
    eng, ap = engine(tmp_path, gen, runtime=rt.DockerRuntime, require_isolation=True)
    m = mission(eng, project)
    gates = {g.name: g for g in m.gates}
    assert m.outcome == "SUCCEEDED", (m.error, [(g.name, g.status, g.detail[:300]) for g in m.gates],
                                      [(r.get("status"), r.get("error"), r.get("counts")) for r in m.runtime])
    first, last = m.runtime[0], m.runtime[-1]
    assert first["environment"].startswith("Docker") and check(first, "e0:valid")["status"] == "failed"
    assert last["counts"] == {"passed": len(last["checks"])} and last["harness"]["node"].startswith("v20")
    assert all(not x["reachable"] for x in last["egress"]) and last["isolation"]["verified"] is True
    assert last["cleanup"]["verified"] and first["cleanup"]["verified"]
    assert gates["isolation and cleanup"].status == "passed" and gates["isolation and cleanup"].mandatory
    assert gates["runtime contract tests"].status == "passed"
    assert gates["project and contract tests"].evidence["environment"].startswith("Docker")
    assert m.repairs[0].component == "backend" and m.repairs[0].outcome == "succeeded" and gen.calls == {"backend": 2, "frontend": 1}
    assert ap.store.get("p1", "plans", m.delivery["autopilot_plan_id"]).status.value == "awaiting_approval"
    for r in m.runtime:                                                         # nothing left behind by any run
        assert _docker("ps", "-a", "-q", "--filter", f"label={LABEL}={r['sandbox_id']}", timeout=30).stdout.strip() == ""
        assert _docker("network", "ls", "-q", "--filter", f"name=aiforge_chaos_{r['sandbox_id']}", timeout=30).stdout.strip() == ""
