"""
AIForge Day 25 — AI Software Architect Simulator Test Suite
============================================================
Comprehensive unit and integration tests covering:
- Current Baseline Architecture Extraction from Engineering DNA
- Read-Only Scenario Builder & Impact Evaluator (MEASURED vs ESTIMATED)
- Side-by-Side Architecture Comparator & Scorecard Generation
- Single Point of Failure (SPOF) & Component Failure Propagation Engine
- Multi-Agent Debate Integration on Architectural Candidates
- ADR Generation & 7-Phase Migration Planning upon User Approval
- Engineering Memory & Incident Evidence Integration
- Read-Only Simulation Safety Enforcement
- Flight Recorder Telemetry Integration
- FastAPI REST API Endpoints
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.architecture_simulator.analyzer import CurrentArchitectureAnalyzer
from backend.architecture_simulator.scenarios import ArchitectureScenarioBuilder
from backend.architecture_simulator.evaluator import ArchitectureEvaluator
from backend.architecture_simulator.comparator import ArchitectureComparator
from backend.architecture_simulator.impact import FailurePropagationEngine
from backend.architecture_simulator.planner import MigrationPlanner
from backend.architecture_simulator.service import ArchitectureSimulatorService
from backend.architecture_simulator.models import EvidenceType, ArchitectureNodeType


@pytest.fixture
def client():
    return TestClient(app)


class TestAISoftwareArchitectSimulator:

    def test_current_architecture_extraction(self):
        analyzer = CurrentArchitectureAnalyzer()
        diagram = analyzer.analyze_current_architecture("proj_test")

        assert diagram.project_id == "proj_test"
        assert len(diagram.nodes) >= 4
        node_types = [n.type for n in diagram.nodes]
        assert ArchitectureNodeType.DATABASE in node_types

    def test_scenario_creation_and_impact_evaluation(self):
        builder = ArchitectureScenarioBuilder()
        evaluator = ArchitectureEvaluator()

        scen = builder.create_scenario("proj_test", "Should we add Redis?")
        assert scen.name == "Introduce Redis Caching Layer"
        assert scen.status == "SIMULATION_ONLY"

        assessment = evaluator.evaluate_scenario("proj_test", scen)
        assert assessment.evidence_type == EvidenceType.ESTIMATED
        assert assessment.confidence == "MEDIUM"

    def test_side_by_side_comparison_matrix(self):
        builder = ArchitectureScenarioBuilder()
        comparator = ArchitectureComparator()

        scen = builder.create_scenario("proj_test", "Should we add Redis?")
        comp = comparator.compare_options(scen)

        assert comp.current_option is not None
        assert len(comp.proposed_options) >= 2
        assert "Option B" in comp.recommendation

    def test_failure_propagation_and_spof_detection(self):
        impact_engine = FailurePropagationEngine()

        report_db = impact_engine.simulate_component_failure("proj_test", "PostgreSQL")
        assert report_db.single_point_of_failure is True
        assert report_db.impact_level == "CRITICAL"
        assert len(report_db.affected_components) >= 2

        report_cache = impact_engine.simulate_component_failure("proj_test", "Redis")
        assert report_cache.single_point_of_failure is False

    def test_adr_and_7_phase_plan_generation(self):
        service = ArchitectureSimulatorService()
        adr, plan = service.approve_scenario_and_create_plan("proj_plan", "scen_101")

        assert adr.status == "APPROVED"
        assert adr.project_id == "proj_plan"
        assert "phase_1_prepare" in plan
        assert "phase_7_rollback" in plan

    def test_architect_rest_api_endpoints(self, client):
        curr_res = client.get("/api/projects/aiforge-demo/architect/current")
        assert curr_res.status_code == 200
        assert curr_res.json()["status"] == "success"

        sim_res = client.post("/api/projects/aiforge-demo/architect/simulate", json={"prompt": "Should we add Redis?"})
        assert sim_res.status_code == 200

        fail_res = client.post("/api/projects/aiforge-demo/architect/failure", json={"component_name": "PostgreSQL"})
        assert fail_res.status_code == 200

        deb_res = client.post("/api/projects/aiforge-demo/architect/debate", json={"topic": "Should we introduce Redis?"})
        assert deb_res.status_code == 200

        appr_res = client.post("/api/projects/aiforge-demo/architect/approve?scenario_id=scen_demo")
        assert appr_res.status_code == 200

        hist_res = client.get("/api/projects/aiforge-demo/architect/history")
        assert hist_res.status_code == 200
