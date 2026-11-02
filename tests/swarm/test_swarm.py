"""
AIForge Swarm Intelligence tests. Missions run for real: the scheduler, isolated agent workspaces, artifact
validation, code-level interface extraction, the Critical Reviewer, consensus, the Integration Agent and the
verification gates (project tests + a generated contract test, Security Guardian). Only the coding model is
replaced by fixed agent answers (tests/swarm/sample.py). Fast tests use the local test sandbox; the genuine
test at the end runs the tests in Docker.
"""

import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.swarm import consensus, interfaces, registry
from backend.swarm.models import Contract, Endpoint, Proposal, Task
from backend.swarm.service import SwarmEngine, SwarmError, SwarmStore
from tests.swarm.sample import BACKEND, BACKEND_TESTS, CLIENT_FIXED, CLIENT_WRONG, CONTRACT, scripted_agents, write_sample


@pytest.fixture
def project(tmp_path):
    return write_sample(tmp_path / "shop")


def engine(tmp_path, gen=None, background=False, autopilot=None):
    """Integration tests run on the test-only LocalRuntime (tests/swarm/local_runtime.py), which reports itself as
    not isolated; the isolation gate is therefore declared not required here. The genuine Docker tests use the
    production DockerRuntime with isolation required."""
    from backend.evolution.autopilot.service import AutopilotService
    from backend.evolution.autopilot.store import AutopilotStore
    from tests.swarm.local_runtime import LocalRuntime
    ap = autopilot or AutopilotService(AutopilotStore(tmp_path / "autopilot"), background=False)
    return SwarmEngine(SwarmStore(tmp_path / "swarm"), background=background, generate=gen or scripted_agents(),
                       runtime=LocalRuntime, require_isolation=False, autopilot=ap)


def run_mission(eng, project, contract=CONTRACT, settings=None):
    m = eng.create("p1", "u1", "orders API and its frontend client", contract, settings=settings)
    eng.run("p1", project, "u1", m.id, approved=True)
    return eng.store.get("p1", "missions", m.id)


# 1 task graph and capabilities -----------------------------------------------------------------------------------
def test_mission_controller_builds_a_valid_dependency_graph(tmp_path):
    m = engine(tmp_path).create("p1", "u1", "orders", CONTRACT)
    deps = {t.id: t.depends_on for t in m.tasks}
    assert m.status == "planned" and deps["t2"] == ["t1"] and deps["t3"] == ["t1"] and set(deps["t5"]) == {"t2", "t3", "t4"}
    assert {t.id: t.agent for t in m.tasks}["t3"] == "frontend_agent" and all(t.agent for t in m.tasks)
    assert next(t for t in m.tasks if t.id == "t6").retry_limit == 0           # verification is never retried into a pass


def test_invalid_graphs_are_rejected():
    a = Task(id="a", objective="a", kind="backend", capability="api_implementation", depends_on=["b"], agent="x")
    b = Task(id="b", objective="b", kind="backend", capability="api_implementation", depends_on=["a"], agent="x")
    assert any("circular" in e for e in registry.validate_graph([a, b]))
    c = Task(id="c", objective="c", kind="backend", capability="api_implementation", depends_on=["zzz"], agent="x")
    assert any("unknown task" in e for e in registry.validate_graph([c]))
    d = Task(id="d", objective="d", kind="deploy", capability="kubernetes")
    d.agent = registry.assign(d)
    assert d.agent is None and any("unsupported" in e for e in registry.validate_graph([d]))


def test_agents_are_chosen_by_capability_not_by_name():
    from backend.swarm.registry import AgentSpec
    misleading = [AgentSpec(id="backend_agent", title="named backend, writes JS", capabilities=["api_client"], task_kinds=["frontend_client"]),
                  AgentSpec(id="js_helper", title="writes FastAPI", capabilities=["api_implementation"], task_kinds=["backend"])]
    t = Task(id="t", objective="x", kind="backend", capability="api_implementation")
    assert registry.assign(t, misleading) == "js_helper"


def test_a_mission_without_a_contract_or_approval_does_not_run(tmp_path, project):
    eng = engine(tmp_path)
    m = eng.create("p1", "u1", "something", Contract(endpoints=[]))
    assert m.status == "rejected" and any("contract" in e for e in m.plan_errors)
    ok = eng.create("p1", "u1", "orders", CONTRACT)
    with pytest.raises(SwarmError, match="approve"):
        eng.run("p1", project, "u1", ok.id, approved=False)


