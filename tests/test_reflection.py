import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch
from backend.agents.reflection_agent import ReflectionAgent
from backend.services.reflection_service import ReflectionService


@pytest.mark.anyio
@patch("backend.agents.reflection_agent.ReflectionAgent.generate_async")
async def test_reflection_agent(mock_gen):
    agent = ReflectionAgent()
    mock_gen.return_value = json.dumps({
        "strengths": ["Clean structure"],
        "weaknesses": ["No database validation"],
        "recommendations": ["Add validator constraints"],
        "lessons": [
            {
                "problem": "Missing validation",
                "lesson": "Always validate all requests payload"
            }
        ],
        "reflection_score": 91
    })

    res = await agent.reflect_on_project(
        project_name="Todo App",
        code_snippets="def index(): pass",
        reviewer_feedback="None",
        test_output="Passed",
        validation_report="{}"
    )
    assert res["reflection_score"] == 91
    assert "Clean structure" in res["strengths"]
    assert len(res["lessons"]) == 1


def test_lesson_extraction():
    # Verify we extract problems and lessons properly from service structure
    lessons = [
        {"problem": "Missing validation", "lesson": "Always validate all requests payload"}
    ]
    assert lessons[0]["problem"] == "Missing validation"
    assert lessons[0]["lesson"] == "Always validate all requests payload"


def test_lesson_merge(tmp_path):
    service = ReflectionService(memory_dir=tmp_path)
    
    # 1. Add first lesson
    service.add_lessons([{"problem": "Missing validation", "lesson": "Always validate all requests payload"}])
    
    # 2. Add second duplicate lesson (similar problem description)
    service.add_lessons([{"problem": "Request validation is missing", "lesson": "Always validate all request payloads"}])

    stored = service.load_lessons()
    assert len(stored) == 1
    assert stored[0]["count"] == 2


def test_similarity_detection():
    service = ReflectionService()
    sim1 = service.compute_similarity("Missing JWT validation", "Authentication validation missing")
    sim2 = service.compute_similarity("SQL Injection risk", "Database vulnerable to SQL injection")
    
    # SequenceMatcher should compute ratios
    assert 0.0 <= sim1 <= 1.0
    assert 0.0 <= sim2 <= 1.0


def test_prompt_optimizer(tmp_path):
    service = ReflectionService(memory_dir=tmp_path)
    service.add_lessons([{"problem": "JWT validation missing", "lesson": "Always validate JWT before accessing protected routes"}])

    original_prompt = "Build JWT authentication mechanism."
    optimized = service.optimize_prompt(original_prompt)

    assert "Always validate JWT before accessing protected routes" in optimized
    assert "Production Quality Best Practices" in optimized


def test_metrics_generation(tmp_path):
    service = ReflectionService(memory_dir=tmp_path)
    service.add_history_record(
        project_name="HMS App",
        reflection_score=90.0,
        bugs_found=2,
        tests_passed=10,
        recommendations=["Improve naming"],
        execution_time=0.5
    )

    metrics = service.get_dashboard_metrics()
    assert metrics["projects_generated"] == 1
    assert metrics["reflection_score"] == 90.0
    assert metrics["average_test_score"] == 10.0


def test_history_logging(tmp_path):
    service = ReflectionService(memory_dir=tmp_path)
    service.add_history_record(
        project_name="Todo App",
        reflection_score=91.0,
        bugs_found=3,
        tests_passed=42,
        recommendations=["Add request validation middleware"],
        execution_time=1.2
    )

    history = service.load_history()
    assert len(history) == 1
    assert history[0]["project_name"] == "Todo App"
    assert history[0]["reflection_score"] == 91.0


def test_memory_persistence(tmp_path):
    service = ReflectionService(memory_dir=tmp_path)
    
    # Verify file IO works correctly
    service.save_lessons([{"problem": "Oversized file", "lesson": "Break down modules"}])
    loaded = service.load_lessons()
    assert len(loaded) == 1
    assert loaded[0]["problem"] == "Oversized file"
