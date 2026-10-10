"""
AIForge Day 19 — Autonomous Production Readiness Gate Test Suite
=================================================================
Comprehensive unit and integration tests covering:
- Readiness Checks Engine & Evidence Collection
- Transparent Weighted Scoring System
- Hard Blocking Rules & Readiness Policies
- CTO Review Agent Executive Summaries
- Human Approval Gate
- Automatic Repair Loop
- Readiness History & Version Diffs
- Flight Recorder Event Emissions
- FastAPI REST API Endpoints
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.readiness.checks import ReadinessCheckCollector
from backend.readiness.scoring import ReadinessScoringEngine
from backend.readiness.policy import HardBlockingPolicyEngine
from backend.readiness.evaluator import CTOReviewAgent
from backend.readiness.gate import ReadinessGate
from backend.readiness.service import ProductionReadinessService
from backend.readiness.models import ReadinessStatus, CheckStatus


@pytest.fixture
def client():
    return TestClient(app)


class TestProductionReadinessGate:

    def test_readiness_checks_evidence_collector(self):
        collector = ReadinessCheckCollector()
        checks = collector.collect_all_checks("proj_test", simulate_security_block=False)

        assert len(checks) >= 8
        cat_names = [c.category for c in checks]
        assert "Security" in cat_names
        assert "Testing" in cat_names
        assert "Performance" in cat_names
        assert "Browser Testing" in cat_names

    def test_transparent_scoring_engine(self):
        collector = ReadinessCheckCollector()
        scoring = ReadinessScoringEngine()

        checks = collector.collect_all_checks("proj_test", simulate_security_block=False)
        score = scoring.calculate_score(checks)
        assert 80.0 <= score <= 100.0

    def test_hard_blocking_rules_scenario1_ready(self):
        gate = ReadinessGate()
        rep = gate.evaluate_project("proj_test", version=1, simulate_security_block=False)

        assert rep.status in (ReadinessStatus.READY, ReadinessStatus.READY_WITH_WARNINGS)
        assert rep.overall_score >= 85.0
        assert len(rep.blocking_issues) == 0

    def test_hard_blocking_rules_scenario2_critical_security_block(self):
        gate = ReadinessGate()
        rep = gate.evaluate_project("proj_test", version=2, simulate_security_block=True)

        assert rep.status == ReadinessStatus.BLOCKED
        assert len(rep.blocking_issues) >= 1
        assert any("SQL injection" in b or "Secret" in b for b in rep.blocking_issues)
        assert rep.cto_review.recommendation == ReadinessStatus.BLOCKED

    def test_autofix_scenario3_recovery(self):
        service = ProductionReadinessService()
        rep_blocked = service.run_readiness_check("proj_autofix", simulate_security_block=True)
        assert rep_blocked.status == ReadinessStatus.BLOCKED

        rep_fixed = service.autofix_blocking_issues("proj_autofix")
        assert rep_fixed.status in (ReadinessStatus.READY, ReadinessStatus.READY_WITH_WARNINGS)

    def test_human_approval_gate(self):
        service = ProductionReadinessService()

        # Cannot approve blocked project
        service.run_readiness_check("proj_approve_blocked", simulate_security_block=True)
        approved_blocked = service.approve_deployment("proj_approve_blocked", "VP Engineering")
        assert approved_blocked is False

        # Can approve ready project
        service.run_readiness_check("proj_approve_ready", simulate_security_block=False)
        approved_ready = service.approve_deployment("proj_approve_ready", "Chief Architect")
        assert approved_ready is True

    def test_readiness_history_and_diff(self):
        service = ProductionReadinessService()
        history = service.get_history("proj_history_test")
        assert len(history.snapshots) >= 2

        diff = service.get_diff("proj_history_test", 1, 2)
        assert diff.old_version == 1
        assert diff.new_version == 2
        assert diff.score_change >= 0.0

    def test_readiness_rest_api_endpoints(self, client):
        run_res = client.post("/api/projects/aiforge-demo/readiness/run", json={"simulate_security_block": False})
        assert run_res.status_code == 200
        assert run_res.json()["status"] == "success"

        rep_res = client.get("/api/projects/aiforge-demo/readiness/report")
        assert rep_res.status_code == 200

        appr_res = client.post("/api/projects/aiforge-demo/readiness/approve", json={"approver": "CTO"})
        assert appr_res.status_code == 200

        hist_res = client.get("/api/projects/aiforge-demo/readiness/history")
        assert hist_res.status_code == 200

        diff_res = client.get("/api/projects/aiforge-demo/readiness/diff?v1=1&v2=2")
        assert diff_res.status_code == 200

        exp_res = client.get("/api/projects/aiforge-demo/readiness/export")
        assert exp_res.status_code == 200
        assert "json" in exp_res.json()
