"""
Day 14: efficiency - small models and short paths for simple requests.

The path tests were written against the removed router graph in backend/graph/workflow.py; they
now check the generation pipeline's fast paths. Model selection depends on which Ollama models are
installed, so the tests pin the installed set instead of depending on the machine.
"""
import pytest

from backend.config import OLLAMA_MEDIUM_MODEL, OLLAMA_SMALL_MODEL
from backend.services.llm import select_model

from tests._pipeline_doubles import EXPLANATION, RESUME, PipelineDoubles

CODING_MODEL = "qwen2.5-coder:latest"


@pytest.fixture
def default_models(monkeypatch):
    """The documented default install: one general model and one coding model, no env overrides."""
    from backend.models import model_router
    monkeypatch.setattr(model_router, "discover_installed_models", lambda force_refresh=False: [OLLAMA_SMALL_MODEL, CODING_MODEL])
    for var in ("AIFORGE_GENERAL_MODEL", "AIFORGE_CODING_MODEL", "AIFORGE_DEBUG_MODEL"):
        monkeypatch.delenv(var, raising=False)


def test_select_model_uses_small_default_for_simple_tasks(default_models):
    assert select_model("explanation", "explain this code") == OLLAMA_SMALL_MODEL
    assert select_model("resume", "improve my resume") == OLLAMA_SMALL_MODEL


def test_select_model_uses_medium_for_planning_and_architecture(default_models):
    assert select_model("planner", "build a full stack app") == OLLAMA_MEDIUM_MODEL
    # Architecture is produced by the coding model: it writes the folder layout, schema and API contracts.
    assert select_model("architect", "project architecture") == CODING_MODEL


def test_select_model_honours_env_override(default_models, monkeypatch):
    monkeypatch.setenv("AIFORGE_GENERAL_MODEL", CODING_MODEL)
    assert select_model("explanation", "explain this code") == CODING_MODEL


def test_fast_explanation_path_skips_planner_and_reviewer(monkeypatch):
    doubles = PipelineDoubles(monkeypatch)
    result = doubles.run("Explain previous code", session_id="fast-1")

    assert result.intent == "EXPLANATION"
    assert result.execution_strategy == "DIRECT"
    assert doubles.calls == ["fast_explanation"], "one model call, no planner, no reviewer"
    assert result.response.strip() == EXPLANATION


def test_resume_path_skips_planner_and_reviewer(monkeypatch):
    doubles = PipelineDoubles(monkeypatch)
    result = doubles.run("Generate Resume", session_id="fast-2")

    assert result.intent == "RESUME"
    assert "planner" not in doubles.calls and "reviewer" not in doubles.calls
    assert doubles.calls == ["resume"]
    assert result.response.strip() == RESUME.strip()


def test_full_coding_path_runs_reviewer_and_explanation(monkeypatch):
    doubles = PipelineDoubles(monkeypatch)
    result = doubles.run("Create Login API", session_id="full-1")

    assert result.intent == "PROJECT_GENERATION"
    # The full project workflow runs exactly once; it has its own planner/architect/reviewer stages.
    assert doubles.calls == ["project"]
    from backend.graph.parallel_workflow import parallel_graph
    nodes = set(parallel_graph.get_graph().nodes)
    assert {"planner", "architect", "reviewer", "testing", "documentation"} <= nodes
