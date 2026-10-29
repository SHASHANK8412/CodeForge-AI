"""
tests/test_extraordinary_features.py
=====================================
Comprehensive tests for AIForge Extraordinary Features:
1. What-If Engineering Simulator
2. AI Engineering DNA Dependency Graph
3. Autonomous Security Hunter (Bug Bounty)
4. Multi-Agent Architectural Debate Arena
5. Talk to Your Software Assistant
6. Autonomous Production Readiness CTO Gate
"""

import pytest
from fastapi.testclient import TestClient

from backend.intelligence.simulator import global_whatif_simulator
from backend.intelligence.dna_graph import global_dna_graph_engine
from backend.intelligence.bug_hunter import global_security_hunter_agent
from backend.intelligence.debate_engine import global_debate_engine
from backend.intelligence.software_assistant import global_software_assistant_engine
from backend.intelligence.cto_gate import global_cto_gate


@pytest.fixture()
def app_client():
    from backend.main import app
    return TestClient(app, raise_server_exceptions=True)


class TestExtraordinaryFeatures:

    def test_whatif_simulator(self):
        res = global_whatif_simulator.simulate("proj_demo", "What happens if I switch PostgreSQL to MongoDB?")
        assert res.recommendation == "REJECT"
        assert res.files_affected == 27
        assert len(res.affected_components) >= 3

    def test_dna_graph(self):
        graph = global_dna_graph_engine.get_graph("proj_demo")
        assert len(graph.nodes) >= 10
        assert len(graph.edges) >= 10

        impact = global_dna_graph_engine.analyze_impact("proj_demo", "payment")
        assert impact["affected_count"] >= 1

    def test_security_hunter_bug_bounty(self):
        report = global_security_hunter_agent.scan_and_repair("proj_demo")
        assert report.vulnerabilities_investigated == 12
        assert report.vulnerabilities_found == 2
        assert all(v.repaired for v in report.vulnerabilities)

    def test_multi_agent_debate(self):
        verdict = global_debate_engine.run_debate("gen_demo", "FastAPI architecture")
        assert verdict.winning_architect == "Architect A"
        assert len(verdict.proposals) == 3

    def test_talk_to_software_assistant(self):
        res = global_software_assistant_engine.answer_query("proj_demo", "Why is auth implemented this way?")
        assert "JWT" in res.answer
        assert len(res.relevant_files) >= 1

    def test_cto_gate_evaluation(self):
        report = global_cto_gate.evaluate("proj_demo")
        assert report.decision == "BLOCKED"
        assert len(report.dimensions) == 6

        override = global_cto_gate.override_or_fix("proj_demo")
        assert override.decision == "APPROVED"

    def test_api_endpoints(self, app_client):
        # Simulator API
        r_sim = app_client.post("/api/simulator/simulate", json={"project_id": "proj_demo", "proposed_change": "Switch to MongoDB"})
        assert r_sim.status_code == 200

        # DNA Graph API
        r_dna = app_client.get("/api/dna/proj_demo/graph")
        assert r_dna.status_code == 200

        # Bug Bounty API
        r_bug = app_client.get("/api/bug-bounty/proj_demo/report")
        assert r_bug.status_code == 200

        # Debate API
        r_deb = app_client.get("/api/debate/gen_demo")
        assert r_deb.status_code == 200

        # Talk to Software API
        r_talk = app_client.post("/api/software-assistant/chat", json={"project_id": "proj_demo", "query": "Which APIs depend on users?"})
        assert r_talk.status_code == 200

        # CTO Gate API
        r_cto = app_client.get("/api/production-gate/proj_demo")
        assert r_cto.status_code == 200
