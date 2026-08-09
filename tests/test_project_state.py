"""
Unit tests for AIForge ProjectState structure and reducer functions
"""

import pytest
from backend.graph.project_state import (
    ProjectState,
    _merge_errors,
    _merge_current_step,
    _merge_stream_events
)


def test_project_state_fields():
    state: ProjectState = {
        "user_request": "Build a Todo application",
        "project_name": "TodoApp",
        "requirements": ["Auth", "CRUD"],
        "project_spec": {"framework": "FastAPI"},
        "architecture": {"style": "Modular Monolith"},
        "files": {"backend/main.py": "from fastapi import FastAPI\napp = FastAPI()"},
        "dependencies": ["fastapi", "uvicorn"],
        "commands": ["pytest"],
        "test_results": {"success": True},
        "errors_list": [],
        "fixes": [],
        "iteration": 1,
        "max_iterations": 3,
        "status": "RUNNING",
        "project_path": "generated_projects/TodoApp"
    }

    assert state["project_name"] == "TodoApp"
    assert len(state["requirements"]) == 2
    assert "backend/main.py" in state["files"]
    assert state["iteration"] == 1
    assert state["max_iterations"] == 3


def test_state_merge_helpers():
    assert _merge_errors("err1", "err2") == "err1\nerr2"
    assert _merge_errors("", "err2") == "err2"
    assert _merge_current_step("step1", "step2") == "step2"
    assert _merge_stream_events(["evt1"], ["evt2"]) == ["evt1", "evt2"]


def test_project_state_backward_compatibility():
    # Verify all legacy fields are still valid keys on ProjectState TypedDict
    state: ProjectState = {
        "prompt": "Test Prompt",
        "user_prompt": "Test User Prompt",
        "plan": {"test": 1},
        "architecture": {"test": 2},
        "frontend": "code",
        "backend": "code",
        "database": "sql",
        "documentation": "md",
        "tests": "py",
        "review": {"score": 90},
        "github": {"url": "http"},
        "assembly_manifest": {"manifest": {}},
        "duplicate_report": {"duplicates": []},
        "current_step": "planner",
        "error": "none",
        "stream_events": ["event1"],
        "cached_nodes": ["planner"],
        "validation_status": {"valid": True},
        "project_path": "/tmp/test",
        "review_findings": [],
        "test_results": {"pass": True},
        "quality_score": {"overall": 95},
        "quality_report": "good",
        "self_heal_attempts": 0,
        "validation_report": {},
        "reflection_report": {},
        "deployment_files": {},
        "deployment_report": {},
        "deployment_platform": "docker",
        "deployment_guide": "guide"
    }

    assert state["prompt"] == "Test Prompt"
    assert state["self_heal_attempts"] == 0
    assert state["deployment_platform"] == "docker"

