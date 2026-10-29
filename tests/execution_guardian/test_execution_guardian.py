"""
Execution Guardian tests. Fast tests run real checks on small projects under the explicit local sandbox opt-in
(tests/conftest.py), with container checks disabled (they are then BLOCKED, never passed) and the coding model
replaced by fixed answers. Genuine tests at the end run the backend startup and the frontend build in Docker.
"""

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from backend.execution_guardian import checks as chk
from backend.execution_guardian import classify as cls
from backend.execution_guardian import repair as rep
from backend.execution_guardian.models import Check
from backend.execution_guardian.service import ExecutionGuardian, GuardianError, VerificationStore
from tests.execution_guardian.sample import (API, API_BROKEN_STARTUP, APP_JS, APP_JS_BROKEN, BUILD_JS, CALC, CALC_RUNTIME,
                                             CALC_SYNTAX, CALC_TESTS, CALC_UNDEFINED, CALC_UNDEFINED_TESTS, CALC_WRONG,
                                             PACKAGE_JSON, file_answer, fixed_agent, python_project, write)


@pytest.fixture(autouse=True)
def _no_containers(monkeypatch):
    monkeypatch.setenv("AIFORGE_GUARDIAN_CONTAINERS", "off")


def autopilot(tmp_path):
    from backend.evolution.autopilot.service import AutopilotService
    from backend.evolution.autopilot.store import AutopilotStore
    return AutopilotService(AutopilotStore(tmp_path / "ap"), background=False)


def guardian(tmp_path, gen=None, llm=None):
    ap = autopilot(tmp_path)
    return ExecutionGuardian(VerificationStore(tmp_path / "eg"), background=False, generate=gen, classify_llm=llm, autopilot=ap), ap


def digest(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob("*") if p.is_file()}


def statuses(v):
    return {c.name: c.status for c in v.checks}


# 1 successful verification -------------------------------------------------------------------------------------------------
def test_a_working_project_is_verified(tmp_path):
    proj = python_project(tmp_path / "p")
    g, ap = guardian(tmp_path)
    v = g.start("p1", proj, "u1")
    assert v.status == "VERIFIED", statuses(v)
    assert all(c.status == "PASSED" for c in v.checks if c.required)
    assert statuses(v)["python_tests"] == "PASSED" and v.checks[[c.name for c in v.checks].index("python_tests")].counts == {"passed": 2}
    assert v.report["verified"] and not v.repairs and not v.delivery and not v.failures


# 2 intentional syntax error ----------------------------------------------------------------------------------------------------
def test_a_syntax_error_is_found_classified_and_routed(tmp_path):
    proj = python_project(tmp_path / "p", calc=CALC_SYNTAX)
    g, _ = guardian(tmp_path)
    v = g.start("p1", proj, "u1", settings={"max_repair_attempts": 0})
    assert v.status == "FAILED" and statuses(v)["python_syntax"] == "FAILED"
    syn = next(f for f in v.failures if f.check == "python_syntax")
    assert syn.category == "syntax_error" and syn.severity == "critical" and syn.responsible_agent == "backend"
    assert "calc.py" in syn.files and syn.classified_by == "rule:python_syntax" and syn.log_excerpt


# 3 frontend build failure (classification; the genuine build runs at the end) --------------------------------------------------
def test_a_frontend_build_failure_is_classified_and_routed_to_the_frontend_agent():
    c = Check(name="frontend_build", label="Frontend build", status="FAILED", error_summary="npm run build failed",
              log_excerpt="file:///work/build.js:3\nSyntaxError: Unexpected token ';' in src/App.js:2\nnpm ERR! code 1")
    f = cls.classify_check(c, ["src/App.js", "build.js", "package.json"])[0]
    assert (f.category, f.responsible_agent, f.severity) == ("frontend_build_error", "frontend", "critical")
    assert "src/App.js" in f.files


