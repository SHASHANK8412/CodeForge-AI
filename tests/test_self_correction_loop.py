"""
Unit and Real Integration Tests for AIForge Closed Self-Correction Loop (Phase 9)
"""

import shutil
import pytest
from pathlib import Path
from unittest.mock import AsyncMock
from langgraph.graph import END
from backend.graph.parallel_workflow import (
    parallel_graph,
    debug_node,
    patch_node,
    route_after_testing,
    restore_file_backups,
    execution_validation_node,
    testing_node
)
from backend.graph.project_state import ProjectState
from backend.execution.project_runner import global_project_runner
from backend.agents.debug_agent import global_debug_agent
from backend.agents.testing_agent import TestingAgent


@pytest.fixture
def tmp_projects_dir(tmp_path):
    p = tmp_path / "generated_projects"
    p.mkdir(parents=True, exist_ok=True)
    yield p
    if p.exists():
        shutil.rmtree(p, ignore_errors=True)


def test_pass_routing():
    state: ProjectState = {
        "execution_results": {"exit_code": 0},
        "test_results": {"success": True},
        "status": "PASS",
        "iteration": 0,
        "max_iterations": 3
    }
    route = route_after_testing(state)
    assert route == "packaging"


def test_fail_routing():
    state: ProjectState = {
        "execution_results": {"exit_code": 1},
        "test_results": {"success": False},
        "status": "FAIL",
        "iteration": 0,
        "max_iterations": 3
    }
    route = route_after_testing(state)
    assert route == "debug"


def test_maximum_iteration_enforcement_routes_to_end_not_packaging():
    state: ProjectState = {
        "execution_results": {"exit_code": 1},
        "test_results": {"success": False},
        "status": "FAIL",
        "iteration": 3,
        "max_iterations": 3
    }
    route = route_after_testing(state)
    assert route != "packaging"
    assert route == END
    assert state["status"] == "FAILED_MAX_ITERATIONS"


def test_unsupported_project_routing_end_not_packaging():
    state: ProjectState = {
        "execution_results": {"exit_code": 1},
        "test_results": {"success": False},
        "status": "UNSUPPORTED",
        "iteration": 1,
        "max_iterations": 3
    }
    route = route_after_testing(state)
    assert route != "packaging"
    assert route == END


def test_security_error_routing_end_not_packaging():
    state: ProjectState = {
        "execution_results": {"exit_code": 1},
        "test_results": {"success": False},
        "status": "SECURITY_ERROR",
        "iteration": 1,
        "max_iterations": 3
    }
    route = route_after_testing(state)
    assert route != "packaging"
    assert route == END


def test_patch_path_traversal_rejection(tmp_projects_dir):
    proj = tmp_projects_dir / "PatchApp"
    proj.mkdir()
    state: ProjectState = {
        "project_path": str(proj),
        "fixes": [{
            "files_to_modify": ["../../outside.py"],
            "changes": {"../../outside.py": "hacked"}
        }],
        "files": {}
    }

    import asyncio
    asyncio.run(patch_node(state))
    assert not (tmp_projects_dir / "outside.py").exists()


def test_absolute_path_rejection(tmp_projects_dir):
    proj = tmp_projects_dir / "AbsApp"
    proj.mkdir()
    state: ProjectState = {
        "project_path": str(proj),
        "fixes": [{
            "files_to_modify": ["/etc/passwd"],
            "changes": {"/etc/passwd": "root:x"}
        }],
        "files": {}
    }

    import asyncio
    asyncio.run(patch_node(state))
    assert not Path("/etc/passwd").exists() or not (proj / "etc" / "passwd").exists()


def test_targeted_single_file_patching(tmp_projects_dir):
    proj = tmp_projects_dir / "SinglePatch"
    proj.mkdir()
    (proj / "backend").mkdir()
    main_file = proj / "backend" / "main.py"
    main_file.write_text("v1", encoding="utf-8")

    state: ProjectState = {
        "project_path": str(proj),
        "fixes": [{
            "files_to_modify": ["backend/main.py"],
            "changes": {"backend/main.py": "v2"}
        }],
        "files": {"backend/main.py": "v1"}
    }

    import asyncio
    res = asyncio.run(patch_node(state))
    assert main_file.read_text(encoding="utf-8") == "v2"
    assert res["files"]["backend/main.py"] == "v2"


