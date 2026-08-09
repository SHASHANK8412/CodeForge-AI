"""
Unit and Real Integration Tests for AIForge DebugAgent & DebugResult (Phase 8)
"""

import shutil
import pytest
from pathlib import Path
from backend.agents.debug_agent import DebugAgent, global_debug_agent
from backend.agents.testing_agent import TestingAgent
from backend.execution.models import DebugResult, TestResult, TestFailureDetail
from backend.execution.project_runner import global_project_runner
from backend.graph.project_state import ProjectState


@pytest.fixture
def tmp_projects_dir(tmp_path):
    p = tmp_path / "generated_projects"
    p.mkdir(parents=True, exist_ok=True)
    yield p
    if p.exists():
        shutil.rmtree(p, ignore_errors=True)


def test_debugging_syntax_error():
    agent = DebugAgent()
    state: ProjectState = {
        "execution_results": {
            "status": "FAIL",
            "exit_code": 1,
            "stderr": 'File "backend/main.py", line 5\n    def broken_syntax(:\n                      ^\nSyntaxError: invalid syntax'
        },
        "files": {
            "backend/main.py": "def broken_syntax(:\n    pass"
        }
    }

    diag = agent.diagnose_and_repair(state)
    assert diag.error_type == "SYNTAX_ERROR"
    assert "backend/main.py" in diag.files_to_modify


def test_debugging_import_error():
    agent = DebugAgent()
    state: ProjectState = {
        "execution_results": {
            "status": "FAIL",
            "exit_code": 1,
            "stderr": "ModuleNotFoundError: No module named 'nonexistent_pkg'"
        }
    }

    diag = agent.diagnose_and_repair(state)
    assert diag.error_type == "IMPORT_ERROR"
    assert "nonexistent_pkg" in diag.diagnosis


def test_debugging_failing_pytest_assertion():
    agent = DebugAgent()
    state: ProjectState = {
        "test_results": {
            "success": False,
            "failures": [
                {
                    "test_name": "test_create_todo",
                    "error": "AssertionError: assert 'WRONG' == 'OK'",
                    "file": "tests/test_todo.py"
                }
            ]
        },
        "files": {
            "backend/todos.py": "def create(): return {'status': 'WRONG'}"
        }
    }

    diag = agent.diagnose_and_repair(state)
    assert diag.error_type == "ASSERTION_FAILURE"
    assert "test_create_todo" in diag.diagnosis
    assert len(diag.files_to_modify) > 0


def test_debugging_api_failure():
    agent = DebugAgent()
    state: ProjectState = {
        "test_results": {
            "success": False,
            "failures": [
                {
                    "test_name": "test_login",
                    "error": "HTTP status 500 Internal Server Error",
                    "file": "tests/test_api.py"
                }
            ]
        },
        "files": {
            "backend/main.py": "def login(): raise Exception('DB down')"
        }
    }

    diag = agent.diagnose_and_repair(state)
    assert diag.error_type == "ASSERTION_FAILURE"
    assert "backend/main.py" in diag.files_to_modify


def test_debugging_database_model_mismatch():
    agent = DebugAgent()
    state: ProjectState = {
        "test_results": {
            "success": False,
            "failures": [
                {
                    "test_name": "test_db_user",
                    "error": "KeyError: 'role'",
                    "file": "tests/test_db.py"
                }
            ]
        },
        "files": {
            "backend/models.py": "class User: name = ''"
        }
    }

    diag = agent.diagnose_and_repair(state)
    assert diag.error_type == "ASSERTION_FAILURE"


def test_correct_root_cause_extraction():
    agent = DebugAgent()
    state: ProjectState = {
        "execution_results": {
            "status": "FAIL",
            "exit_code": 1,
            "stderr": "TypeError: unsupported operand type(s) for +: 'int' and 'str'"
        }
    }

    diag = agent.diagnose_and_repair(state)
    assert diag.success is True
    assert diag.root_cause != ""