def test_without_containers_frontend_and_startup_checks_are_blocked_not_passed(tmp_path):
    proj = write(tmp_path / "p", {"backend/main.py": API, "tests/test_api.py": "def test_ok():\n    assert True\n",
                                  "frontend/package.json": PACKAGE_JSON, "frontend/build.js": BUILD_JS, "frontend/src/App.js": APP_JS})
    g, _ = guardian(tmp_path)
    v = g.start("p1", proj, "u1")
    s = statuses(v)
    assert s["backend_startup"] == s["frontend_build"] == s["frontend_dependencies"] == "BLOCKED"
    assert v.status == "BLOCKED" and not v.report["verified"]
    assert any("AIFORGE_GUARDIAN_CONTAINERS=off" in c.reason for c in v.checks if c.name == "backend_startup")
    assert all(f.category == "infrastructure_error" and not f.repairable for f in v.failures) and not v.repairs


# 4 failed unit tests ---------------------------------------------------------------------------------------------------------------
def test_failing_unit_tests_name_the_tests(tmp_path):
    proj = python_project(tmp_path / "p", calc=CALC_WRONG)
    g, _ = guardian(tmp_path)
    v = g.start("p1", proj, "u1", settings={"max_repair_attempts": 0})
    t = next(c for c in v.checks if c.name == "python_tests")
    assert t.status == "FAILED" and t.counts.get("failed") == 1 and t.counts.get("passed") == 1
    f = next(x for x in v.failures if x.check == "python_tests")
    assert f.category == "unit_test_failure" and f.failing_tests == ["tests/test_calc.py::test_discount"]
    assert f.responsible_agent == "backend" and "calc.py" in f.files


# 5 missing dependencies -------------------------------------------------------------------------------------------------------------
def test_missing_dependencies_go_to_the_controlled_dependency_resolver(tmp_path):
    c = Check(name="python_tests", label="Python unit tests", status="FAILED",
              log_excerpt="ImportError while importing test module 'tests/test_x.py'.\nE   ModuleNotFoundError: No module named 'jose'")
    f = cls.classify_check(c, ["app.py", "tests/test_x.py", "requirements.txt"])[0]
    assert f.category == "dependency_install_error" and f.responsible_agent == "dependency_resolver"
    ws = write(tmp_path / "ws", {"app.py": "from jose import jwt\n", "requirements.txt": "fastapi\n"})
    strategy, changes, _ = rep.propose([f], "dependency_resolver", ws, {"frontend": None}, "p1", None)
    assert strategy == "add_missing_requirements" and changes["requirements.txt"] == "fastapi\npython-jose[cryptography]\n"
    # a module without a known package is never guessed: the resolver proposes nothing
    unknown = f.model_copy(update={"log_excerpt": "ModuleNotFoundError: No module named 'yaml'"})
    strategy, changes, note = rep.propose([unknown], "dependency_resolver", ws, {"frontend": None}, "p1", None)
    assert not changes and "no controlled dependency fix" in note
    pip = Check(name="python_dependencies", label="deps", status="FAILED",
                log_excerpt="ERROR: Could not find a version that satisfies the requirement fastapi==99.0.0\n"
                            "ERROR: No matching distribution found for fastapi==99.0.0")
    f2 = cls.classify_check(pip, ["requirements.txt"])[0]
    ws2 = write(tmp_path / "ws2", {"requirements.txt": "fastapi==99.0.0\nhttpx\n"})
    strategy, changes, _ = rep.propose([f2], "dependency_resolver", ws2, {"frontend": None}, "p1", None)
    assert strategy == "unpin_unavailable_version" and changes["requirements.txt"] == "fastapi\nhttpx\n"
    ok, why = rep.in_scope("dependency_resolver", "app.py", {"frontend": None}, [])
    assert not ok and "requirements.txt" in why


