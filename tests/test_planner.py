"""
Day 42 - Root Test Suite Wrapper for Architecture Planning
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.agents.planner_agent import PlannerAgent
from backend.schemas.agent_contract import ProjectSpec


def test_planner_valid_json_parsing():
    agent = PlannerAgent()
    raw_output = """
## 1. Executive Summary
Build a Todo application.

```json
{
  "project_name": "TodoManager",
  "domain": "Productivity",
  "executive_summary": "A modern task tracking application.",
  "functional_requirements": ["FR-1: Create Task", "FR-2: Complete Task"],
  "non_functional_requirements": ["Response < 100ms"],
  "user_stories": ["As a user I want to add tasks"],
  "assumptions": ["Single user mode"],
  "constraints": ["FastAPI backend"],
  "tech_stack": {"frontend": "React", "backend": "FastAPI", "database": "PostgreSQL"}
}
```
"""
    plan = agent.parse_plan_json(raw_output)

    assert plan["project_name"] == "TodoManager"
    assert plan["domain"] == "Productivity"
    assert len(plan["functional_requirements"]) == 2
    assert plan["frontend"] == "React"
    assert plan["backend"] == "FastAPI"
    assert plan["database"] == "PostgreSQL"


import pytest
from unittest.mock import AsyncMock
from backend.graph.project_state import ProjectState
from backend.graph.project_workflow import planner_node


def test_planner_malformed_json_raises_error():
    agent = PlannerAgent()
    raw_output = "Here is a broken output with unclosed JSON { 'project_name': 'Broken"
    with pytest.raises(ValueError, match="Planner output"):
        agent.parse_plan_json(raw_output, allow_fallback=False)



def test_planner_malformed_json_explicit_fallback():
    agent = PlannerAgent()
    raw_output = "Here is a broken output with unclosed JSON { 'project_name': 'Broken"
    plan = agent.parse_plan_json(raw_output, allow_fallback=True)

    assert plan["project_name"] == "AIForge Application"
    assert plan["frontend"] == "React"
    assert plan["backend"] == "FastAPI"
    assert isinstance(plan["functional_requirements"], list)


@pytest.mark.anyio
async def test_planner_node_project_state_integration():
    from backend.graph import project_workflow
    
    mock_llm_json = """
```json
{
  "project_name": "TodoApp",
  "domain": "Productivity",
  "executive_summary": "A Todo management application with authentication and CRUD.",
  "functional_requirements": ["FR-1: Auth", "FR-2: CRUD Operations"],
  "tech_stack": {"frontend": "React", "backend": "FastAPI", "database": "PostgreSQL"}
}
```
"""
    project_workflow.planner.run_async = AsyncMock(return_value=mock_llm_json)

    initial_state: ProjectState = {
        "prompt": "Build a Todo application with authentication and CRUD operations.",
        "user_prompt": "Build a Todo application with authentication and CRUD operations."
    }

    state_update = await planner_node(initial_state)

    assert state_update.get("project_name") == "TodoApp"
    assert len(state_update.get("requirements", [])) == 2
    assert "FR-1: Auth" in state_update.get("requirements", [])
    assert isinstance(state_update.get("project_spec"), dict)
    assert state_update["project_spec"]["frontend"] == "React"
    assert state_update.get("plan") is not None
    assert state_update["plan"]["project_name"] == "TodoApp"


if __name__ == "__main__":
    from tests.verify_day42_planner import main as run_day42_tests
    success = run_day42_tests()
    if not success:
        sys.exit(1)
    sys.exit(0)


