"""
Day 11: request routing and the architecture completeness check.

The routing tests originally drove a router graph in backend/graph/workflow.py that has since been
replaced by the canonical generation pipeline. They now check the same behaviour there: each kind
of prompt reaches the right agent, with the real intent classifier and validator in the loop.
"""
from backend.graph import workflow

from tests._pipeline_doubles import DEBUG, EXPLANATION, PipelineDoubles


def test_validate_architecture_sections_complete():
    architecture = """# High-Level Architecture
# Database Schema
# API Specifications
# Folder Structure
# Development Roadmap
# Task Breakdown
# Dependency Graph
# Risk Analysis
# Testing Strategy
# Deployment Strategy
"""
    is_complete, missing = workflow.validate_architecture_sections(architecture)
    assert is_complete is True
    assert missing == []


def test_enforce_architecture_sections_adds_quality_warning():
    architecture = "# Folder Structure\n# API Specifications"
    enriched = workflow.enforce_architecture_sections(architecture)

    assert "Architecture Quality Check" in enriched
    assert "Status: Incomplete" in enriched
    assert "High-Level Architecture" in enriched
    assert "Database Schema" in enriched


def test_graph_routes_to_coding_for_general_prompt(monkeypatch):
    doubles = PipelineDoubles(monkeypatch)
    result = doubles.run("Build a todo app")

    assert result.intent == "PROJECT_GENERATION"
    assert doubles.calls == ["project"]
    assert result.files_map == doubles.project_result["files"]
    assert result.response.startswith("# Project generated: **todo-app**")


def test_graph_routes_to_debug_for_error_prompt(monkeypatch):
    doubles = PipelineDoubles(monkeypatch)
    result = doubles.run("Fix this error in API")

    assert result.intent == "DEBUGGING"
    assert result.agent == "DebugAgent"
    assert doubles.calls[0] == "debug" and "project" not in doubles.calls
    assert "missing import" in result.response and result.response.strip() in DEBUG


def test_graph_routes_to_resume_for_resume_prompt(monkeypatch):
    doubles = PipelineDoubles(monkeypatch)
    result = doubles.run("Improve my resume for backend roles")

    assert result.intent == "RESUME"
    assert result.agent == "ResumeAgent"
    assert doubles.calls == ["resume"]
    assert "Professional Summary" in result.response


def test_graph_routes_to_explanation_for_learning_prompt(monkeypatch):
    doubles = PipelineDoubles(monkeypatch)
    result = doubles.run("Explain what is MVC architecture")

    assert result.intent == "EXPLANATION"
    assert result.response.strip() == EXPLANATION
    assert not {"project", "debug", "coding", "resume"} & set(doubles.calls)