# 6 execution timeouts ------------------------------------------------------------------------------------------------------------------
def test_a_timed_out_test_run_is_a_failure_not_a_pass(tmp_path, monkeypatch):
    import backend.execution.docker_test_sandbox as dts
    from backend.execution.models import ExecutionResult, ExecutionStatus
    monkeypatch.setenv("AIFORGE_TEST_SANDBOX", "docker")
    monkeypatch.setattr(dts, "docker_available", lambda: True)
    monkeypatch.setattr(dts, "run_pytest_in_docker", lambda project, timeout_seconds=900: ExecutionResult(
        status=ExecutionStatus.TIMEOUT, exit_code=-1, timed_out=True, stderr=f"Tests did not finish within {timeout_seconds:.0f}s"))
    proj = python_project(tmp_path / "p")
    g, _ = guardian(tmp_path)
    v = g.start("p1", proj, "u1", settings={"max_repair_attempts": 0, "check_timeout_seconds": 60})
    t = next(c for c in v.checks if c.name == "python_tests")
    assert t.status == "FAILED" and t.timed_out and "60s" in t.error_summary
    assert statuses(v)["python_dependencies"] == "PASSED" and v.status == "FAILED"
    assert any(f.classified_by == "rule:test_timeout" for f in v.failures)


# 7 sandbox failures --------------------------------------------------------------------------------------------------------------------
def test_without_an_isolated_environment_the_result_is_blocked(tmp_path, monkeypatch):
    import backend.execution.docker_test_sandbox as dts
    monkeypatch.setenv("AIFORGE_TEST_SANDBOX", "docker")
    monkeypatch.setattr(dts, "docker_available", lambda: False)
    proj = python_project(tmp_path / "p")
    g, _ = guardian(tmp_path)
    v = g.start("p1", proj, "u1")
    s = statuses(v)
    assert s["python_dependencies"] == s["python_tests"] == "BLOCKED" and s["python_syntax"] == "PASSED"
    assert v.status == "BLOCKED" and not v.report["verified"] and not v.repairs
    assert all(f.category == "infrastructure_error" for f in v.failures)
    assert "could not run" in v.report["statement"]


# 8 classification ------------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("check,text,category,agent", [
    ("backend_startup", "sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server", "database_connection_error", "database"),
    ("backend_startup", "KeyError: 'DATABASE_URL'", "configuration_error", "debug"),
    ("backend_startup", "ModuleNotFoundError: No module named 'jose'", "dependency_install_error", "dependency_resolver"),
    ("backend_startup", 'File "/tmp/app/backend/main.py", line 4, in <module>\nRuntimeError: startup failed', "backend_startup_error", "backend"),
    ("quality_gate", "calc.py:7:12: F821 undefined name 'json'", "compilation_error", "backend"),
    ("python_tests", "FAILED tests/test_integration_api.py::test_flow - assert 500 == 200\nE   assert 500 == 200", "integration_test_failure", "backend"),
    ("python_tests", "FAILED tests/test_calc.py::test_add - NameError: name 'x' is not defined\nE   NameError: name 'x' is not defined", "runtime_exception", "backend"),
])
def test_deterministic_classification(check, text, category, agent):
    f = cls.classify_check(Check(name=check, label=check, status="FAILED", log_excerpt=text, error_summary="failed"),
                           ["backend/main.py", "calc.py", "tests/test_calc.py", "tests/test_integration_api.py"])[0]
    assert (f.category, f.responsible_agent) == (category, agent) and f.classified_by.startswith("rule:")


def test_ambiguous_failures_use_the_model_only_with_a_known_label():
    c = Check(name="custom", label="custom check", status="FAILED", log_excerpt="something odd happened", error_summary="odd")
    f = cls.classify_check(c, [], llm=lambda s, p: "this is a configuration_error")[0]
    assert f.category == "configuration_error" and f.classified_by.startswith("model")
    junk = cls.classify_check(c, [], llm=lambda s, p: "a quantum flux problem")[0]
    assert junk.category == "runtime_exception" and junk.classified_by.startswith("fallback")
    none = cls.classify_check(c, [])[0]
    assert none.classified_by.startswith("fallback") and none.log_excerpt == "something odd happened"   # nothing invented