# 2 interfaces are read from code ---------------------------------------------------------------------------------
def test_routes_and_client_calls_are_extracted_and_matched():
    routes = interfaces.routes({"backend/main.py": BACKEND})
    assert {(r["method"], r["path"]) for r in routes} >= {("POST", "/api/orders"), ("GET", "/api/orders/{order_id}")}
    post = next(r for r in routes if r["method"] == "POST")
    assert post["body_fields"] == ["item", "quantity"] and post["required_fields"] == ["item"]
    wrong = interfaces.match(interfaces.client_calls({"frontend/src/api/client.js": CLIENT_WRONG}), routes)
    assert [c["status"] for c in wrong] == ["mismatch", "ok"] and "no backend route has this path" in wrong[0]["reason"]
    fixed = interfaces.match(interfaces.client_calls({"frontend/src/api/client.js": CLIENT_FIXED}), routes)
    assert [c["status"] for c in fixed] == ["ok", "ok"]
    drift = interfaces.match([{"file": "c.js", "line": 1, "path": "/api/orders", "method": "POST", "body_fields": ["qty"],
                               "resolved": True}], routes)
    assert "does not accept: ['qty']" in drift[0]["reason"] and "omits required fields: ['item']" in drift[0]["reason"]
    dyn = interfaces.client_calls({"x.js": "fetch(buildUrl(kind))"})
    assert dyn[0]["resolved"] is False and interfaces.match(dyn, routes)[0]["status"] == "unresolved"


def test_artifacts_are_validated_before_they_are_accepted():
    v = SwarmEngine._validate
    assert v("contract", {"endpoints": [{"method": "FETCH", "path": "x"}]}) and v("contract", {"endpoints": []})
    dup = {"endpoints": [{"method": "GET", "path": "/a/{x}"}, {"method": "GET", "path": "/a/{y}"}]}
    assert any("duplicate" in e for e in v("contract", dup))
    assert any("outside" in e for e in v("source_files", {"files": {"backend/x.py": "1"}, "owned_paths": ["frontend/"]}))
    assert v("source_files", {"files": {"frontend/a.js": "1"}, "owned_paths": ["frontend/"]}) == []


# 3 consensus -----------------------------------------------------------------------------------------------------
def _p(pid, violates=(), **scores):
    full = {"contract_conformance": 0.5, "correctness_evidence": 0.5, "security": 0.5, "change_cost": 0.5, "maintainability": 0.5}
    full.update(scores)
    return Proposal(id=pid, author="a", title=pid, action="repair:frontend", scores=full, violates=list(violates))


def test_consensus_ignores_votes_enforces_mandatory_constraints_and_escalates_ties():
    sel = consensus.decide([_p("a", contract_conformance=1.0), _p("b", contract_conformance=0.0)])
    assert sel["outcome"] == "selected" and sel["selected"] == "a" and "votes are not counted" in sel["method"]
    vetoed = consensus.decide([_p("fast", contract_conformance=1, correctness_evidence=1, security=1, change_cost=1,
                                  maintainability=1, violates=["breaks the contract"]), _p("slow")])
    assert vetoed["selected"] == "slow"
    tie = consensus.decide([_p("a"), _p("b", maintainability=0.6)])
    assert tie["outcome"] == "escalate" and "tied" in tie["reason"]
    unknown = Proposal(id="u", author="a", title="u", action="x", scores={"security": 1.0})
    assert consensus.decide([unknown])["outcome"] == "escalate"
    assert consensus.decide([_p("x", violates=["v"])])["outcome"] == "escalate"


def test_the_critical_reviewer_cites_its_evidence():
    contract = [e.model_dump() for e in CONTRACT.endpoints]
    routes = interfaces.routes({"backend/main.py": BACKEND})
    calls = interfaces.client_calls({"c.js": CLIENT_WRONG})
    f = consensus.review(contract, routes, calls, {"backend/main.py": BACKEND}, ["SQL built from strings (backend/main.py:9)"],
                         {"contract": "art_c", "route_inventory": "art_r", "client_calls": "art_k", "source_files": "art_s"})
    unsupported = next(x for x in f if x["kind"] == "unsupported_assumption" and "POST /api/order" in x["detail"])
    assert unsupported["severity"] == "high" and unsupported["based_on"] == ["art_k", "art_c"]
    assert any(x["kind"] == "missing_evidence" for x in f)                    # no backend tests were given
    assert any(x["kind"] == "security" and x["severity"] == "high" for x in f)


