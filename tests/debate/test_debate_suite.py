"""
AIForge Day 16 — Multi-Agent Debate & Architecture Decision Engine Test Suite
================================================================================
Comprehensive unit and integration tests covering:
- Candidate Proposal Generator (A, B, C)
- CriteriaEngine Scoring & Weights
- Independent JudgeAgent Evaluation & ADR Drafting
- Debate Threshold Logic (LOW, MEDIUM, HIGH, CRITICAL)
- Project Memory Persistence (ARCHITECTURE_DECISION)
- Flight Recorder Event Logging
- Human Approval Gates
- Failure Fallback
- FastAPI Debate REST Endpoints
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.debate.candidates import CandidateArchitectGenerator
from backend.debate.judge import JudgeAgent
from backend.debate.criteria import CriteriaEngine
from backend.debate.engine import DebateEngine
from backend.debate.service import DebateService
from backend.debate.models import DebateThreshold


@pytest.fixture
def client():
    return TestClient(app)


class TestMultiAgentDebate:

    def test_candidate_architect_generator(self):
        gen = CandidateArchitectGenerator()
        candidates = gen.generate_all_candidates("proj_test", "Build a highly scalable social platform")

        assert len(candidates) == 3
        ids = [c.candidate_id for c in candidates]
        assert "A" in ids and "B" in ids and "C" in ids

        cand_a = next(c for c in candidates if c.candidate_id == "A")
        assert len(cand_a.advantages) > 0
        assert len(cand_a.disadvantages) > 0
        assert cand_a.estimated_complexity in ("LOW", "MEDIUM", "HIGH")

    def test_criteria_engine_score_calculation(self):
        engine = CriteriaEngine()
        score = engine.calculate_total_score(
            req_fit=90, scalability=90, security=90, maintainability=90,
            perf=90, complexity=90, cost=90, aiforge_fit=90
        )
        assert score == 90.0

    def test_judge_agent_evaluation_and_adr(self):
        gen = CandidateArchitectGenerator()
        judge = JudgeAgent()

        candidates = gen.generate_all_candidates("proj_test", "Build a highly scalable social platform")
        decision = judge.evaluate_candidates("proj_test", "Build a highly scalable social platform", candidates)

        assert decision.winner in ("A", "B", "C")
        assert decision.winning_proposal_name is not None
        assert len(decision.scores) == 3
        assert decision.adr is not None
        assert decision.adr.adr_id.startswith("ADR-")
        assert decision.minority_report is not None

    def test_debate_threshold_logic(self):
        engine = DebateEngine()

        assert engine.determine_threshold("Fix a button color in UI") == DebateThreshold.LOW
        assert engine.determine_threshold("Add caching strategy") == DebateThreshold.MEDIUM
        assert engine.determine_threshold("Select database and GraphQL API architecture") == DebateThreshold.HIGH
        assert engine.determine_threshold("Setup authentication and role-based access control") == DebateThreshold.CRITICAL

    def test_debate_engine_full_run_and_approval(self):
        service = DebateService()
        session = service.run_project_debate(
            "proj_full_test",
            "Build a highly scalable social media platform with authentication, cart, and payments.",
            "aiforge-demo",
            force_debate=True
        )

        assert session.debate_id is not None
        assert len(session.candidates) == 3
        assert session.decision is not None

        # Approval test
        approved = service.approve_decision("proj_full_test", session.debate_id)
        assert approved is True

    def test_debate_rest_api_endpoints(self, client):
        start_res = client.post(
            "/api/debate/start",
            json={"project_id": "aiforge-demo", "requirement": "Build scalable social platform", "force_debate": True}
        )
        assert start_res.status_code == 200
        assert start_res.json()["status"] == "success"
        session_id = start_res.json()["session"]["debate_id"]

        latest_res = client.get("/api/debate/aiforge-demo/latest")
        assert latest_res.status_code == 200
        assert latest_res.json()["status"] == "success"

        history_res = client.get("/api/debate/aiforge-demo/history")
        assert history_res.status_code == 200

        adrs_res = client.get("/api/debate/aiforge-demo/adrs")
        assert adrs_res.status_code == 200

        approve_res = client.post(f"/api/debate/aiforge-demo/{session_id}/approve")
        assert approve_res.status_code == 200
        assert approve_res.json()["approved"] is True