# 9 agent routing ------------------------------------------------------------------------------------------------------------------------------
def test_routing_follows_the_failure_and_uses_the_agents_own_prompt(tmp_path):
    assert cls.route("unit_test_failure", ["tests/test_ui.test.js", "frontend/src/App.jsx"]) == "frontend"
    assert cls.route("syntax_error", ["backend/models.py"]) == "database"
    assert cls.route("runtime_exception", ["backend/routes.py"]) == "backend"
    assert cls.route("api_contract_mismatch", []) == "debug" and cls.route("infrastructure_error", []) is None
    from backend.agents.factory import AgentFactory
    gen = fixed_agent(file_answer("calc.py", CALC))
    proj = python_project(tmp_path / "p", calc=CALC_WRONG)
    g, _ = guardian(tmp_path, gen)
    v = g.start("p1", proj, "u1")
    assert v.repairs[0].agent == "backend" and v.repairs[0].strategy == "model:backend"
    assert gen.calls[0]["system"] == AgentFactory.create_agent("backend").system_prompt          # the Backend Agent repaired it
    assert "test_discount" in gen.calls[0]["prompt"] and "tests are the specification" in gen.calls[0]["prompt"]


# 10 successful automatic repair ---------------------------------------------------------------------------------------------------------------
def test_a_successful_repair_is_verified_and_delivered_for_approval(tmp_path):
    proj = python_project(tmp_path / "p", calc=CALC_WRONG)
    before = digest(proj)
    g, ap = guardian(tmp_path, fixed_agent(file_answer("calc.py", CALC)))
    v = g.start("p1", proj, "u1")
    assert v.status == "VERIFIED" and len(v.repairs) == 1
    r = v.repairs[0]
    assert r.outcome == "resolved" and r.files_changed == ["calc.py"] and not r.rolled_back
    assert r.before["python_tests"] == "FAILED" and r.after["python_tests"] == "PASSED"
    assert v.original_failures and not v.failures and v.report["failures_resolved"]
    plan = ap.store.get("p1", "plans", v.delivery["autopilot_plan_id"])
    assert plan.status.value == "awaiting_approval" and plan.tasks[0].contents["calc.py"] == CALC and plan.origin == "execution_guardian"
    assert digest(proj) == before                                                    # the project itself is unchanged
    deterministic = guardian(tmp_path / "d")[0].start("p1", python_project(tmp_path / "pd", calc=CALC_UNDEFINED, tests=CALC_UNDEFINED_TESTS), "u1")
    assert deterministic.status == "VERIFIED" and deterministic.repairs[0].strategy == "add_missing_imports"   # no model needed


# 11 failed automatic repair ------------------------------------------------------------------------------------------------------------------
def test_a_failed_repair_is_reported_honestly(tmp_path):
    still_wrong = CALC_WRONG.replace("round(price", "round(1.0 * price")
    proj = python_project(tmp_path / "p", calc=CALC_WRONG)
    g, ap = guardian(tmp_path, fixed_agent(file_answer("calc.py", still_wrong)))
    v = g.start("p1", proj, "u1", settings={"max_repair_attempts": 1})
    assert v.status == "FAILED" and v.repairs[0].outcome == "no_change" and not v.delivery
    assert v.report["remaining_failures"] and not v.report["verified"]
    assert v.report["remaining_failures"][0]["category"] == "unit_test_failure"


# 12 maximum repair attempts ---------------------------------------------------------------------------------------------------------------------
def test_repairs_stop_at_the_configured_limit(tmp_path):
    variants = [file_answer("calc.py", CALC_WRONG.replace("pct / 100", f"pct / {100 + i}")) for i in range(1, 6)]
    proj = python_project(tmp_path / "p", calc=CALC_WRONG)
    gen = fixed_agent(variants)
    g, _ = guardian(tmp_path, gen)
    v = g.start("p1", proj, "u1", settings={"max_repair_attempts": 2})
    assert len(v.repairs) <= 2 and len(gen.calls) <= 2 and v.status == "FAILED"
    with pytest.raises(GuardianError):
        g.start("p1", proj, "u1", settings={"max_repair_attempts": 50})


