from backend.graph import workflow


class DummyPlanner:
    def run(self, prompt):
        return f"PLAN:{prompt}"


class DummyArchitect:
    def run(self, plan):
        return """# Project Architecture

# Folder Structure

# Frontend Files

# Backend Files

# Database Schema

# API Routes

# Dependencies
"""


class DummyRouter:
    def route(self, prompt):
        value = prompt.lower()
        if "error" in value:
            return "debug"
        if "resume" in value or "cv" in value:
            return "resume"
        if "explain" in value or "what is" in value:
            return "explanation"
        return "coding"


class DummyAgent:
    def __init__(self, name):
        self.name = name

    def run(self, prompt):
        return f"{self.name}:{len(prompt)}"


def _mock_graph_agents():
    workflow.planner = DummyPlanner()
    workflow.architect = DummyArchitect()
    workflow.router = DummyRouter()
    workflow.coding = DummyAgent("coding")
    workflow.debug = DummyAgent("debug")
    workflow.resume = DummyAgent("resume")
    workflow.explanation = DummyAgent("explanation")


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


def test_enforce_architecture_sections_adds_quality_warning():
    architecture = "# Folder Structure\n# API Routes"
    enriched = workflow.enforce_architecture_sections(architecture)

    assert "Architecture Quality Check" in enriched
    assert "Status: Incomplete" in enriched
    assert "Project Architecture" in enriched
    assert "Database Schema" in enriched


def test_graph_routes_to_coding_for_general_prompt():
    _mock_graph_agents()
    result = workflow.graph.invoke({"prompt": "Build a todo app"})

    assert result["route"] == "coding"
    assert result["response"].startswith("coding:")


def test_graph_routes_to_debug_for_error_prompt():
    _mock_graph_agents()
    result = workflow.graph.invoke({"prompt": "Fix this error in API"})

    assert result["route"] == "debug"
    assert result["response"].startswith("debug:")


def test_graph_routes_to_resume_for_resume_prompt():
    _mock_graph_agents()
    result = workflow.graph.invoke({"prompt": "Improve my resume for backend roles"})

    assert result["route"] == "resume"
    assert result["response"].startswith("resume:")


def test_graph_routes_to_explanation_for_learning_prompt():
    _mock_graph_agents()
    result = workflow.graph.invoke({"prompt": "Explain what is MVC architecture"})

    assert result["route"] == "explanation"
    assert result["response"].startswith("explanation:")
