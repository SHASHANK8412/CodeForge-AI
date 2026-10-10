"""
Day 24 target: AIForge repairs a deliberately broken project on its own.

A small FastAPI project ships with two real bugs (missing imports, the defect the 7B model produced
in real runs). The actual pipeline nodes run: testing (tests + code-quality gate) -> debug ->
patch -> testing again, and the project must end up passing with the fix written to disk.
"""
import asyncio

from backend.agents.repair_strategies import fix_literal_assertion, fix_missing_modules, fix_undefined_names
from backend.graph import parallel_workflow as wf

BROKEN_MAIN = '''app = FastAPI()


@app.get("/health")
def health(limit: Optional[int] = None):
    return {"status": "ok"}
'''

TEST = '''from fastapi.testclient import TestClient
from backend.main import app


def test_health():
    assert TestClient(app).get("/health").json() == {"status": "ok"}
'''


def run(coro):
    return asyncio.run(coro)


def _broken_project(tmp_path):
    (tmp_path / "backend").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "backend" / "main.py").write_text(BROKEN_MAIN, encoding="utf-8")
    (tmp_path / "tests" / "test_main.py").write_text(TEST, encoding="utf-8")
    return {"backend/main.py": BROKEN_MAIN, "tests/test_main.py": TEST}


def test_pipeline_repairs_a_broken_project_and_its_tests_pass(tmp_path, monkeypatch):
    monkeypatch.setattr(wf.testing_agent, "run_async", _no_new_tests)
    files = _broken_project(tmp_path)
    state = {"project_path": str(tmp_path), "files": files, "plan": {"project_name": "demo"},
             "backend": "", "frontend": "", "fixes": [], "retry_count": 0}

    first = run(wf.testing_node(state))
    assert first["test_results"]["success"] is False
    assert {e["message"] for e in first["quality_gate"]["errors"]} >= {"Undefined name `FastAPI`", "Undefined name `Optional`"}

    state.update(first)
    state.update(run(wf.debug_node(state)))
    assert state["fixes"][-1]["changes"], "the debug agent must propose a real change"
    state.update(run(wf.patch_node(state)))

    fixed = (tmp_path / "backend" / "main.py").read_text(encoding="utf-8")
    assert "from fastapi import FastAPI" in fixed and "from typing import Optional" in fixed

    second = run(wf.testing_node(state))
    assert second["test_results"]["success"] is True, second["test_results"]
    assert second["quality_gate"]["passed"] is True


async def _no_new_tests(*_args, **_kwargs):
    return ""


def test_imports_are_added_not_commented_out():
    files = {"backend/main.py": '"""API."""\nimport os\n\napp = FastAPI()\n'}
    errors = [{"file": "backend/main.py", "message": "Undefined name `FastAPI`"}]
    fixed = fix_undefined_names(files, errors)["backend/main.py"]
    assert fixed.splitlines()[:3] == ['"""API."""', "import os", "from fastapi import FastAPI"]
    assert "app = FastAPI()" in fixed and "#" not in fixed


def test_missing_packages_go_into_requirements():
    files = {"requirements.txt": "fastapi\n", "backend/auth.py": "from jose import jwt\n"}
    out = "E   ModuleNotFoundError: No module named 'jose'"
    assert fix_missing_modules(files, out) == {"requirements.txt": "fastapi\npython-jose[cryptography]\n"}


def test_ambiguous_literal_mismatch_is_left_alone():
    files = {"backend/a.py": "X = 'WRONG'\n", "backend/b.py": "Y = 'WRONG'\n"}
    assert fix_literal_assertion(files, "assert 'WRONG' == 'OK'") == {}


def test_no_fix_found_is_not_reported_as_a_fix():
    from backend.agents.debug_agent import global_debug_agent
    res = global_debug_agent.diagnose_and_repair({
        "files": {"backend/main.py": "def f():\n    return 1\n"},
        "test_results": {"success": False, "overall_status": "FAIL", "output": "something odd happened"},
        "execution_results": {"exit_code": 1, "stderr": "something odd happened"},
    })
    assert res.success is False and res.changes == {}