# 4 missions ------------------------------------------------------------------------------------------------------
def test_mission_detects_the_mismatch_repairs_the_deviating_side_and_verifies(tmp_path, project):
    gen = scripted_agents()
    eng = engine(tmp_path, gen)
    before = (project / "backend" / "main.py").read_text(encoding="utf-8")
    m = run_mission(eng, project)
    assert m.status == "completed", (m.error, [(t.id, t.status, t.error) for t in m.tasks])
    assert gen.calls == {"backend": 1, "frontend": 2}                          # only the deviating side was asked again
    c = m.conflicts[0]
    assert c.kind == "api_contract" and "POST /api/order" in c.detail and c.status == "resolved"
    assert c.decision["outcome"] == "selected" and c.decision["selected"] == "p_client"
    assert any(p.violates for p in c.proposals if p.id == "p_backend")         # the backend follows the contract
    gates = {g.name: g for g in m.gates}
    assert all(g.status == "passed" for g in m.gates if g.mandatory)
    assert gates["project and contract tests"].evidence["counts"]["passed"] == 4      # 1 + 1 backend + 2 contract
    assert gates["performance"].status == "not_applicable"
    fe = [a for a in m.artifacts if a.task_id == "t3" and a.kind == "source_files"]
    assert len(fe) == 2 and fe[1].supersedes == fe[0].id and fe[0].content_hash != fe[1].content_hash   # nothing overwritten
    assert all(a.creator and a.task_id and a.revision == m.base_revision and a.content_hash for a in m.artifacts)
    types = [x.type for x in m.messages]
    assert {"submit_artifact", "report_finding", "raise_conflict", "propose_resolution"} <= set(types)
    assert (project / "backend" / "main.py").read_text(encoding="utf-8") == before        # the project is untouched
    assert m.report["status"] == "completed" and not m.report["unresolved_conflicts"]


def test_independent_tasks_run_concurrently(tmp_path, project):
    base = scripted_agents()

    def slow(system, prompt):
        time.sleep(1.0)
        return base(system, prompt)
    for conc, overlap in ((2, True), (1, False)):
        eng = engine(tmp_path / f"s{conc}", slow)
        m = eng.create("p1", "u1", "orders", CONTRACT, settings={"concurrency": conc})
        eng.run("p1", project, "u1", m.id, approved=True)
        m = eng.store.get("p1", "missions", m.id)
        t2, t3 = (next(t for t in m.tasks if t.id == i) for i in ("t2", "t3"))
        # first attempts of t2 and t3 (t3 is repaired later; its first start is in the messages)
        starts = {x.task_id: x.at for x in m.messages if x.type == "submit_artifact" and x.task_id in ("t2", "t3")}
        assert t2.status == "completed"
        concurrent = t2.started_at < starts["t3"] and t2.finished_at > min(x.at for x in m.messages if x.task_id == "t3")
        assert concurrent is overlap, (conc, t2.started_at, t2.finished_at, starts)


def test_both_sides_departing_from_the_contract_goes_to_a_person(tmp_path, project):
    backend = BACKEND.replace("    quantity: int = 1", "    amount: int")                  # backend drifts too
    gen = scripted_agents(frontend_fixes_on_feedback=False, backend=backend)
    eng = engine(tmp_path, gen)
    contract = Contract(endpoints=[Endpoint(method="POST", path="/api/order", request_fields=["item", "quantity"])])
    m = run_mission(eng, project, contract)
    assert m.status == "awaiting_decision", m.error
    c = m.conflicts[-1]
    assert c.status == "escalated" and c.decision["outcome"] == "escalate" and not any(p.violates for p in c.proposals)
    assert next(t for t in m.tasks if t.id == "t5").status == "awaiting_review"
    with pytest.raises(SwarmError):
        eng.decide("p1", project, "u1", m.id, c.id, "p_unknown")
    calls_before = dict(gen.calls)
    eng.decide("p1", project, "u1", m.id, c.id, "p_backend")
    m = eng.store.get("p1", "missions", m.id)
    assert gen.calls["backend"] == calls_before["backend"] + 1                  # the chosen side was asked to change
    assert next(x for x in m.conflicts if x.id == c.id).decision["by"] == "user u1"
    assert m.status in ("failed", "awaiting_decision") and m.status != "completed"   # the drift is not fixed: not completed


