"""
Quality Center and production-readiness (CTO) gate: computed only from recorded evidence - the Execution Guardian's
latest verification, the Integration Engine's latest run and the project's files. Nothing is a fixed value; what no
check covered is NOT_EVALUATED. (These used to return 15 hardcoded PASSED gates, "48/48 tests" and fixed scores.)
"""

import json

import pytest

from backend.compatibility.models import CompatFinding, GeneratedTest, IntegrationRun
from backend.compatibility.service import global_integration_engine
from backend.execution_guardian.models import Check, Failure, Verification
from backend.execution_guardian.service import global_execution_guardian

README = "# Notes\n\n" + "Run the backend with uvicorn and the frontend with npm run dev. " * 6


@pytest.fixture
def quality(tmp_path, monkeypatch):
    import backend.routes.export as export
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from backend.generation.store import global_generation_store
    from backend.routes.quality import router
    proj = tmp_path / "Notes_App"
    proj.mkdir()
    records = {"gen_q1": {"generation_id": "gen_q1", "user_id": "alice", "status": "completed", "project_path": str(proj)}}
    monkeypatch.setattr(global_generation_store, "get", lambda gid, default=None: records.get(gid, default))
    monkeypatch.setattr(export, "_safe_project_dir", lambda p: proj if p == str(proj) else None)
    app = FastAPI()
    app.include_router(router)
    return TestClient(app), proj


def _verification():
    return Verification(
        id="ver_q1", project_id="gen_q1", user_id="alice", source="api", status="FAILED", finished_at="2026-10-30T10:00:00",
        checks=[Check(name="python_syntax", label="Python syntax", status="PASSED"),
                Check(name="quality_gate", label="Code-quality gate", status="PASSED"),
                Check(name="python_dependencies", label="Python dependency install", status="PASSED"),
                Check(name="python_tests", label="Python unit tests", status="FAILED", counts={"passed": 7, "failed": 2},
                      error_summary="2 failed, 0 error(s)"),
                Check(name="backend_startup", label="Backend startup", status="BLOCKED", reason="Docker is not available")],
        failures=[Failure(id="f1", check="python_tests", category="unit_test_failure", severity="high", summary="2 tests fail",
                          failing_tests=["tests/test_api.py::test_create", "tests/test_api.py::test_list"],
                          next_action="fix the create endpoint")])


def test_without_evidence_nothing_is_invented(quality):
    client, proj = quality
    data = client.get("/api/projects/gen_q1/quality").json()
    assert data["overall_score"] is None and data["status"] == "not_evaluated"
    gates = {g["name"][3:]: g for g in data["quality_gates"]}
    assert gates["Python Tests"]["status"] == "NOT_EVALUATED" and gates["Python Tests"]["score"] is None
    assert gates["Requirements Fidelity"]["status"] == "NOT_EVALUATED"
    assert gates["Documentation"]["status"] == "FAILED", "no README is a real, checked finding"
    assert data["passed_gates_count"] == 0 and data["tests"] is None
    assert data["testing_findings"]["status"] == "NOT_RUN" and data["testing_findings"]["tests_executed"] is None
    assert data["security"]["checks"] == {} and data["performance"] == {}
    assert {"Verify the project", "Check component compatibility"} <= {r["title"] for r in data["recommendations"]}
    text = json.dumps(data)
    for invented in ("48/48", "94% line coverage", "Sub-50ms", "No CVE vulnerabilities"):
        assert invented not in text


