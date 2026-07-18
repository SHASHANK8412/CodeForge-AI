from backend.graph import workflow


class DummyPlanner:
    def run(self, prompt, memory_context="", previous_output=""):
        return f"PLAN::{prompt[:30]}"


class DummyArchitect:
    def run(self, plan, memory_context="", previous_output=""):
        return """# Project Architecture

# Folder Structure
- backend/
- frontend/

# Frontend Files
- src/App.jsx

# Backend Files
- main.py

# Database Schema
- users

# API Routes
- /chat

# Dependencies
- FastAPI
"""


class DummyRouter:
    def route(self, prompt, memory_context=""):
        text = prompt.lower()
        if "fix" in text or "bug" in text:
            return "debug"
        if "resume" in text:
            return "resume"
        if "explain" in text:
            return "explanation"
        return "coding"


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


class DummyMemoryManager:
    def build_context_block(self, session_id, prompt):
        return {
            "history_text": "previous prompt: Create login page",
            "project_text": "Current Project: AIForge",
            "relevant_text": "login flow remembered",
        }

    def build_planner_prompt(self, prompt, session_id):
        return f"Planner Prompt::{prompt}::{session_id}"

    def save_interaction(self, **kwargs):
        self.last_saved = kwargs
        return kwargs


def test_validate_architecture_sections_complete():
    architecture = """# Project Architecture
# Folder Structure
# Frontend Files
# Backend Files
# Database Schema
# API Routes
# Dependencies
"""
    is_complete, missing = workflow.validate_architecture_sections(architecture)
    assert is_complete is True
    assert missing == []


def test_graph_coding_path_runs_reviewer_then_explanation():
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

    result = workflow.graph.invoke({"prompt": "Create Login API", "session_id": "s1"})

    assert result["route"] == "coding"
    assert workflow.coding.calls
    assert workflow.reviewer.calls
    assert workflow.explanation.calls
    assert result["response"].startswith("EXPLANATION::")


def test_graph_explanation_path_skips_reviewer():
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

    result = workflow.graph.invoke({"prompt": "Explain previous code", "session_id": "s2"})

    assert result["route"] == "explanation"
    assert not workflow.reviewer.calls
    assert workflow.explanation.calls
    assert result["response"].startswith("EXPLANATION::")


def test_graph_debug_path_runs_reviewer_then_explanation():
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

    result = workflow.graph.invoke({"prompt": "Fix previous bug", "session_id": "s3"})

    assert result["route"] == "debug"
    assert workflow.debug.calls
    assert workflow.reviewer.calls
    assert workflow.explanation.calls


def test_graph_resume_path_routes_to_explanation_only():
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

    result = workflow.graph.invoke({"prompt": "Generate Resume", "session_id": "s4"})

    assert result["route"] == "resume"
    assert workflow.resume.calls
    assert workflow.explanation.calls
    assert not workflow.reviewer.calls
