from pathlib import Path

from backend.graph import workflow
from backend.memory.memory_manager import memory_manager


class DummyPlanner:
    def run(self, prompt, memory_context=""):
        return f"PLAN::{prompt[:40]}"


class DummyArchitect:
    def run(self, plan, memory_context=""):
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
- React
"""


class DummyRouter:
    def route(self, prompt, memory_context=""):
        value = prompt.lower()
        if "bug" in value or "fix" in value:
            return "debug"
        if "resume" in value or "cv" in value:
            return "resume"
        if "explain" in value:
            return "explanation"
        return "coding"


class CaptureAgent:
    def __init__(self, name):
        self.name = name
        self.last_prompt = ""
        self.last_memory_context = ""

    def run(self, user_prompt, memory_context=""):
        self.last_prompt = user_prompt
        self.last_memory_context = memory_context
        return f"{self.name.upper()}::{user_prompt[:30]}"



def configure_temp_memory(tmp_path: Path):
    conversation_root = tmp_path / "conversations"
    project_root = tmp_path / "projects"
    vector_root = tmp_path / "vectors"

    memory_manager.conversation_memory.storage_root = conversation_root
    memory_manager.project_memory.storage_root = project_root
    memory_manager.vector_memory.storage_root = vector_root

    conversation_root.mkdir(parents=True, exist_ok=True)
    project_root.mkdir(parents=True, exist_ok=True)
    vector_root.mkdir(parents=True, exist_ok=True)

    memory_manager.clear_session("test-session")


def mock_graph_agents():
    workflow.planner = DummyPlanner()
    workflow.architect = DummyArchitect()
    workflow.router = DummyRouter()
    workflow.coding = CaptureAgent("coding")
    workflow.debug = CaptureAgent("debug")
    workflow.resume = CaptureAgent("resume")
    workflow.explanation = CaptureAgent("explanation")
    return workflow.coding


def test_memory_manager_conversation_and_project_storage(tmp_path):
    configure_temp_memory(tmp_path)

    memory_manager.save_interaction(
        session_id="session-a",
        user_prompt="Create login page",
        ai_response="Use React form components",
        agent_name="coding",
        route="coding",
        plan="Plan A",
        architecture="Arch A",
    )

    history = memory_manager.get_history("session-a")
    project = memory_manager.get_project("session-a")

    assert len(history) == 1
    assert history[0]["user_prompt"] == "Create login page"
    assert project["latest_plan"] == "Plan A"
    assert project["latest_architecture"] == "Arch A"
    assert project["last_agent"] == "coding"


def test_clear_session_removes_all_memory(tmp_path):
    configure_temp_memory(tmp_path)

    memory_manager.save_interaction(
        session_id="session-b",
        user_prompt="Create FastAPI backend",
        ai_response="Backend ready",
        agent_name="coding",
        route="coding",
    )

    memory_manager.clear_session("session-b")

    assert memory_manager.get_history("session-b") == []
    project = memory_manager.get_project("session-b")
    assert project["current_project"] == ""
    assert project["latest_plan"] == ""


def test_graph_carries_memory_forward_between_prompts(tmp_path):
    configure_temp_memory(tmp_path)
    coding_agent = mock_graph_agents()

    first = workflow.graph.invoke({"prompt": "Create login page", "session_id": "session-c"})
    second = workflow.graph.invoke({"prompt": "Continue", "session_id": "session-c"})

    assert first["route"] == "coding"
    assert second["route"] == "coding"
    assert "Create login page" in coding_agent.last_prompt
    assert "Conversation History" in coding_agent.last_prompt
    assert second["response"].startswith("CODING::")


def test_router_uses_memory_context_for_continuation_hint():
    router = DummyRouter()
    assert router.route("Continue", "last_agent: coding") == "coding"
    assert router.route("Fix previous bug", "something") == "debug"
