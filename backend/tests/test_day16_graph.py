import pytest
from backend.graph.state import WorkflowState
from backend.graph.nodes import (
    planner_node, architect_node, frontend_node,
    backend_node, database_node, reviewer_node,
    testing_node, documentation_node, export_node
)
from backend.graph.conditions import (
    should_retry_planner, should_refine_code, should_retry_reviewer
)
from backend.graph.executor import WorkflowExecutor


def test_workflow_state_initialization():
    """Test 1: WorkflowState dictionary schema structure."""
    state: WorkflowState = {
        "prompt": "Build Hospital Management System",
        "session_id": "test_session_16",
        "logs": [],
        "errors": []
    }
    assert state["prompt"] == "Build Hospital Management System"
    assert state["session_id"] == "test_session_16"


def test_planner_architect_nodes():
    """Test 2: PlannerNode and ArchitectNode state transformation."""
    state: WorkflowState = {
        "prompt": "Build Hospital Management System",
        "session_id": "test_session_16",
        "logs": [],
        "errors": []
    }

    s1 = planner_node(state)
    assert "plan" in s1
    assert any("[Planner] Completed" in log for log in s1["logs"])

    s2 = architect_node(s1)
    assert "architecture" in s2
    assert any("[Architect] Completed" in log for log in s2["logs"])


def test_coding_and_database_nodes():
    """Test 3: FrontendNode, BackendNode, and DatabaseNode state execution."""
    state: WorkflowState = {
        "prompt": "Hospital Management System",
        "session_id": "test_session_16",
        "architecture": {"components": ["PatientForm"], "routes": ["GET /api/patients"], "models": ["Patient"]},
        "logs": []
    }

    s1 = frontend_node(state)
    assert "frontend_code" in s1
    assert "src/App.jsx" in s1["frontend_code"]

    s2 = backend_node(s1)
    assert "backend_code" in s2
    assert "main.py" in s2["backend_code"]

    s3 = database_node(s2)
    assert "database_schema" in s3
    assert "CREATE TABLE" in s3["database_schema"]


def test_reviewer_testing_documentation_nodes():
    """Test 4: ReviewerNode, TestingNode, DocumentationNode, ExportNode pipeline."""
    state: WorkflowState = {
        "prompt": "Hospital Management System",
        "session_id": "test_session_16",
        "frontend_code": {"src/App.jsx": "export default function App() {}"},
        "backend_code": {"main.py": "app = FastAPI()"},
        "database_schema": "CREATE TABLE users ();",
        "logs": []
    }

    s1 = reviewer_node(state)
    assert s1["review"]["status"] == "APPROVED"

    s2 = testing_node(s1)
    assert "tests/test_api.py" in s2["tests"]

    s3 = documentation_node(s2)
    assert "# AIForge" in s3["documentation"]

    s4 = export_node(s3)
    assert s4["is_complete"] is True
    assert "README.md" in s4["project_files"]
    assert "frontend/src/App.jsx" in s4["project_files"]


def test_conditional_routing_logic():
    """Test 5: Routing conditions retry logic."""
    state: WorkflowState = {"retry_count": {}, "plan": None}
    r1 = should_retry_planner(state)
    assert r1 == "planner"
    assert state["retry_count"]["planner"] == 1

    state_rev: WorkflowState = {"retry_count": {}, "review": {"score": 50}}
    r2 = should_refine_code(state_rev)
    assert r2 == "frontend"

    state_test: WorkflowState = {"retry_count": {}, "tests": {}}
    r3 = should_retry_reviewer(state_test)
    assert r3 == "reviewer"


def test_end_to_end_workflow_execution():
    """Test 6: Full end-to-end autonomous LangGraph workflow execution."""
    executor = WorkflowExecutor()
    prompt = "Build a Hospital Management System with React, FastAPI, PostgreSQL, JWT, and Stripe"

    final_state = executor.execute_project_workflow(prompt, session_id="day16_test_session")

    assert final_state["is_complete"] is True
    assert len(final_state["project_files"]) >= 4
    assert any("Workflow Completed" in log for log in final_state["logs"])