# 13 repeated failure detection ------------------------------------------------------------------------------------------------------------------
def test_a_failure_that_survives_its_repair_is_not_attempted_again(tmp_path):
    useless = CALC_WRONG + "\n# tried something\n"
    proj = python_project(tmp_path / "p", calc=CALC_WRONG)
    gen = fixed_agent(file_answer("calc.py", useless))
    g, _ = guardian(tmp_path, gen)
    v = g.start("p1", proj, "u1", settings={"max_repair_attempts": 3})
    assert len(v.repairs) == 1 and len(gen.calls) == 1                                # stopped early, not 3 attempts
    assert v.repairs[0].outcome == "no_change" and v.status == "FAILED"
    assert any("no repairable failure left" in a["text"] for a in v.activity)


# 14 API ------------------------------------------------------------------------------------------------------------------------------------------
@pytest.fixture
def api(tmp_path, monkeypatch):
    import backend.execution_guardian.routes as routes
    import backend.routes.export as export
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from backend.auth.dependencies import get_current_user
    from backend.generation.store import global_generation_store
    proj = python_project(tmp_path / "proj", calc=CALC_WRONG)
    g, ap = guardian(tmp_path, fixed_agent(file_answer("calc.py", CALC)))
    monkeypatch.setattr(routes, "global_execution_guardian", g)
    records = {"mine": {"generation_id": "mine", "user_id": "alice", "status": "completed", "project_path": str(proj)},
               "theirs": {"generation_id": "theirs", "user_id": "bob", "status": "completed", "project_path": str(proj)}}
    monkeypatch.setattr(global_generation_store, "get", lambda gid, default=None: records.get(gid, default))
    monkeypatch.setattr(export, "_safe_project_dir", lambda p: proj if p == str(proj) else None)
    app = FastAPI()
    app.include_router(routes.execution_guardian_router)
    app.dependency_overrides[get_current_user] = lambda: {"id": "alice"}
    return TestClient(app), proj


def test_verification_api(api):
    client, proj = api
    base = "/api/projects/mine/verifications"
    assert client.post("/api/projects/theirs/verifications", json={}).status_code == 403
    assert client.post(base, json={"settings": {"max_repair_attempts": 99}}).status_code == 422
    assert client.post(base, json={"settings": {"rm -rf": 1}}).status_code == 422
    r = client.post(base, json={"settings": {"max_repair_attempts": 2}})
    assert r.status_code == 202
    vid = r.json()["verification_id"]
    assert client.get(f"{base}/{vid}").json()["verification"]["status"] == "VERIFIED"
    checks = client.get(f"{base}/{vid}/checks").json()
    assert {c["name"] for c in checks["checks"]} >= {"python_syntax", "python_tests"} and checks["original_checks"]
    repairs = client.get(f"{base}/{vid}/repairs").json()
    assert repairs["repairs"][0]["outcome"] == "resolved" and repairs["original_failures"] and repairs["max_repair_attempts"] == 2
    report = client.get(f"{base}/{vid}/report").json()
    assert report["verification_id"] == vid and report["verified"] is True
    md = client.get(f"{base}/{vid}/report?format=markdown").text
    assert "## What was not tested" in md and "## How to run it" in md and "pytest" in md
    assert client.get(base).json()["verifications"][0]["id"] == vid
    assert client.post(f"{base}/{vid}/cancel").status_code == 200
    assert client.get(f"{base}/ver_missing").status_code == 404 and client.get(f"{base}/{vid}/report?format=xml").status_code == 422


# 15 invalid project paths --------------------------------------------------------------------------------------------------------------------------
def test_invalid_paths_are_rejected(api, tmp_path):
    client, _ = api
    assert client.post("/api/projects/unknown/verifications", json={}).status_code in (403, 404)
    assert client.post("/api/projects/..%2F..%2Fetc/verifications", json={}).status_code in (403, 404)
    g, _ = guardian(tmp_path)
    with pytest.raises(GuardianError):
        g.start("p1", tmp_path / "does-not-exist", "u1")
    ws = python_project(tmp_path / "ws")
    accepted, rejected = rep.validate({"../escape.py": "x", "C:/Windows/evil.py": "x", "/etc/passwd": "x", "calc.py": CALC},
                                      "backend", {"frontend": None}, ws, ["calc.py"])
    assert set(accepted) == {"calc.py"} and {r["path"] for r in rejected} == {"../escape.py", "C:/Windows/evil.py", "/etc/passwd"}
    assert all(r["reason"] == "outside the workspace" for r in rejected)


