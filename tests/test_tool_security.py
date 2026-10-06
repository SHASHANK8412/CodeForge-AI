"""Agent tools must not run code by default, and must not return invented results."""
import pytest
from fastapi.testclient import TestClient

from backend.ai_core.tool_registry import global_tool_registry
from backend.main import app
from backend.tools.python_runner import CODE_TOOLS_ENV, global_python_runner_tool

client = TestClient(app)


@pytest.fixture(autouse=True)
def _code_tools_off(monkeypatch):
    monkeypatch.delenv(CODE_TOOLS_ENV, raising=False)


def test_plugin_route_refuses_code_execution():
    res = client.post("/api/plugins/execute", json={"plugin_id": "python_runner", "params": {"code": "print(6*7)"}})
    assert res.status_code == 200 and res.json()["status"] == "error"


def test_high_risk_permissions_are_denied_unless_enabled(monkeypatch):
    from backend.plugins.permissions import global_permission_manager as pm
    for perm in ("python_exec", "execute_commands", "docker_ops", "db_ops"):
        assert pm.check_permission("any_plugin", perm) is False
    assert pm.check_permission("any_plugin", "read_files") is True
    monkeypatch.setenv(CODE_TOOLS_ENV, "1")
    assert pm.check_permission("any_plugin", "python_exec") is True


def test_plugin_route_refuses_shell_commands_by_default():
    res = client.post("/api/plugins/execute", json={"plugin_id": "terminal", "params": {"command": "echo hi"}})
    assert res.json()["status"] == "error"


def test_python_runner_runs_in_a_separate_process_when_enabled(monkeypatch):
    monkeypatch.setenv(CODE_TOOLS_ENV, "1")
    res = global_python_runner_tool.execute({"code": "import os; print(os.getpid())"})
    assert res["status"] == "success"
    import os
    assert int(res["output"].strip()) != os.getpid(), "must not exec inside the server process"


def test_python_runner_times_out(monkeypatch):
    monkeypatch.setenv(CODE_TOOLS_ENV, "1")
    res = global_python_runner_tool.execute({"code": "while True: pass", "timeout": 1})
    assert res["status"] == "error" and "Timed out" in res["error"]


def test_code_execution_tool_does_not_fake_a_pass():
    res = global_tool_registry.execute_tool("code_execution", {"code": "assert False"}, user_confirmed=True)
    assert res["result"]["executed"] is False


def test_calculator_is_safe():
    calc = lambda e: global_tool_registry.execute_tool("calculator", {"expression": e}, user_confirmed=True)["result"]
    assert calc("2 + 3 * (4 - 1)")["result"] == 11
    assert "error" in calc("9**9**9")
    assert "error" in calc("__import__('os')")


def test_file_reader_reads_real_files_and_blocks_escapes():
    read = lambda p: global_tool_registry.execute_tool("file_reader", {"path": p}, user_confirmed=True)["result"]
    assert "AIForge" in read("README.md")["content"]
    assert "error" in read("../../Windows/win.ini")


def test_web_search_does_not_invent_results():
    res = global_tool_registry.execute_tool("web_search", {"query": "fastapi"}, user_confirmed=True)
    assert res["result"]["results"] == []