def test_recorded_checks_become_the_gates(quality):
    client, proj = quality
    (proj / "README.md").write_text(README, encoding="utf-8")
    global_execution_guardian.store.put("gen_q1", "verifications", _verification())
    global_integration_engine.store.put("gen_q1", "runs", IntegrationRun(
        id="int_q1", project_id="gen_q1", user_id="alice", kind="verify", status="INCOMPATIBLE",
        finished_at="2026-10-30T10:05:00", test_execution={"status": "FAILED", "counts": {"passed": 3, "failed": 1}},
        tests=[GeneratedTest(id=f"t{i}", kind="valid_request", target="POST /api/notes", description="d",
                             status="failed" if i == 0 else "passed") for i in range(4)],
        findings=[CompatFinding(id="c1", key="k1", rule="auth_mismatch", severity="critical", target="POST /api/notes",
                                responsible_agent="backend", status="open")],
        coverage=[{"check": "database entities vs schema / models", "status": "checked", "detail": "1 entity"}]))
    data = client.get("/api/projects/gen_q1/quality").json()
    gates = {g["name"][3:]: g for g in data["quality_gates"]}
    assert gates["Python Syntax"]["status"] == "PASSED" and gates["Python Syntax"]["source"] == "verification ver_q1"
    assert gates["Python Tests"]["status"] == "FAILED" and "2 tests fail" in " ".join(gates["Python Tests"]["findings"])
    assert gates["Backend Startup"]["status"] == "BLOCKED"
    assert gates["API Contract Compatibility"]["status"] == "FAILED" and gates["API Contract Compatibility"]["critical"] == 1
    assert gates["Database Compatibility"]["status"] == "PASSED"
    assert gates["Documentation"]["status"] == "PASSED"
    assert gates["Test Coverage"]["status"] == "NOT_EVALUATED" and gates["Performance"]["status"] == "NOT_EVALUATED"
    assert data["tests"]["passed"] == 7 and data["tests"]["failed"] == 2 and data["tests"]["coverage"] is None
    assert data["testing_findings"]["failed_tests"] == ["tests/test_api.py::test_create", "tests/test_api.py::test_list"]
    assert data["security"]["checks"]["auth_matches_contract"] == "FAILED"
    # 5 passed (syntax, quality gate, dependencies, database, documentation) of 8 evaluated
    assert (data["passed_gates_count"], data["evaluated_gates_count"]) == (5, 8)
    assert data["overall_score"] == 62.5 and data["status"] == "needs_improvement"
    assert data["test_breakdown"]["contract tests"] == {"passed": 3, "total": 4}
    assert any(r["title"] == "Python Tests" and r["priority"] == "HIGH" for r in data["recommendations"])
    assert data["evidence"]["verification"]["id"] == "ver_q1" and data["evidence"]["integration_run"]["id"] == "int_q1"


def test_quality_report_never_uses_sample_files(quality):
    client, _ = quality
    from backend.graph.executor import global_workflow_executor
    assert global_workflow_executor.get_project_status("no_such_project").get("project_files") in (None, {})
    assert client.get("/quality-report/no_such_project").status_code == 404
    assert client.post("/optimize/no_such_project").status_code == 404


def test_readiness_gate_uses_the_same_evidence(quality):
    _, proj = quality
    from backend.intelligence.cto_gate import AutonomousCtoGate
    (proj / "README.md").write_text(README, encoding="utf-8")
    global_execution_guardian.store.put("gen_q1", "verifications", _verification())
    gate = AutonomousCtoGate()
    report = gate.evaluate("gen_q1")
    dims = {d.name: d for d in report.dimensions}
    assert dims["Testing"].status == "FAIL" and dims["Testing"].score == 0.0
    assert dims["Documentation"].status == "PASS" and dims["Documentation"].score == 100.0
    assert dims["Architecture"].status == "NOT_EVALUATED" and dims["Architecture"].score is None
    assert dims["Performance"].status == "NOT_EVALUATED"
    assert report.decision == "BLOCKED" and any(b.startswith("Testing") for b in report.blocking_issues)
    overridden = gate.override("gen_q1", "alice", "ship the demo")
    assert overridden.decision == "APPROVED_BY_OVERRIDE"
    assert [d.model_dump() for d in overridden.dimensions] == [d.model_dump() for d in report.dimensions]
