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

    def run(self, prompt, *args, **kwargs):
        return f"{self.name}:{len(prompt)}"


class DummyTestingAgent:
    def process(self, code, *args, **kwargs):
        return f"testing:{len(code)}"


class DummyMemoryManager:
    def build_context_block(self, session_id, prompt):
        return {
            "history_text": "",
            "project_text": "",
            "relevant_text": "",
        }
    def build_planner_prompt(self, prompt, session_id):
        return prompt
    def save_interaction(self, **kwargs):
        return kwargs


def _mock_graph_agents():
    workflow.planner = DummyPlanner()
    workflow.architect = DummyArchitect()
    workflow.router = DummyRouter()
    workflow.coding = DummyAgent("coding")
    workflow.debug = DummyAgent("debug")
    workflow.resume = DummyAgent("resume")
    workflow.explanation = DummyAgent("explanation")
    workflow.reviewer = DummyAgent("reviewer")
    workflow.testing_agent = DummyTestingAgent()
    workflow.memory_manager = DummyMemoryManager()


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


def test_graph_routes_to_coding_for_general_prompt():
    _mock_graph_agents()
    result = workflow.graph.invoke({"prompt": "Build a todo app"})

    assert result["route"] == "coding"
    assert result["generated_code"].startswith("coding:")
    assert result["response"].startswith("explanation:")


def test_graph_routes_to_debug_for_error_prompt():
    _mock_graph_agents()
    result = workflow.graph.invoke({"prompt": "Fix this error in API"})

    assert result["route"] == "debug"
    assert result["generated_code"].startswith("debug:")
    assert result["response"].startswith("explanation:")


def test_graph_routes_to_resume_for_resume_prompt():
    _mock_graph_agents()
    result = workflow.graph.invoke({"prompt": "Improve my resume for backend roles"})

    assert result["route"] == "resume"
    assert result["generated_code"].startswith("resume:")
    assert result["response"].startswith("explanation:")


def test_graph_routes_to_explanation_for_learning_prompt():
    _mock_graph_agents()
    result = workflow.graph.invoke({"prompt": "Explain what is MVC architecture"})

    assert result["route"] == "explanation"
    assert result["response"].startswith("explanation:")