# 16 workspace isolation ----------------------------------------------------------------------------------------------------------------------------
def test_repairs_stay_in_the_copy_and_never_touch_tests_or_secrets(tmp_path):
    proj = python_project(tmp_path / "p", calc=CALC_WRONG, extra={".env": "API_KEY=sk-test-1234567890abcdef\n"})
    before = digest(proj)
    weakened = CALC_TESTS.replace("== 180.0", "== 220.0")
    answer = file_answer("tests/test_calc.py", weakened) + file_answer(".env", "API_KEY=changed\n")
    g, _ = guardian(tmp_path, fixed_agent(answer))
    v = g.start("p1", proj, "u1", settings={"max_repair_attempts": 1})
    r = v.repairs[0]
    assert v.status == "FAILED" and r.outcome in ("rejected", "no_fix") and not r.files_changed
    reasons = {x["path"]: x["reason"] for x in r.rejected_paths}
    assert all("read-only" in why or "secret" in why or "outside" in why for why in reasons.values())
    assert digest(proj) == before and not (proj / ".venv").exists() and not list(proj.rglob("__pycache__"))
    assert rep.in_scope("frontend", "backend/main.py", {"frontend": "frontend"}, [])[0] is False
    assert rep.in_scope("backend", "frontend/src/App.jsx", {"frontend": "frontend"}, [])[0] is False


# 17 accurate final status -----------------------------------------------------------------------------------------------------------------------------
def test_final_status_rules():
    def c(name, status, required=True):
        return Check(name=name, label=name, status=status, required=required, reason="r")
    assert chk.final_status([c("a", "PASSED"), c("b", "PASSED")])[0] == "VERIFIED"
    assert chk.final_status([c("a", "PASSED"), c("b", "FAILED")])[0] == "FAILED"
    assert chk.final_status([c("a", "PASSED"), c("b", "BLOCKED")])[0] == "BLOCKED"
    assert chk.final_status([c("a", "FAILED"), c("b", "BLOCKED")])[0] == "FAILED"
    assert chk.final_status([c("a", "PASSED"), c("t", "SKIPPED")])[0] == "VERIFIED_WITH_WARNINGS"
    assert chk.final_status([c("a", "PASSED"), c("sec", "FAILED", required=False)])[0] == "VERIFIED_WITH_WARNINGS"
    assert chk.final_status([c("t", "SKIPPED")])[0] == "BLOCKED"                     # nothing ran: never verified
    assert chk.final_status([c("a", "PASSED"), c("x", "RUNNING")])[0] == "BLOCKED"


# 18 skipped checks -----------------------------------------------------------------------------------------------------------------------------------
def test_a_project_without_tests_is_never_plainly_verified(tmp_path):
    proj = write(tmp_path / "p", {"calc.py": CALC})
    g, _ = guardian(tmp_path)
    v = g.start("p1", proj, "u1")
    assert statuses(v)["python_tests"] == "SKIPPED" and v.status == "VERIFIED_WITH_WARNINGS"
    assert any("Python unit tests" in w for w in v.report["warnings"])
    assert any(x.startswith("Python unit tests: SKIPPED") for x in v.report["what_was_not_tested"])
    assert any(x.startswith("API contract / integration: SKIPPED") for x in v.report["what_was_not_tested"])


