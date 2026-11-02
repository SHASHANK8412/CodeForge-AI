"""
Production readiness: every check comes from recorded evidence (Security Guardian assessments, Autopilot
test runs, Performance Engineer runs, static inspection of the project) or is NOT_AVAILABLE; categories
without evidence are left out of the score and readiness is INCOMPLETE without security and test evidence.
The Security Guardian assessments here are real (advisory lookups replaced by an offline stub); test runs are
stored as Autopilot records the way an execution stores them.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import backend.guardian.scanners as scanners
import backend.guardian.service as gs
from backend.evolution.autopilot.models import CheckResult, Execution, now_iso
from backend.evolution.autopilot.service import AutopilotService
from backend.evolution.autopilot.store import AutopilotStore
from backend.guardian.models import ToolRun
from backend.guardian.service import GuardianStore, SecurityGuardian
from backend.readiness.checks import ReadinessCheckCollector
from backend.readiness.gate import ReadinessGate
from backend.readiness.models import CheckSeverity, CheckStatus, ReadinessCheck, ReadinessStatus
from backend.readiness.policy import HardBlockingPolicyEngine
from backend.readiness.scoring import ReadinessScoringEngine
from backend.readiness.service import ProductionReadinessService
from tests.guardian.sample_project import write_sample

CLEAN_APP = '''import logging

from fastapi import FastAPI

logger = logging.getLogger("app")
app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}
'''


@pytest.fixture
def evidence(tmp_path, monkeypatch):
    """Isolated Guardian and Autopilot stores, used by the readiness checks through their globals."""
    import backend.evolution.autopilot.service as aps
    monkeypatch.setattr(scanners, "pip_audit", lambda p: ([], ToolRun(tool="pip-audit", status="unavailable", detail="offline test")))
    monkeypatch.setattr(scanners, "npm_audit", lambda p: ([], ToolRun(tool="npm audit", status="skipped", detail="no package.json")))
    ap = AutopilotService(AutopilotStore(tmp_path / "ap"), background=False)
    sg = SecurityGuardian(GuardianStore(tmp_path / "g"), autopilot=ap, background=False)
    monkeypatch.setattr(gs, "global_security_guardian", sg)
    monkeypatch.setattr(aps, "global_autopilot_service", ap)
    return sg, ap


def clean_project(root):
    (root / "backend").mkdir(parents=True)
    (root / "backend" / "main.py").write_text(CLEAN_APP, encoding="utf-8")
    return root


def record_tests(ap, project_id, status, passed, failed=0, when=None):
    when = when or now_iso()
    check = CheckResult(check_id="tests", label="tests", environment="Docker sandbox (no network, non-root)",
                        started_at=when, finished_at=when, status=status, counts={"passed": passed, "failed": failed})
    ap.store.put(project_id, "executions", Execution(id=f"exe_{status}_{passed}", plan_id="pln_1", project_id=project_id,
                                                     user_id="u1", status="completed", baseline=[check]))


def by_id(checks):
    return {c.id: c for c in checks}


# --- no evidence -----------------------------------------------------------------------------------------------------
def test_without_evidence_nothing_is_assumed(evidence):
    checks = by_id(ReadinessCheckCollector().collect_all_checks("proj_none"))
    assert all(c.status == CheckStatus.NOT_AVAILABLE for c in checks.values())
    assert "real browser" in checks["chk_browser_01"].evidence
    rep = ReadinessGate().evaluate_project("proj_none")
    assert rep.status == ReadinessStatus.INCOMPLETE and rep.overall_score == 0.0 and rep.evidence_coverage == 0.0
    assert "INSUFFICIENT EVIDENCE" in rep.cto_review.executive_summary
    service = ProductionReadinessService()
    service.run_readiness_check("proj_none")
    assert service.approve_deployment("proj_none", "Chief Architect") is False


# --- scoring and policy ------------------------------------------------------------------------------------------------
def _check(category, status, score, blocking=False, severity=CheckSeverity.LOW):
    return ReadinessCheck(id=category, category=category, name=category, status=status, score=score, evidence="e",
                          blocking=blocking, severity=severity)


def test_score_covers_only_categories_with_evidence():
    checks = [_check("Security", CheckStatus.PASS, 100.0), _check("Testing", CheckStatus.FAIL, 50.0),
              _check("Browser Testing", CheckStatus.NOT_AVAILABLE, 0.0)]
    scoring = ReadinessScoringEngine()
    assert scoring.calculate_score(checks) == 75.0                         # (100*0.2 + 50*0.2) / 0.4, nothing assumed
    assert scoring.evidence_coverage(checks) == 40.0
    assert scoring.calculate_score([_check("Testing", CheckStatus.NOT_AVAILABLE, 0.0)]) == 0.0


def test_policy_blocks_and_requires_security_and_test_evidence():
    policy = HardBlockingPolicyEngine()
    status, blockers, _ = policy.evaluate_policy([_check("Security", CheckStatus.FAIL, 40.0, blocking=True),
                                                  _check("Testing", CheckStatus.NOT_AVAILABLE, 0.0)])
    assert status == ReadinessStatus.BLOCKED and blockers
    status, _, warnings = policy.evaluate_policy([_check("Security", CheckStatus.PASS, 100.0),
                                                  _check("Testing", CheckStatus.NOT_AVAILABLE, 0.0)])
    assert status == ReadinessStatus.INCOMPLETE and any("[Testing]" in w for w in warnings)
    status, _, _ = policy.evaluate_policy([_check("Security", CheckStatus.PASS, 100.0), _check("Testing", CheckStatus.PASS, 100.0),
                                           _check("Browser Testing", CheckStatus.NOT_AVAILABLE, 0.0)])
    assert status == ReadinessStatus.READY


# --- real evidence -------------------------------------------------------------------------------------------------------
def test_open_verified_or_detected_vulnerabilities_block(evidence, tmp_path):
    sg, ap = evidence
    project = write_sample(tmp_path / "vulnerable")
    sg.start("p1", project, "u1")
    record_tests(ap, "p1", "passed", 4)
    rep = ReadinessGate().evaluate_project("p1", project=project)
    sec = by_id(rep.checks)["chk_sec_01"]
    assert sec.status == CheckStatus.FAIL and sec.blocking and "critical/high" in sec.evidence
    assert rep.status == ReadinessStatus.BLOCKED
    service = ProductionReadinessService()
    service.run_readiness_check("p1", project=project)
    assert service.approve_deployment("p1") is False


def test_a_clean_assessment_and_passing_tests_can_be_approved(evidence, tmp_path):
    sg, ap = evidence
    project = clean_project(tmp_path / "clean")
    sg.start("p2", project, "u1")
    record_tests(ap, "p2", "passed", 7)
    service = ProductionReadinessService()
    rep = service.run_readiness_check("p2", project=project)
    checks = by_id(rep.checks)
    assert checks["chk_test_01"].status == CheckStatus.PASS and "7 passed" in checks["chk_test_01"].evidence
    assert "exe_passed_7" in checks["chk_test_01"].evidence
    assert checks["chk_sec_01"].status == CheckStatus.WARN          # pip-audit did not run: not a clean pass
    assert rep.status == ReadinessStatus.READY_WITH_WARNINGS and 0 < rep.evidence_coverage < 100
    assert service.approve_deployment("p2", "Chief Architect") is True


def test_failing_tests_block(evidence, tmp_path):
    sg, ap = evidence
    project = clean_project(tmp_path / "clean")
    record_tests(ap, "p3", "passed", 5, when="2026-01-01T00:00:00+00:00")
    record_tests(ap, "p3", "failed", 3, failed=2, when="2026-01-02T00:00:00+00:00")     # the newest run counts
    test = by_id(ReadinessCheckCollector().collect_all_checks("p3", project))["chk_test_01"]
    assert test.status == CheckStatus.FAIL and test.blocking and test.score == 60.0 and "2 failed" in test.evidence


def test_static_project_checks(tmp_path):
    root = clean_project(tmp_path / "static")
    collector = ReadinessCheckCollector()
    assert collector.deployment(root).status == CheckStatus.WARN                       # no Dockerfile
    (root / "Dockerfile").write_text("FROM python:3.12-slim\nCOPY . /app\nCMD [\"uvicorn\"]\n", encoding="utf-8")
    dep = collector.deployment(root)
    assert dep.status == CheckStatus.WARN and "runs as root" in dep.evidence and "no HEALTHCHECK" in dep.evidence
    (root / "Dockerfile").write_text("FROM python:3.12-slim\nUSER app\nHEALTHCHECK CMD curl -f http://localhost/health\n",
                                     encoding="utf-8")
    assert collector.deployment(root).status == CheckStatus.PASS
    assert collector.database(root).status == CheckStatus.NOT_AVAILABLE                  # no database used
    (root / "backend" / "db.py").write_text("import sqlite3\n", encoding="utf-8")
    assert collector.database(root).status == CheckStatus.WARN
    (root / "alembic" / "versions").mkdir(parents=True)
    (root / "alembic" / "versions" / "0001_init.py").write_text("revision = '0001'\n", encoding="utf-8")
    assert collector.database(root).status == CheckStatus.PASS
    assert collector.documentation(root).status == CheckStatus.WARN                     # no README
    (root / "README.md").write_text("# App\n\n## Install\n\npip install -r requirements.txt\n\n## Run\n\nuvicorn backend.main:app\n"
                                    "\n## Test\n\npytest\n" + "Details. " * 30, encoding="utf-8")
    assert collector.documentation(root).status == CheckStatus.PASS
    obs = collector.observability(root)
    assert obs.status == CheckStatus.WARN and "logging" in obs.evidence


def test_history_holds_only_real_evaluations(evidence, tmp_path):
    service = ProductionReadinessService()
    assert service.get_history("p4").snapshots == []
    with pytest.raises(KeyError):
        service.get_diff("p4", 1, 2)
    project = clean_project(tmp_path / "clean")
    service.run_readiness_check("p4", project=project)
    record_tests(evidence[1], "p4", "passed", 3)
    service.run_readiness_check("p4", project=project)
    diff = service.get_diff("p4", 1, 2)
    assert [s.version for s in service.get_history("p4").snapshots] == [1, 2] and diff.new_version == 2


# --- API -------------------------------------------------------------------------------------------------------------------
@pytest.fixture
def api(evidence, tmp_path, monkeypatch):
    import backend.readiness.routes as routes
    import backend.routes.export as export
    from backend.auth.dependencies import get_current_user
    from backend.generation.store import global_generation_store
    project = clean_project(tmp_path / "api_app")
    records = {"gen_mine": {"generation_id": "gen_mine", "user_id": "alice", "status": "completed", "project_path": str(project)},
               "gen_theirs": {"generation_id": "gen_theirs", "user_id": "bob", "status": "completed", "project_path": str(project)}}
    monkeypatch.setattr(global_generation_store, "get", lambda gid, default=None: records.get(gid, default))
    monkeypatch.setattr(export, "_safe_project_dir", lambda p: project if p == str(project) else None)
    monkeypatch.setattr(routes, "global_readiness_service", ProductionReadinessService())
    app = FastAPI()
    app.include_router(routes.day19_readiness_router)
    app.dependency_overrides[get_current_user] = lambda: {"id": "alice"}
    return TestClient(app)


def test_rest_api_enforces_access_and_reports_real_evidence(api):
    assert api.post("/api/projects/gen_theirs/readiness/run").status_code == 403
    assert api.post("/api/projects/aiforge-demo/readiness/run").status_code == 404
    res = api.post("/api/projects/gen_mine/readiness/run")
    assert res.status_code == 200
    report = res.json()["report"]
    assert report["status"] == "INCOMPLETE" and report["evidence_coverage"] < 100
    checks = {c["id"]: c for c in report["checks"]}
    assert checks["chk_dep_01"]["status"] == "WARN" and "static inspection" in checks["chk_dep_01"]["evidence"]
    assert api.post("/api/projects/gen_mine/readiness/approve").json() == {"status": "refused", "approved": False}
    assert api.get("/api/projects/gen_mine/readiness/diff", params={"v1": 1, "v2": 2}).status_code == 404
    assert api.post("/api/projects/gen_mine/readiness/autofix").status_code in (404, 405)
    assert api.get("/api/projects/gen_mine/readiness/history").json()["history"]["snapshots"][0]["version"] == 1
