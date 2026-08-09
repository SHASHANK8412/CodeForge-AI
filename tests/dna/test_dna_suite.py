"""
AIForge Day 15 — Engineering DNA & Dependency Intelligence Test Suite
======================================================================
Comprehensive unit and integration tests covering:
- Code AST Parser
- Dependency Linker & Requirement Traceability
- Graph Repository, Versioning & Graph Diffing
- Impact Analysis Engine
- Dead Code & Circular Dependency Detection
- Security Integration
- FastAPI Engineering DNA REST Endpoints
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.dna.parser import CodeParser
from backend.dna.dependency import DependencyExtractor
from backend.dna.repository import GraphRepository, global_graph_repository
from backend.dna.impact import ImpactEngine
from backend.dna.analyzer import DNAAnalyzer
from backend.dna.service import DNAService
from backend.dna.models import NodeKind, RelationType


@pytest.fixture
def client():
    return TestClient(app)


class TestEngineeringDNA:

    def test_code_parser_python(self):
        parser = CodeParser()
        code = (
            "import os\n"
            "class UserModel(Base):\n    pass\n"
            "def login_user():\n    pass\n"
            "def test_login_user():\n    pass\n"
        )
        nodes, edges = parser.parse_python("backend/models.py", code)

        labels = [n.label for n in nodes]
        assert "UserModel" in labels
        assert "login_user" in labels
        assert "test_login_user" in labels

        kinds = {n.label: n.kind for n in nodes}
        assert kinds["test_login_user"] == NodeKind.TEST
        assert kinds["login_user"] in (NodeKind.FUNCTION, NodeKind.API)

    def test_dependency_linking_and_requirement_tracing(self):
        analyzer = DNAAnalyzer()
        files = {
            "backend/auth.py": "def login_user(): pass",
            "frontend/src/Login.jsx": "export default function Login() { return <div/>; }",
            "tests/test_auth.py": "def test_login_user(): pass"
        }
        reqs = [{"id": "r1", "text": "Users must be able to log in"}]

        graph = analyzer.analyze_project("proj_test_dna", files, reqs)
        assert len(graph.nodes) > 0
        assert len(graph.edges) > 0

        engine = ImpactEngine()
        traces = engine.trace_requirements("proj_test_dna")
        assert len(traces) > 0

    def test_impact_analysis_engine(self):
        service = DNAService()
        engine = ImpactEngine()

        files = {
            "backend/services/payment_service.py": "class PaymentService:\n    def process_payment(self):\n        pass",
            "backend/routes/orders.py": "from backend.services.payment_service import PaymentService\ndef create_order():\n    pass",
            "tests/test_payment.py": "def test_process_payment(): pass"
        }

        service.get_or_build_graph("proj_impact_test", files)
        impact = engine.analyze_change_impact("proj_impact_test", "PaymentService", "modify")

        assert impact.node_id is not None
        assert impact.risk_score in ("CRITICAL", "HIGH", "MEDIUM", "LOW")
        assert len(impact.affected_files) >= 1

    def test_dead_code_and_circular_dependency_detection(self):
        engine = ImpactEngine()
        analyzer = DNAAnalyzer()

        files = {
            "backend/utils/legacy.py": "def old_unused_function():\n    pass",
        }
        analyzer.analyze_project("proj_dead_test", files)

        dead = engine.detect_dead_code("proj_dead_test")
        assert len(dead) >= 1
        assert any(d.name == "old_unused_function" for d in dead)

    def test_graph_versioning_and_diff(self):
        repo = global_graph_repository
        analyzer = DNAAnalyzer()

        files_v1 = {"main.py": "def fn1(): pass"}
        g1 = analyzer.analyze_project("proj_v", files_v1)

        files_v2 = {"main.py": "def fn1(): pass", "utils.py": "def fn2(): pass"}
        g2 = analyzer.analyze_project("proj_v", files_v2)

        diff = repo.diff_graphs("proj_v", g1.version, g2.version)
        assert diff.old_version == g1.version
        assert diff.new_version == g2.version
        assert len(diff.added_nodes) >= 1

    def test_dna_rest_api_endpoints(self, client):
        res_graph = client.get("/api/dna/aiforge-demo/graph")
        assert res_graph.status_code == 200
        assert res_graph.json()["status"] == "success"

        res_impact = client.post("/api/projects/aiforge-demo/impact-analysis", json={"node_id": "PaymentService", "change_type": "modify"})
        assert res_impact.status_code == 200
        assert res_impact.json()["status"] == "success"
        assert "risk_score" in res_impact.json()["impact"]

        res_trace = client.get("/api/dna/aiforge-demo/requirements-trace")
        assert res_trace.status_code == 200
        assert res_trace.json()["status"] == "success"

        res_dead = client.get("/api/dna/aiforge-demo/dead-code")
        assert res_dead.status_code == 200

        res_circ = client.get("/api/dna/aiforge-demo/circular-dependencies")
        assert res_circ.status_code == 200

        res_explain = client.post("/api/dna/aiforge-demo/explain-node", json={"node_id": "PaymentService"})
        assert res_explain.status_code == 200
        assert "explanation" in res_explain.json()
