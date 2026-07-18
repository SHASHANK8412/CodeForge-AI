from backend.graph import workflow
from backend.services.llm import select_model
from backend.config import OLLAMA_SMALL_MODEL, OLLAMA_MEDIUM_MODEL


class DummyPlanner:
    def __init__(self):
        self.calls = 0

    def run(self, prompt, memory_context="", previous_output=""):
        self.calls += 1
        return f"PLAN::{prompt[:20]}"


class DummyArchitect:
    def __init__(self):
        self.calls = 0

    def run(self, plan, memory_context="", previous_output=""):
        self.calls += 1
        return """# Project Architecture
# Folder Structure
# Frontend Files
# Backend Files
# Database Schema
# API Routes
# Dependencies
"""


class DummyRouter:
    def __init__(self):
        self.calls = 0

    def route(self, prompt, memory_context=""):
        self.calls += 1
        text = prompt.lower()
        if "fix" in text or "bug" in text:
            return "debug"
        if "resume" in text:
            return "resume"
        if "explain" in text:
            return "explanation"
        return "coding"


class DummyMemoryManager:
    def build_context_block(self, session_id, prompt):
        return {
            "history_text": "recent: create login page",
            "project_text": "current project: aiforge",
            "relevant_text": "login flow",
        }

    def build_compact_memory_context(self, session_id, prompt):
        return "Recent History\n- create login page\nProject Snapshot\nAIForge\nRelevant Memory\nlogin flow"

    def save_interaction(self, **kwargs):
        self.last_saved = kwargs
        return kwargs


class CaptureAgent:
    def __init__(self, name):
        self.name = name
        self.calls = []

    def run(self, user_prompt, memory_context="", previous_output=""):
        self.calls.append(
            {
                "prompt": user_prompt,
                "memory_context": memory_context,
                "previous_output": previous_output,
            }
        )
        return f"{self.name.upper()}::{len(user_prompt)}"

    def process(self, user_prompt, memory_context="", previous_output=""):
        return self.run(user_prompt, memory_context, previous_output)



def configure_dummies():
    workflow.planner = DummyPlanner()
    workflow.architect = DummyArchitect()
    workflow.router = DummyRouter()
    workflow.coding = CaptureAgent("coding")
    workflow.debug = CaptureAgent("debug")
    workflow.resume = CaptureAgent("resume")
    workflow.explanation = CaptureAgent("explanation")
    workflow.reviewer = CaptureAgent("reviewer")
    workflow.testing_agent = CaptureAgent("testing")
    workflow.memory_manager = DummyMemoryManager()
    return workflow


def test_select_model_uses_small_default_for_simple_tasks():
    assert select_model("explanation", "explain this code") == OLLAMA_SMALL_MODEL
    assert select_model("resume", "improve my resume") == OLLAMA_SMALL_MODEL


def test_select_model_uses_medium_for_planning_and_architecture():
    assert select_model("planner", "build a full stack app") == OLLAMA_MEDIUM_MODEL
    assert select_model("architect", "project architecture") == OLLAMA_MEDIUM_MODEL


def test_fast_explanation_path_skips_planner_and_reviewer():
    wf = configure_dummies()
    result = wf.graph.invoke({"prompt": "Explain previous code", "session_id": "fast-1"})

    assert result["route"] == "explanation"
    assert wf.planner.calls == 0
    assert len(wf.reviewer.calls) == 0
    assert len(wf.explanation.calls) == 1
    assert result["response"].startswith("EXPLANATION::")


def test_resume_path_skips_planner_and_reviewer():
    wf = configure_dummies()
    wf.memory_manager.format_compact_context = lambda context: ""
    result = wf.graph.invoke({"prompt": "Generate Resume", "session_id": "fast-2"})

    assert result["route"] == "resume"
    assert wf.planner.calls == 0
    assert len(wf.reviewer.calls) == 0
    assert len(wf.resume.calls) == 1
    assert result["response"].startswith("RESUME::")


def test_full_coding_path_runs_reviewer_and_explanation():
    wf = configure_dummies()
    result = wf.graph.invoke({"prompt": "Create Login API", "session_id": "full-1"})

    assert result["route"] == "coding"
    assert wf.planner.calls == 1
    assert len(wf.reviewer.calls) == 1
    assert len(wf.explanation.calls) == 1
    assert result["response"].startswith("EXPLANATION::")