# 19 report ------------------------------------------------------------------------------------------------------------------------------------------------
def test_the_report_says_what_ran_and_what_did_not(tmp_path):
    proj = python_project(tmp_path / "p", calc=CALC_RUNTIME, extra={"requirements.txt": ""})
    g, _ = guardian(tmp_path, fixed_agent(file_answer("calc.py", CALC)))
    v = g.start("p1", proj, "u1")
    r = v.report
    for key in ("project_id", "verification_id", "technology_stack", "started_at", "finished_at", "checks", "counts", "test_summaries",
                "runtime_startup", "repair_attempts", "failures_discovered", "failures_resolved", "remaining_failures", "status",
                "how_to_run", "what_was_tested", "what_was_not_tested", "limitations"):
        assert key in r, key
    assert r["runtime_startup"]["status"] == "not applicable" and r["test_summaries"]["python_tests"] == {"passed": 2}
    # the undefined helper is found statically (quality gate) and at runtime (the tests); both are resolved
    assert {f["category"] for f in r["failures_discovered"]} == {"compilation_error", "runtime_exception"}
    assert len(r["failures_resolved"]) == len(r["failures_discovered"]) and not r["remaining_failures"]
    assert "pytest" in r["how_to_run"] and r["counts"]["PASSED"] >= 4
    assert any("frontend-to-backend calls are not exercised" in x for x in r["limitations"])


# 20 the workflow ------------------------------------------------------------------------------------------------------------------------------------------
def test_the_workflow_routes_on_the_guardian_result(tmp_path, monkeypatch):
    import asyncio
    import backend.graph.parallel_workflow as wf
    from backend.execution_guardian.service import ExecutionGuardian
    g, _ = guardian(tmp_path)
    monkeypatch.setattr("backend.execution_guardian.service.global_execution_guardian", g)
    good = python_project(tmp_path / "good")
    out = asyncio.run(wf.execution_guardian_node({"project_path": str(good), "project_id": "p1"}))
    assert out["verification"]["status"] == "VERIFIED" and out["current_step"] == "execution_guardian"
    state = {**out, "files": {"calc.py": CALC}, "test_results": {"success": True}}
    assert wf.route_after_guardian(state) == "final_approval" and state.get("verified_project_hash")
    bad = python_project(tmp_path / "bad", calc=CALC_WRONG)
    out = asyncio.run(wf.execution_guardian_node({"project_path": str(bad), "project_id": "p1"}))
    failed = {**out, "test_results": {"success": False}, "retry_count": 0}
    assert out["verification"]["status"] == "FAILED" and wf.route_after_guardian(failed) == "debug"
    assert wf.route_after_guardian({**failed, "retry_count": 3, "max_retries": 3}) == "final_approval"
    assert wf.guardian_escalation({**failed, "retry_count": 3, "max_retries": 3}) == "STOPPED_MAX_ATTEMPTS"
    sigs = sorted(f["signature"] for f in out["verification"]["failures"])
    repeated = {**failed, "retry_count": 1, "verification_history": [{"status": "FAILED", "signatures": sigs}]}
    assert wf.guardian_escalation(repeated) == "STOPPED_REPEATED_FAILURE" and wf.route_after_guardian(repeated) == "final_approval"
    blocked = {"verification": {"status": "BLOCKED", "failures": []}, "test_results": {"success": True}}
    assert wf.route_after_guardian(blocked) == "final_approval" and not blocked.get("verified_project_hash")
    # tests passing is no longer enough: a failed verification is not reported as ready
    approval = asyncio.run(wf.final_approval_node({**failed, "retry_count": 3, "max_retries": 3, "files": {"calc.py": CALC_WRONG}}))
    assert approval["approval_request"]["verification"]["status"] == "FAILED"
    assert approval["approval_request"]["deployment_readiness"] != "READY FOR EXPORT"
    assert "execution_guardian" in wf.parallel_graph.get_graph().nodes and isinstance(g, ExecutionGuardian)


def test_the_page_uses_the_real_api():
    root = Path(__file__).resolve().parents[2] / "frontend" / "src"
    service = (root / "services" / "executionGuardian.js").read_text(encoding="utf-8")
    for path in ("/verifications", "/checks", "/repairs", "/report", "/cancel"):
        assert path in service
    comps = root / "components" / "verification"
    for name in ("VerificationDashboard", "VerificationStep", "VerificationStatus", "ErrorSummary", "RepairHistory", "VerificationReport"):
        text = (comps / f"{name}.jsx").read_text(encoding="utf-8")
        for fake in ("Math.random", "mockData", "setTimeout(() => setStatus"):
            assert fake not in text, (name, fake)
    dash = (comps / "VerificationDashboard.jsx").read_text(encoding="utf-8")
    assert "clearInterval" in dash and "getVerification" in dash
    assert "ExecutionGuardianPage" in (root / "App.jsx").read_text(encoding="utf-8")


