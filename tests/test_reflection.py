import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from backend.agents.reflection_agent import ReflectionAgent
from backend.services.reflection_service import ReflectionService
from backend.graph.reflection_node import reflection_node
from backend.main import app


@pytest.mark.anyio
@patch("backend.agents.reflection_agent.ReflectionAgent.generate_async")
async def test_reflection_agent_format(mock_gen):
    agent = ReflectionAgent()
    
    mock_gen.return_value = json.dumps({
        "strengths": ["Clear folder layout"],
        "weaknesses": ["Missing middleware validation"],
        "recommendations": ["Add JWT verification middleware"],
        "lessons": [
            {
                "problem": "Missing validation in route",
                "lesson": "Always validate JWT token details"
            }
        ],
        "reflection_score": 92
    })

    result = await agent.reflect_on_project(
        project_name="E-Commerce",
        code_snippets="def login(): pass",
        reviewer_feedback="Good",
        test_output="Passed",
        validation_report="{}"
    )

    assert result["reflection_score"] == 92
    assert "Clear folder layout" in result["strengths"]
    assert "Missing middleware validation" in result["weaknesses"]
    assert len(result["lessons"]) == 1


def test_reflection_service_lessons_and_similarity(tmp_path):
    service = ReflectionService(memory_dir=tmp_path)
    
    # 1. Add first lesson
    new_lessons = [
        {"problem": "auth credentials hardcoded", "lesson": "Use env variables for API keys"}
    ]
    service.add_lessons(new_lessons)
    
    lessons = service.load_lessons()
    assert len(lessons) == 1
    assert lessons[0]["count"] == 1

    # 2. Add highly similar lesson to trigger merging
    similar_lessons = [
        {"problem": "auth credential hardcoded on main", "lesson": "Use environment variables instead of hardcoding keys"}
    ]
    service.add_lessons(similar_lessons, threshold=0.60)
    
    lessons_merged = service.load_lessons()
    assert len(lessons_merged) == 1
    assert lessons_merged[0]["count"] == 2


def test_reflection_service_prompt_optimization(tmp_path):
    service = ReflectionService(memory_dir=tmp_path)
    
    new_lessons = [
        {"problem": "SQL Injection risk", "lesson": "Use sqlalchemy parameterized statement bindings"}
    ]
    service.add_lessons(new_lessons)
    
    original_prompt = "Build a user login with sql queries database support"
    optimized = service.optimize_prompt(original_prompt)
    
    assert "Production Quality Best Practices" in optimized
    assert "parameterized statement bindings" in optimized


def test_reflection_service_history_and_metrics(tmp_path):
    service = ReflectionService(memory_dir=tmp_path)
    
    service.add_history_record(
        project_name="Todo-App",
        reflection_score=95.0,
        bugs_found=1,
        tests_passed=10,
        recommendations=["Refactor authentication"],
        execution_time=0.45
    )
    
    history = service.load_history()
    assert len(history) == 1
    assert history[0]["project_name"] == "Todo-App"
    
    metrics = service.get_dashboard_metrics()
    assert metrics["projects_generated"] == 1
    assert metrics["reflection_score"] == 95.0
    assert metrics["average_test_score"] == 10.0


@pytest.mark.anyio
@patch("backend.graph.reflection_node.reflection_agent.reflect_on_project")
async def test_reflection_node_workflow(mock_reflect, tmp_path):
    mock_reflect.return_value = {
        "strengths": ["Clean testing coverage"],
        "weaknesses": ["None"],
        "recommendations": ["Maintain current structure"],
        "lessons": [],
        "reflection_score": 98
    }

    # Setup directories
    (tmp_path / "backend").mkdir()
    (tmp_path / "backend/main.py").write_text("def test(): pass")
    
    state = {
        "project_path": str(tmp_path),
        "prompt": "Todo",
        "validation_report": {"overall_score": 95},
        "test_results": {"passed": 5, "failed": 0}
    }

    # Temporarily patch service memory dir to test run in isolations
    with patch("backend.graph.reflection_node.reflection_service.memory_dir", tmp_path), \
         patch("backend.graph.reflection_node.reflection_service.lessons_path", tmp_path / "lessons.json"), \
         patch("backend.graph.reflection_node.reflection_service.history_path", tmp_path / "reflection_history.json"):
        
        # Initialize temp memory files
        (tmp_path / "lessons.json").write_text("[]")
        (tmp_path / "reflection_history.json").write_text("[]")

        updates = await reflection_node(state)
        assert updates["current_step"] == "reflection"
        assert updates["reflection_report"]["reflection_score"] == 98


def test_reflection_api_endpoints(tmp_path):
    client = TestClient(app)
    
    with patch("backend.routes.project.reflection_service.memory_dir", tmp_path), \
         patch("backend.routes.project.reflection_service.lessons_path", tmp_path / "lessons.json"), \
         patch("backend.routes.project.reflection_service.history_path", tmp_path / "reflection_history.json"):
        
        # Initialize temp memory files
        (tmp_path / "lessons.json").write_text("[]")
        (tmp_path / "reflection_history.json").write_text("[]")

        # 1. GET lessons
        resp = client.get("/lessons")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

        # 2. GET metrics
        resp_met = client.get("/metrics")
        assert resp_met.status_code == 200
        assert resp_met.json()["projects_generated"] == 0

        # 3. GET reflection (should be 404 when history is empty)
        resp_ref = client.get("/reflection")
        assert resp_ref.status_code == 404