def test_correct_file_identification():
    agent = DebugAgent()
    state: ProjectState = {
        "test_results": {
            "success": False,
            "failures": [{"test_name": "test_auth", "error": "Auth failed", "file": "tests/test_auth.py"}]
        },
        "files": {
            "backend/auth.py": "# auth logic"
        }
    }

    diag = agent.diagnose_and_repair(state)
    assert "backend/auth.py" in diag.files_to_modify


def test_structured_debug_result_generation():
    agent = DebugAgent()
    diag = agent.diagnose_and_repair({})
    assert isinstance(diag, DebugResult)
    assert diag.success is True
    assert diag.error_type == "NONE"


def test_previous_fix_awareness():
    agent = DebugAgent()
    state: ProjectState = {
        "test_results": {
            "success": False,
            "failures": [{"test_name": "test_foo", "error": "err", "file": "tests/test_foo.py"}]
        },
        "files": {"backend/foo.py": "def foo(): pass"},
        "fixes": [{"files_to_modify": ["backend/foo.py"], "explanation": "attempt 1"}]
    }

    diag = agent.diagnose_and_repair(state)
    assert isinstance(diag, DebugResult)


def test_path_traversal_rejection(tmp_projects_dir):
    agent = DebugAgent()
    state: ProjectState = {
        "project_path": str(tmp_projects_dir / "SafeApp"),
        "test_results": {
            "success": False,
            "failures": [{"test_name": "test_hack", "error": "err", "file": "../../outside.py"}]
        },
        "files": {"../../outside.py": "malicious"}
    }

    diag = agent.diagnose_and_repair(state)
    assert "../../outside.py" not in diag.files_to_modify


def test_good_project_no_fix_needed():
    agent = DebugAgent()
    state: ProjectState = {
        "execution_results": {"status": "PASS", "exit_code": 0},
        "test_results": {"success": True, "passed": 5, "failed": 0}
    }

    diag = agent.diagnose_and_repair(state)
    assert diag.error_type == "NONE"
    assert len(diag.files_to_modify) == 0
    assert len(diag.changes) == 0


def test_broken_todo_app_targeted_repair(tmp_projects_dir):
    # 1. Setup real BrokenTodoApp on disk
    broken_proj = tmp_projects_dir / "BrokenTodoApp"
    (broken_proj / "backend").mkdir(parents=True)
    (broken_proj / "tests").mkdir(parents=True)
    (broken_proj / "backend" / "__init__.py").write_text("", encoding="utf-8")
    (broken_proj / "tests" / "__init__.py").write_text("", encoding="utf-8")

    backend_code = "def get_status():\n    return {'status': 'WRONG'}\n"
    test_code = "from backend.main import get_status\ndef test_status():\n    assert get_status()['status'] == 'OK'\n"

    (broken_proj / "backend" / "main.py").write_text(backend_code, encoding="utf-8")
    (broken_proj / "tests" / "test_status.py").write_text(test_code, encoding="utf-8")

    # 2. Run ProjectRunner + TestingAgent to produce real failure evidence
    exec_res = global_project_runner.run_project(str(broken_proj))
    testing_agent = TestingAgent()
    test_res = testing_agent.evaluate_execution_results(exec_res.model_dump())

    assert exec_res.exit_code != 0
    assert test_res.success is False

    # 3. Diagnose using DebugAgent
    state: ProjectState = {
        "project_path": str(broken_proj),
        "execution_results": exec_res.model_dump(),
        "test_results": test_res.model_dump(),
        "files": {
            "backend/main.py": backend_code,
            "tests/test_status.py": test_code
        }
    }

    debug_res = global_debug_agent.diagnose_and_repair(state)

    assert debug_res.success is True
    assert debug_res.error_type == "ASSERTION_FAILURE"
    assert "backend/main.py" in debug_res.files_to_modify
    assert "backend/main.py" in debug_res.changes
    assert "'OK'" in debug_res.changes["backend/main.py"]
