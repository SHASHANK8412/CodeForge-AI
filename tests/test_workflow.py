"""
The project-generation workflow and the legacy /generate endpoint.

These tests used to drive backend/graph/project_workflow.py, a second pipeline that nothing in
the application ran (it has been removed). The pipeline that generations use is
backend/graph/parallel_workflow.py; tests/test_pipeline_integration.py runs it end to end. Here:
its wiring, and the /generate contract.
"""
from fastapi.testclient import TestClient

from backend.graph.parallel_workflow import parallel_graph
from backend.main import app


def _edges():
    graph = parallel_graph.get_graph()
    out = {}
    for e in graph.edges:
        out.setdefault(e.source, set()).add(e.target)
    return out


def test_entire_pipeline():
    edges = _edges()
    assert edges["__start__"] == {"planner"}
    assert edges["planner"] == {"architect"}
    assert edges["architect"] == {"human_approval"}
    assert {"dispatch_parallel", "architect", "human_approval"} >= edges["human_approval"] >= {"dispatch_parallel", "architect"}
    assert edges["dispatch_parallel"] == {"frontend", "backend", "database"}, "the three code agents fan out"
    assert edges["frontend"] == edges["backend"] == edges["database"] == {"assembly"}, "and join at assembly"
    chain = ["assembly", "reviewer", "documentation", "build_validation", "dependency_manager",
             "security_scan", "performance", "execution_validation", "testing"]
    for a, b in zip(chain, chain[1:]):
        assert edges[a] == {b}
    assert edges["testing"] >= {"debug", "final_approval"}
    assert edges["debug"] == {"patch"} and edges["patch"] == {"execution_validation"}, "bounded repair loop"
    assert "packaging" in edges["final_approval"]
    assert edges["health_check"] == {"__end__"}


def test_generate_endpoint(monkeypatch):
    from types import SimpleNamespace
    from backend.services import generation_service

    async def fake_generate(user_prompt, session_id=None, **_k):
        return SimpleNamespace(
            plan_text="1. Parse resumes", arch_text="FastAPI + React", response="Here is the analyzer.",
            files_map={"backend/main.py": "app = None\n", "frontend/src/App.jsx": "export default 1\n"},
            intent="PROJECT_GENERATION", agent="AutonomousSoftwareEngineer", quality_score=82.0, validation_passed=True)

    monkeypatch.setattr(generation_service.global_generation_pipeline, "generate", fake_generate)
    response = TestClient(app).post("/generate", json={"prompt": "Build an AI Resume Analyzer"})
    assert response.status_code == 200
    data = response.json()
    assert data["plan"] == "1. Parse resumes"
    assert data["architecture"] == "FastAPI + React"
    assert data["backend"] == "app = None\n" and data["frontend"] == "export default 1\n"
    assert data["generated_code"] == "app = None\n" and data["explanation"] == "Here is the analyzer."
    # This path neither reviews nor tests the code; it must not say it did.
    assert data["review"] is None and data["tests"] is None
    assert data["reviewed_code"] is None and data["testing_report"] is None
    assert "15/15" not in response.text and "Pytest Suite Generated" not in response.text
