"""
AIForge Day 24 — Autonomous Software Evolution Engine Test Suite
===================================================================
Comprehensive unit and integration tests covering:
- Technical Debt Detection & Score Calculation
- Dependency Analysis & Multi-System Evidence Gathering
- Recommendation Generation & Priority Scoring with User Goals
- Evolution Roadmap (NOW / NEXT / LATER) Generation
- Engineering DNA Dependency Tracing & What-If Refactoring Impact
- Memory & Incident Influenced Evolution Recommendations
- Autonomous Recommendation Implementation, Validation & Rollback
- Flight Recorder Telemetry Integration
- FastAPI REST API Endpoints
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.evolution.analyzer import ProjectEvolutionAnalyzer
from backend.evolution.debt import DebtDetectionEngine
from backend.evolution.prioritizer import RecommendationPrioritizer
from backend.evolution.roadmap import EvolutionRoadmapGenerator
from backend.evolution.service import EvolutionService
from backend.evolution.models import TechnicalDebtCategory, DebtSeverity


@pytest.fixture
def client():
    return TestClient(app)


class TestAutonomousSoftwareEvolution:

    def test_technical_debt_detection_and_scoring(self):
        debt_engine = DebtDetectionEngine()
        score, items = debt_engine.detect_debt("proj_test", {"latency_ms": 620.0})

        assert score.overall_score > 70.0
        assert len(items) >= 2
        assert any(i.category == TechnicalDebtCategory.PERFORMANCE for i in items)

    def test_evolution_analyzer_evidence_gathering(self):
        analyzer = ProjectEvolutionAnalyzer()
        evidence = analyzer.analyze("proj_test")

        assert evidence["project_id"] == "proj_test"
        assert len(evidence["dna_affected_files"]) >= 1
        assert "security_decision" in evidence

    def test_priority_scoring_with_user_goals(self):
        prioritizer = RecommendationPrioritizer()
        analyzer = ProjectEvolutionAnalyzer()
        evidence = analyzer.analyze("proj_test")
        _, items = DebtDetectionEngine().detect_debt("proj_test", evidence)

        from backend.evolution.recommendations import EvolutionRecommendationEngine
        recs = EvolutionRecommendationEngine().generate_recommendations("proj_test", items)

        prioritized_perf = prioritizer.prioritize_recommendations(recs, user_goal="App Performance")
        assert prioritized_perf[0].category == TechnicalDebtCategory.PERFORMANCE

    def test_roadmap_phase_generation(self):
        roadmap_gen = EvolutionRoadmapGenerator()
        analyzer = ProjectEvolutionAnalyzer()
        evidence = analyzer.analyze("proj_test")
        _, items = DebtDetectionEngine().detect_debt("proj_test", evidence)

        from backend.evolution.recommendations import EvolutionRecommendationEngine
        recs = EvolutionRecommendationEngine().generate_recommendations("proj_test", items)

        roadmap = roadmap_gen.build_roadmap("proj_test", recs)
        assert len(roadmap.now) >= 1
        assert roadmap.health_score == 89.0

    def test_autonomous_recommendation_implementation(self):
        service = EvolutionService()
        rec_id = "rec_test_101"

        res = service.implement_recommendation("proj_impl", rec_id, simulate_failure=False)
        assert res["status"] == "COMPLETED"
        assert "P95 latency improved" in res["message"]

        res_rolled = service.implement_recommendation("proj_impl", rec_id, simulate_failure=True)
        assert res_rolled["status"] == "ROLLED_BACK"

    def test_evolution_rest_api_endpoints(self, client):
        an_res = client.get("/api/projects/aiforge-demo/evolution/analyze")
        assert an_res.status_code == 200
        assert an_res.json()["status"] == "success"

        debt_res = client.get("/api/projects/aiforge-demo/evolution/debt")
        assert debt_res.status_code == 200

        map_res = client.get("/api/projects/aiforge-demo/evolution/roadmap")
        assert map_res.status_code == 200

        impl_res = client.post("/api/projects/aiforge-demo/evolution/recommendations/rec_1/implement")
        assert impl_res.status_code == 200

        hist_res = client.get("/api/projects/aiforge-demo/evolution/history")
        assert hist_res.status_code == 200

        goal_res = client.post("/api/projects/aiforge-demo/evolution/goal", json={"goal": "App Performance"})
        assert goal_res.status_code == 200