def test_patch_backup(tmp_projects_dir):
    proj = tmp_projects_dir / "BackupApp"
    proj.mkdir()
    (proj / "main.py").write_text("original", encoding="utf-8")

    state: ProjectState = {
        "project_path": str(proj),
        "fixes": [{
            "files_to_modify": ["main.py"],
            "changes": {"main.py": "patched"}
        }],
        "files": {"main.py": "original"}
    }

    import asyncio
    res = asyncio.run(patch_node(state))
    assert res["file_backups"]["main.py"] == "original"
    assert (proj / "main.py").read_text() == "patched"


def test_actual_rollback_restoration(tmp_projects_dir):
    proj = tmp_projects_dir / "RollbackApp"
    proj.mkdir()
    main_file = proj / "main.py"

    original_code = "def get_status(): return {'status': 'WRONG'}\n"
    bad_patched_code = "def get_status(): return {'status': 'CRASH'}\n"

    main_file.write_text(bad_patched_code, encoding="utf-8")

    state: ProjectState = {
        "project_path": str(proj),
        "files": {"main.py": bad_patched_code},
        "file_backups": {"main.py": original_code}
    }

    # Execute rollback
    res = restore_file_backups(state)
    assert main_file.read_text(encoding="utf-8") == original_code
    assert res["files"]["main.py"] == original_code


@pytest.mark.anyio
async def test_full_broken_todo_app_self_healing_integration(tmp_projects_dir):
    # 1. Create a broken project on disk
    broken_proj = tmp_projects_dir / "BrokenTodoApp"
    (broken_proj / "backend").mkdir(parents=True)
    (broken_proj / "tests").mkdir(parents=True)
    (broken_proj / "backend" / "__init__.py").write_text("", encoding="utf-8")
    (broken_proj / "tests" / "__init__.py").write_text("", encoding="utf-8")

    backend_code = "def get_status():\n    return {'status': 'WRONG'}\n"
    test_code = "from backend.main import get_status\ndef test_status():\n    assert get_status()['status'] == 'OK'\n"

    (broken_proj / "backend" / "main.py").write_text(backend_code, encoding="utf-8")
    (broken_proj / "tests" / "test_status.py").write_text(test_code, encoding="utf-8")

    state: ProjectState = {
        "project_name": "BrokenTodoApp",
        "project_path": str(broken_proj),
        "files": {
            "backend/main.py": backend_code,
            "tests/test_status.py": test_code
        },
        "iteration": 0,
        "max_iterations": 3,
        "commands": [],
        "fixes": [],
        "errors": []
    }

    # Step 1: Initial Run & Verification -> FAIL
    exec_res1 = await execution_validation_node(state)
    state.update(exec_res1)
    test_res1 = await testing_node(state)
    state.update(test_res1)

    assert state["status"] == "FAIL"
    assert state["test_results"]["success"] is False

    # Step 2: Route after testing -> debug
    route1 = route_after_testing(state)
    assert route1 == "debug"

    # Step 3: Debugger -> patch
    debug_res1 = await debug_node(state)
    state.update(debug_res1)
    assert state["iteration"] == 1

    patch_res1 = await patch_node(state)
    state.update(patch_res1)

    # Verify backend/main.py was patched on disk with status OK
    patched_file = broken_proj / "backend" / "main.py"
    assert "'OK'" in patched_file.read_text(encoding="utf-8")

    # Step 4: Retest -> PASS
    exec_res2 = await execution_validation_node(state)
    state.update(exec_res2)
    test_res2 = await testing_node(state)
    state.update(test_res2)

    assert state["status"] == "PASS"
    assert state["test_results"]["success"] is True
    assert state["execution_results"]["exit_code"] == 0

    route2 = route_after_testing(state)
    assert route2 == "packaging"


@pytest.mark.anyio
async def test_fail_after_three_iterations(tmp_projects_dir):
    unfixable_proj = tmp_projects_dir / "UnfixableApp"
    unfixable_proj.mkdir()
    (unfixable_proj / "main.py").write_text("def broken(): syntax error", encoding="utf-8")

    state: ProjectState = {
        "project_name": "UnfixableApp",
        "project_path": str(unfixable_proj),
        "files": {"main.py": "def broken(): syntax error"},
        "iteration": 2,
        "max_iterations": 3,
        "commands": [],
        "fixes": [],
        "errors": []
    }

    # Attempt 3 (Iteration 2 -> 3)
    exec_res = await execution_validation_node(state)
    state.update(exec_res)
    test_res = await testing_node(state)
    state.update(test_res)

    debug_res = await debug_node(state)
    state.update(debug_res)

    assert state["iteration"] == 3

    route = route_after_testing(state)
    assert route != "packaging"
    assert route == END
    assert state["status"] == "FAILED_MAX_ITERATIONS"
