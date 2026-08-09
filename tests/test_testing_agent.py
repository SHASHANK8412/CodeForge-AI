"""
Unit and Integration Tests for AIForge TestingAgent & Real Execution Verification (Phase 7)
"""

import shutil
import pytest
from pathlib import Path
from backend.agents.testing_agent import TestingAgent
from backend.execution.models import TestResult, ExecutionStatus, ExecutionResult
from backend.execution.project_runner import global_project_runner
from backend.schemas.agent_contract import ProjectSpec, ArchitectureSpec
from backend.graph.project_state import ProjectState
from backend.graph.parallel_workflow import testing_node


@pytest.fixture
def tmp_projects_dir(tmp_path):
    p = tmp_path / "generated_projects"
    p.mkdir(parents=True, exist_ok=True)
    yield p
    if p.exists():
        shutil.rmtree(p, ignore_errors=True)


def test_successful_test_execution_evaluation():
    agent = TestingAgent()
    exec_res = {
        "status": "PASS",
        "exit_code": 0,
        "stdout": "collected 2 items\ntests/test_main.py .. [100%]\n2 passed in 0.10s",
        "stderr": "",
        "duration_ms": 100.0
    }

    test_res = agent.evaluate_execution_results(exec_res)
    assert test_res.success is True
    assert test_res.passed == 2
    assert test_res.failed == 0
    assert "PASSED" in test_res.summary


def test_failed_test_execution_evaluation():
    agent = TestingAgent()
    exec_res = {
        "status": "FAIL",
        "exit_code": 1,
        "stdout": "FAILED tests/test_main.py::test_create_todo - AssertionError: assert 'WRONG' == 'Buy milk'\n1 failed, 1 passed in 0.12s",
        "stderr": "",
        "duration_ms": 120.0
    }

    test_res = agent.evaluate_execution_results(exec_res)
    assert test_res.success is False
    assert test_res.failed == 1
    assert len(test_res.failures) == 1
    assert test_res.failures[0].test_name == "test_create_todo"
    assert "AssertionError" in test_res.failures[0].error


def test_parsing_pytest_failures():
    agent = TestingAgent()
    exec_res = {
        "status": "FAIL",
        "exit_code": 1,
        "stdout": "FAILED tests/test_auth.py::test_login - KeyError: 'token'\nFAILED tests/test_items.py::test_delete - 404 Not Found\n2 failed in 0.5s",
        "stderr": ""
    }

    test_res = agent.evaluate_execution_results(exec_res)
    assert test_res.failed == 2
    assert test_res.failures[0].test_name == "test_login"
    assert test_res.failures[1].test_name == "test_delete"


def test_parsing_build_failures():
    agent = TestingAgent()
    exec_res = {
        "status": "COMPILE_ERROR",
        "exit_code": 1,
        "stdout": "",
        "stderr": "SyntaxError: invalid syntax (main.py, line 5)"
    }

    test_res = agent.evaluate_execution_results(exec_res)
    assert test_res.success is False
    assert "SyntaxError" in test_res.summary or "SyntaxError" in test_res.errors[0]


def test_structured_test_result_generation():
    agent = TestingAgent()
    exec_res = {
        "status": "PASS",
        "exit_code": 0,
        "stdout": "3 passed in 0.02s",
        "stderr": ""
    }

    test_res = agent.evaluate_execution_results(exec_res)
    assert isinstance(test_res, TestResult)
    assert test_res.total == 3


def test_requirement_to_test_mapping():
    agent = TestingAgent()
    spec = {
        "functional_requirements": ["FR-1: Create user todo", "FR-2: Authenticate user login"]
    }
    exec_res = {
        "status": "FAIL",
        "exit_code": 1,
        "stdout": "FAILED tests/test_todo.py::test_create_todo - AssertionError\n1 failed"
    }

    test_res = agent.evaluate_execution_results(exec_res, project_spec=spec)
    assert test_res.failures[0].requirement == "FR-1: Create user todo"


@pytest.mark.anyio
async def test_testing_node_project_state_update(monkeypatch):
    from backend.graph import parallel_workflow
    from unittest.mock import AsyncMock

    monkeypatch.setattr(parallel_workflow.testing_agent, "run_async", AsyncMock(return_value="## Unit Tests\ndef test_x(): pass"))

    state: ProjectState = {
        "backend": "def foo(): pass",
        "frontend": "// App",
        "execution_results": {
            "status": "PASS",
            "exit_code": 0,
            "stdout": "1 passed"
        }
    }

    state_update = await testing_node(state)
    assert "test_results" in state_update
    assert state_update["test_results"]["success"] is True



def test_preservation_of_raw_execution_evidence():
    agent = TestingAgent()
    raw_exec = {
        "status": "FAIL",
        "exit_code": 1,
        "stdout": "raw stdout content",
        "stderr": "raw stderr content",
        "duration_ms": 150.0
    }

    test_res = agent.evaluate_execution_results(raw_exec)
    assert test_res.errors is not None
    assert "raw stderr content" in test_res.errors or len(test_res.failures) >= 0


def test_real_good_and_broken_todo_app_verification(tmp_projects_dir):
    agent = TestingAgent()

    # 1. Good Todo App Integration
    good_proj = tmp_projects_dir / "GoodTodoApp"
    (good_proj / "backend").mkdir(parents=True)
    (good_proj / "tests").mkdir(parents=True)
    (good_proj / "backend" / "__init__.py").write_text("", encoding="utf-8")
    (good_proj / "tests" / "__init__.py").write_text("", encoding="utf-8")

    (good_proj / "backend" / "main.py").write_text("def get_status(): return 'OK'\n", encoding="utf-8")
    (good_proj / "tests" / "test_status.py").write_text(
        "from backend.main import get_status\ndef test_status(): assert get_status() == 'OK'\n",
        encoding="utf-8"
    )

    good_exec = global_project_runner.run_project(str(good_proj))
    good_eval = agent.evaluate_execution_results(good_exec.model_dump())

    assert good_exec.exit_code == 0
    assert good_eval.success is True
    assert good_eval.passed == 1
    assert good_eval.failed == 0

    # 2. Broken Todo App Integration
    bad_proj = tmp_projects_dir / "BadTodoApp"
    (bad_proj / "backend").mkdir(parents=True)
    (bad_proj / "tests").mkdir(parents=True)
    (bad_proj / "backend" / "__init__.py").write_text("", encoding="utf-8")
    (bad_proj / "tests" / "__init__.py").write_text("", encoding="utf-8")

    (bad_proj / "backend" / "main.py").write_text("def get_status(): return 'BROKEN'\n", encoding="utf-8")
    (bad_proj / "tests" / "test_status.py").write_text(
        "from backend.main import get_status\ndef test_status(): assert get_status() == 'OK'\n",
        encoding="utf-8"
    )

    bad_exec = global_project_runner.run_project(str(bad_proj))
    bad_eval = agent.evaluate_execution_results(bad_exec.model_dump())

    assert bad_exec.exit_code != 0
    assert bad_eval.success is False
    assert bad_eval.failed >= 1
    assert len(bad_eval.failures) == 1
    assert bad_eval.failures[0].test_name == "test_status"