# genuine: Docker -------------------------------------------------------------------------------------------------------------------------------------------
def _docker_ok():
    try:
        from backend.execution.docker_test_sandbox import docker_available
        return docker_available()
    except Exception:
        return False


@pytest.mark.skipif(not _docker_ok(), reason="Docker is not available: the genuine verification was NOT run")
def test_genuine_backend_startup_failure_is_repaired_in_docker(tmp_path, monkeypatch):
    """A FastAPI app that raises at import: tests and dependencies pass in the Docker sandbox, the app does not start
    in the hardened preview container, the failure is classified and routed to the Backend Agent, its fix is applied
    to the copy, and every check runs again - all in containers."""
    monkeypatch.setenv("AIFORGE_GUARDIAN_CONTAINERS", "on")
    monkeypatch.setenv("AIFORGE_TEST_SANDBOX", "docker")
    proj = write(tmp_path / "p", {"backend/main.py": API_BROKEN_STARTUP, "requirements.txt": "fastapi\nhttpx\n",
                                  "tests/test_ok.py": "def test_ok():\n    assert 1 + 1 == 2\n"})
    gen = fixed_agent(file_answer("backend/main.py", API))
    g, ap = guardian(tmp_path, gen)
    v = g.start("p1", proj, "u1")
    first = {c.name: c.status for c in v.original_checks}
    assert first["backend_startup"] == "FAILED" and first["python_tests"] == "PASSED" and first["python_dependencies"] == "PASSED"
    f = v.original_failures[0]
    assert f.category == "backend_startup_error" and f.responsible_agent == "backend" and "startup failed" in f.log_excerpt
    assert v.status == "VERIFIED", (statuses(v), [(r.outcome, r.note) for r in v.repairs])
    assert v.repairs[0].after["backend_startup"] == "PASSED" and "Docker" in next(c for c in v.checks if c.name == "python_tests").environment
    assert "cleanup verified: True" in next(c for c in v.checks if c.name == "backend_startup").environment
    print(json.dumps({"original": first, "final": statuses(v), "repairs": [r.model_dump(exclude={"started_at", "finished_at"}) for r in v.repairs]},
                     default=str))


@pytest.mark.skipif(not _docker_ok(), reason="Docker is not available: the genuine verification was NOT run")
def test_genuine_frontend_build_failure_is_repaired_by_the_frontend_agent(tmp_path, monkeypatch):
    import backend.execution.docker_test_sandbox as dts
    monkeypatch.setenv("AIFORGE_GUARDIAN_CONTAINERS", "on")
    monkeypatch.setattr(dts, "NODE_IMAGE", "node:20-slim")
    proj = write(tmp_path / "p", {"frontend/package.json": PACKAGE_JSON, "frontend/build.js": BUILD_JS, "frontend/src/App.js": APP_JS_BROKEN})
    gen = fixed_agent(file_answer("frontend/src/App.js", APP_JS))
    g, _ = guardian(tmp_path, gen)
    v = g.start("p1", proj, "u1")
    first = {c.name: c.status for c in v.original_checks}
    assert first["frontend_dependencies"] == "PASSED" and first["frontend_build"] == "FAILED", first
    f = v.original_failures[0]
    assert f.category == "frontend_build_error" and f.responsible_agent == "frontend"
    from backend.agents.factory import AgentFactory
    assert gen.calls and gen.calls[0]["system"] == AgentFactory.create_agent("frontend").system_prompt
    assert v.status == "VERIFIED" and v.repairs[0].files_changed == ["frontend/src/App.js"], (statuses(v), v.repairs)
    assert (proj / "frontend" / "src" / "App.js").read_text(encoding="utf-8") == APP_JS_BROKEN       # project unchanged
    left = subprocess.run([dts.docker_exe() or "docker", "ps", "-a", "-q", "--filter", "name=aiforge_npm_"], capture_output=True,
                          text=True, env=dts.docker_env()).stdout.strip()
    assert left == ""
