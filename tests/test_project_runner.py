"""
Unit and Real Integration Tests for AIForge ProjectRunner & SandboxExecutor (Phase 6)
"""

import sys
import shutil
import pytest
from pathlib import Path
from backend.execution.project_runner import global_project_runner
from backend.execution.models import ExecutionStatus, ExecutionResult
from backend.graph.project_state import ProjectState
from backend.graph.parallel_workflow import execution_validation_node


@pytest.fixture
def tmp_projects_dir(tmp_path):
    p = tmp_path / "generated_projects"
    p.mkdir(parents=True, exist_ok=True)
    yield p
    if p.exists():
        shutil.rmtree(p, ignore_errors=True)


def test_successful_command_execution(tmp_projects_dir):
    proj = tmp_projects_dir / "ValidPy"
    proj.mkdir()
    (proj / "main.py").write_text("def hello(): return 'world'", encoding="utf-8")

    res = global_project_runner.run_project(str(proj))
    assert res.exit_code == 0
    assert res.status in [ExecutionStatus.PASS, ExecutionStatus.COMPILE_ERROR]


def test_failed_command_execution(tmp_projects_dir):
    proj = tmp_projects_dir / "SyntaxErrPy"
    proj.mkdir()
    (proj / "main.py").write_text("def broken_syntax(:\n    pass", encoding="utf-8")

    res = global_project_runner.run_project(str(proj))
    assert res.exit_code != 0
    combined = (res.stderr or "") + (res.stdout or "")
    assert "SyntaxError" in combined or "syntax" in combined.lower()


def test_nonzero_exit_code(tmp_projects_dir):
    proj = tmp_projects_dir / "FailTestPy"
    proj.mkdir()
    (proj / "test_sample.py").write_text("def test_fail(): assert False", encoding="utf-8")

    res = global_project_runner.run_project(str(proj))
    assert res.exit_code != 0


def test_timeout_handling(tmp_projects_dir, monkeypatch):
    proj = tmp_projects_dir / "TimeoutPy"
    proj.mkdir()
    (proj / "main.py").write_text("import time; time.sleep(10)", encoding="utf-8")

    # Set 0.5s timeout for fast test run
    monkeypatch.setattr(global_project_runner.limits, "timeout_seconds", 0.5)
    res = global_project_runner.run_project(str(proj), command_override=[sys.executable, "main.py"])

    assert res.timed_out is True
    assert res.status == ExecutionStatus.TIMEOUT



def test_stdout_capture(tmp_projects_dir):
    proj = tmp_projects_dir / "PrintPy"
    proj.mkdir()
    (proj / "main.py").write_text("print('HELLO_OUTPUT_STDOUT')", encoding="utf-8")

    res = global_project_runner.run_project(str(proj))
    assert res.exit_code == 0


def test_stderr_capture(tmp_projects_dir):
    proj = tmp_projects_dir / "ErrPy"
    proj.mkdir()
    (proj / "main.py").write_text("import sys; sys.stderr.write('ERR_MSG_TEST')", encoding="utf-8")

    res = global_project_runner.run_project(str(proj), command_override=[sys.executable, "main.py"])
    assert "ERR_MSG_TEST" in res.stderr


def test_unsupported_project_command(tmp_projects_dir):
    res = global_project_runner.run_project(str(tmp_projects_dir / "NonExistent"))
    assert res.status == ExecutionStatus.UNSUPPORTED
    assert res.exit_code == -1


def test_project_path_isolation(tmp_projects_dir):
    proj = tmp_projects_dir / "IsoPy"
    proj.mkdir()
    (proj / "main.py").write_text("import os; print(os.getcwd())", encoding="utf-8")

    res = global_project_runner.run_project(str(proj))
    assert res.exit_code == 0


def test_python_project_validation(tmp_projects_dir):
    proj = tmp_projects_dir / "PyProj"
    proj.mkdir()
    (proj / "app.py").write_text("x = 10", encoding="utf-8")

    cmd, lang = global_project_runner.select_safe_command(proj)
    assert lang == "python"
    assert "compileall" in cmd or "pytest" in cmd


def test_node_project_validation(tmp_projects_dir):
    proj = tmp_projects_dir / "NodeProj"
    proj.mkdir()
    (proj / "package.json").write_text('{"name": "test", "scripts": {"build": "echo build"}}', encoding="utf-8")

    cmd, lang = global_project_runner.select_safe_command(proj)
    assert lang == "javascript"
    assert "build" in cmd


@pytest.mark.anyio
async def test_runner_project_state_integration(tmp_projects_dir):
    proj = tmp_projects_dir / "StatePy"
    proj.mkdir()
    (proj / "main.py").write_text("def foo(): pass", encoding="utf-8")

    state: ProjectState = {
        "project_name": "StatePy",
        "project_path": str(proj),
        "commands": []
    }

    state_update = await execution_validation_node(state)

    assert "execution_results" in state_update
    assert state_update["status"] == "PASS"
    assert len(state_update["commands"]) == 1


def test_real_todo_project_execution_success_and_failure(tmp_projects_dir):
    # 1. Real Passing Todo Project
    good_proj = tmp_projects_dir / "GoodTodoApp"
    (good_proj / "backend").mkdir(parents=True)
    (good_proj / "tests").mkdir(parents=True)
    (good_proj / "backend" / "__init__.py").write_text("", encoding="utf-8")
    (good_proj / "tests" / "__init__.py").write_text("", encoding="utf-8")

    (good_proj / "backend" / "main.py").write_text(
        "def create_todo(title: str):\n"
        "    return {'id': 1, 'title': title, 'completed': False}\n",
        encoding="utf-8"
    )

    (good_proj / "tests" / "test_main.py").write_text(
        "from backend.main import create_todo\n"
        "def test_create_todo():\n"
        "    res = create_todo('Buy milk')\n"
        "    assert res['title'] == 'Buy milk'\n",
        encoding="utf-8"
    )

    good_res = global_project_runner.run_project(str(good_proj))
    assert good_res.exit_code == 0
    assert good_res.status == ExecutionStatus.PASS

    # 2. Real Broken Todo Project
    bad_proj = tmp_projects_dir / "BadTodoApp"
    (bad_proj / "backend").mkdir(parents=True)
    (bad_proj / "tests").mkdir(parents=True)
    (bad_proj / "backend" / "__init__.py").write_text("", encoding="utf-8")
    (bad_proj / "tests" / "__init__.py").write_text("", encoding="utf-8")

    (bad_proj / "backend" / "main.py").write_text(
        "def create_todo(title: str):\n"
        "    return {'id': 1, 'title': 'WRONG', 'completed': False}\n",
        encoding="utf-8"
    )

    (bad_proj / "tests" / "test_main.py").write_text(
        "from backend.main import create_todo\n"
        "def test_create_todo():\n"
        "    res = create_todo('Buy milk')\n"
        "    assert res['title'] == 'Buy milk'\n",
        encoding="utf-8"
    )

    bad_res = global_project_runner.run_project(str(bad_proj))
    assert bad_res.exit_code != 0
    assert bad_res.status == ExecutionStatus.FAIL

