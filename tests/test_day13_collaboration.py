"""
Day 13: agent collaboration - which requests get a reviewer pass.

Originally written against the removed router graph in backend/graph/workflow.py. The same rules
now live in the generation pipeline and the review policy:
  * project generation is reviewed inside the project workflow (its reviewer node), not in chat;
  * explanations and resume edits are never reviewed;
  * a debugging answer is reviewed when its validation score is borderline (< 0.85).
"""
from backend.graph import workflow

from tests._pipeline_doubles import EXPLANATION, PipelineDoubles


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


def _successors(graph, node):
    return {e.target for e in graph.get_graph().edges if e.source == node}


def test_graph_coding_path_runs_reviewer_then_explanation(monkeypatch):
    doubles = PipelineDoubles(monkeypatch)
    result = doubles.run("Create Login API", session_id="s1")

    assert result.intent == "PROJECT_GENERATION"
    assert doubles.calls == ["project"], "the chat pipeline hands project review to the workflow"
    assert result.execution_strategy == "WORKFLOW"

    # In the project workflow the reviewer runs on the assembled code, before documentation.
    from backend.graph.parallel_workflow import parallel_graph
    assert _successors(parallel_graph, "assembly") == {"reviewer"}
    assert _successors(parallel_graph, "reviewer") == {"documentation"}


def test_graph_explanation_path_skips_reviewer(monkeypatch):
    doubles = PipelineDoubles(monkeypatch)
    result = doubles.run("Explain previous code", session_id="s2")

    assert result.intent == "EXPLANATION"
    assert "reviewer" not in doubles.calls
    assert result.response.strip() == EXPLANATION


def test_graph_debug_path_runs_reviewer_then_explanation(monkeypatch):
    from backend.services import generation_service as gs
    doubles = PipelineDoubles(monkeypatch)
    real_validate = gs.global_output_validator.validate

    def borderline(**kwargs):
        res = real_validate(**kwargs)
        return res.model_copy(update={"score": min(res.score, 0.8)})

    monkeypatch.setattr(gs.global_output_validator, "validate", borderline)
    result = doubles.run("Fix previous bug", session_id="s3")

    assert result.intent == "DEBUGGING"
    assert doubles.calls == ["debug", "reviewer"]


def test_graph_debug_path_with_strong_answer_is_not_reviewed(monkeypatch):
    doubles = PipelineDoubles(monkeypatch)
    result = doubles.run("Fix previous bug", session_id="s3b")

    assert result.intent == "DEBUGGING" and result.quality_score >= 85
    assert doubles.calls == ["debug"]


def test_graph_resume_path_routes_to_explanation_only(monkeypatch):
    doubles = PipelineDoubles(monkeypatch)
    result = doubles.run("Generate Resume", session_id="s4")

    assert result.intent == "RESUME"
    assert doubles.calls == ["resume"]
    assert "reviewer" not in doubles.calls