def test_a_failing_mandatory_test_fails_the_mission_whatever_the_agents_report(tmp_path, project):
    broken_tests = BACKEND_TESTS.replace('created["quantity"] == 2', 'created["quantity"] == 3')
    gen = scripted_agents()

    def answers(system, prompt):
        out = gen(system, prompt)
        return out.replace(BACKEND_TESTS, broken_tests) if "Agent: backend_agent" in prompt else out
    m = run_mission(engine(tmp_path, answers), project)
    gates = {g.name: g for g in m.gates}
    assert m.status == "failed" and gates["project and contract tests"].status == "failed"
    assert gates["project and contract tests"].evidence["rerun"]["status"] == "failed"   # reproduced, not flaky
    assert all(t.status == "completed" for t in m.tasks if t.id in ("t1", "t2", "t3", "t4", "t5"))
    assert next(t for t in m.tasks if t.id == "t6").status == "failed" and "mandatory gate" in m.report["failed_tasks"][0]


def test_invalid_agent_output_fails_the_task_and_blocks_dependents(tmp_path, project):
    def outside(system, prompt):
        if "Agent: frontend_agent" in prompt:
            return "### backend/evil.py\n```python\nimport os\n```\n"
        return scripted_agents()(system, prompt)
    m = run_mission(engine(tmp_path, outside), project)
    t3 = next(t for t in m.tasks if t.id == "t3")
    assert t3.status == "failed" and t3.attempts == 2                           # one bounded retry
    assert {t.id: t.status for t in m.tasks if t.id in ("t4", "t5", "t6")} == {"t4": "blocked", "t5": "blocked", "t6": "blocked"}
    assert m.status == "failed"


def test_message_limit_stops_a_mission(tmp_path, project):
    m = run_mission(engine(tmp_path), project, settings={"max_messages": 3})
    assert m.status in ("failed", "cancelled") and "message limit" in (m.error or "")


def test_cancellation(tmp_path, project):
    eng = engine(tmp_path)
    m = eng.create("p1", "u1", "orders", CONTRACT)
    m = eng.cancel("p1", m.id)
    assert m.status == "cancelled" and all(t.status == "cancelled" for t in m.tasks)
    base = scripted_agents()

    def slow(system, prompt):
        time.sleep(2)
        return base(system, prompt)
    eng2 = engine(tmp_path / "bg", slow, background=True)
    m2 = eng2.create("p1", "u1", "orders", CONTRACT)
    eng2.run("p1", project, "u1", m2.id, approved=True)
    time.sleep(0.5)
    eng2.cancel("p1", m2.id)
    for _ in range(60):
        if eng2.store.get("p1", "missions", m2.id).status != "running":
            break
        time.sleep(0.5)
    final = eng2.store.get("p1", "missions", m2.id)
    assert final.status == "cancelled" and not any(t.status in ("running", "pending") for t in final.tasks)


def test_interrupted_missions_resume_without_redoing_completed_work(tmp_path, project):
    gen = scripted_agents()
    eng = engine(tmp_path, gen)
    m = eng.create("p1", "u1", "orders", CONTRACT)

    def crash(x):                                          # the server died while t2/t3 ran (t1 had completed)
        x.status = "running"
        for t in x.tasks:
            t.status = {"t1": "completed", "t2": "running", "t3": "running"}.get(t.id, "pending")
    eng.store.update("p1", "missions", m.id, crash)
    assert SwarmStore(tmp_path / "swarm").close_interrupted() == 1
    m = eng.store.get("p1", "missions", m.id)
    assert m.status == "interrupted" and {t.id: t.status for t in m.tasks}["t2"] == "pending"
    eng.run("p1", project, "u1", m.id, approved=True)
    m = eng.store.get("p1", "missions", m.id)
    assert m.status == "completed" and not any(a.task_id == "t1" for a in m.artifacts)    # t1 was not redone


def test_delivery_is_an_autopilot_plan_awaiting_approval(tmp_path, project, monkeypatch):
    import backend.evolution.autopilot.service as aps
    from backend.evolution.autopilot.service import AutopilotService
    from backend.evolution.autopilot.store import AutopilotStore
    ap = AutopilotService(AutopilotStore(tmp_path / "ap"), background=False)
    monkeypatch.setattr(aps, "global_autopilot_service", ap)
    eng = engine(tmp_path, autopilot=ap)
    m = eng.create("p1", "u1", "orders", CONTRACT)
    with pytest.raises(SwarmError):
        eng.deliver("p1", "u1", m.id)
    eng.run("p1", project, "u1", m.id, approved=True)
    m = eng.deliver("p1", "u1", m.id)
    plan = ap.store.get("p1", "plans", m.delivery["autopilot_plan_id"])
    assert plan.status.value == "awaiting_approval" and plan.origin == "swarm"
    assert set(plan.tasks[0].contents) == {"backend/main.py", "backend/tests/test_orders.py", "frontend/src/api/client.js"}
    assert "LEFT" not in (project / "backend" / "main.py").read_text(encoding="utf-8") and not (project / "frontend" / "src").exists()


# 5 API ------------------------------------------------------------------------------------------------------------
@pytest.fixture
def api(tmp_path, project, monkeypatch):
    import backend.routes.export as export
    import backend.swarm.routes as routes
    from backend.auth.dependencies import get_current_user
    from backend.generation.store import global_generation_store
    monkeypatch.setattr(routes, "global_swarm_engine", engine(tmp_path))
    records = {"gen_mine": {"generation_id": "gen_mine", "user_id": "alice", "status": "completed", "project_path": str(project)},
               "gen_theirs": {"generation_id": "gen_theirs", "user_id": "bob", "status": "completed", "project_path": str(project)}}
    monkeypatch.setattr(global_generation_store, "get", lambda gid, default=None: records.get(gid, default))
    monkeypatch.setattr(export, "_safe_project_dir", lambda p: project if p == str(project) else None)
    app = FastAPI()
    app.include_router(routes.swarm_router)
    app.dependency_overrides[get_current_user] = lambda: {"id": "alice"}
    return TestClient(app)


def test_api_flow_and_access(api):
    base = "/api/projects/gen_mine/swarm/missions"
    body = {"objective": "orders API and client", "contract": CONTRACT.model_dump()}
    assert api.post("/api/projects/gen_theirs/swarm/missions", json=body).status_code == 403
    assert api.post(base, json={**body, "settings": {"concurrency": 50}}).status_code == 422
    assert api.post(base, json={**body, "settings": {"rm -rf": 1}}).status_code == 422
    m = api.post(base, json=body).json()["mission"]
    assert m["status"] == "planned" and api.get("/api/swarm/agents").json()["agents"]
    assert api.post(f"{base}/{m['id']}/run", json={}).status_code == 409                  # not approved
    assert api.post(f"{base}/{m['id']}/run", json={"approved": True}).status_code == 202
    done = api.get(f"{base}/{m['id']}").json()["mission"]
    assert done["status"] == "completed" and done["report"]["status"] == "completed"
    assert api.post(f"{base}/{m['id']}/decide", json={"conflict_id": "cf_x", "proposal_id": "p"}).status_code == 409
    assert api.get(f"{base}/swm_missing").status_code == 404


def test_the_page_uses_the_real_api():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2] / "frontend" / "src"
    service = (root / "services" / "swarm.js").read_text(encoding="utf-8")
    page = (root / "pages" / "SwarmPage.jsx").read_text(encoding="utf-8")
    for path in ("/api/swarm/agents", "/run", "/cancel", "/decide", "/deliver"):
        assert path in service
    assert "approved: true" in service and "consent" in page
    for fake in ("Math.random", "mockData", "consensus_score", "COMPLETED"):
        assert fake not in page
    assert not (root / "pages" / "MultiAgentPage.jsx").exists()


# 6 genuine: Docker ------------------------------------------------------------------------------------------------
def _docker_ok():
    try:
        from backend.execution.docker_test_sandbox import docker_available
        return docker_available()
    except Exception:
        return False


@pytest.mark.skipif(not _docker_ok(), reason="Docker is not available: the genuine mission was NOT run")
def test_genuine_mission_in_docker(tmp_path, project, monkeypatch):
    """Two agents in parallel -> artifacts -> the Integration Agent finds the client's wrong path and field ->
    the frontend agent repairs it -> integrated in an isolated workspace -> project tests and the generated contract
    test run in the Docker sandbox -> the report reflects exactly that."""
    monkeypatch.setenv("AIFORGE_TEST_SANDBOX", "docker")
    m = run_mission(engine(tmp_path), project)
    tests = next(g for g in m.gates if g.name == "project and contract tests")
    assert m.status == "completed", (m.error, [(g.name, g.status, g.detail) for g in m.gates])
    assert tests.evidence["environment"].startswith("Docker") and tests.evidence["counts"]["passed"] == 4
    assert m.conflicts[0].status == "resolved" and m.report["status"] == "completed"
