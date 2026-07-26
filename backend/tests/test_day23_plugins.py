import pytest
from fastapi.testclient import TestClient

from backend.plugins.sdk import BasePlugin
from backend.plugins.permissions import PermissionManager
from backend.plugins.sandbox import ToolSandbox
from backend.plugins.registry import PluginRegistry
from backend.plugins.executor import ToolExecutionEngine
from backend.plugins.manager import PluginManager
from backend.tools.filesystem import FilesystemTool
from backend.tools.terminal import TerminalTool
from backend.tools.git import GitTool
from backend.tools.docker import DockerTool
from backend.main import app

client = TestClient(app)


def test_plugin_sdk_interface():
    """Test 1: BasePlugin SDK class inheritance and execution interface."""
    class CustomTestPlugin(BasePlugin):
        name = "custom_test"
        version = "1.0.0"
        permissions = ["read_files"]

        def execute(self, params):
            return {"echo": params.get("msg", "")}

    plugin = CustomTestPlugin()
    assert plugin.name == "custom_test"
    res = plugin.execute({"msg": "hello"})
    assert res["echo"] == "hello"


def test_builtin_filesystem_and_terminal_tools(tmp_path):
    """Test 2: Built-in FilesystemTool and TerminalTool execution."""
    fs = FilesystemTool()
    term = TerminalTool()

    test_file = tmp_path / "sample.txt"
    fs.write_file(str(test_file), "AIForge Plugin System Test")
    content = fs.read_file(str(test_file))
    assert content == "AIForge Plugin System Test"

    res_cmd = term.run_cmd("echo Hello Plugin", cwd=str(tmp_path))
    assert res_cmd["exit_code"] == 0
    assert "Hello Plugin" in res_cmd["stdout"]


def test_builtin_git_and_docker_tools():
    """Test 3: Built-in GitTool and DockerTool execution."""
    git_tool = GitTool()
    docker_tool = DockerTool()

    res_git = git_tool.execute({"action": "commit", "message": "Test Commit"})
    assert res_git["status"] == "success"
    assert res_git["action"] == "commit"

    res_docker = docker_tool.execute({"action": "build", "image_name": "test_app:1.0"})
    assert res_docker["status"] == "success"
    assert "test_app:1.0" in res_docker["image"]


def test_permission_manager_and_sandbox():
    """Test 4: PermissionManager enforcement and ToolSandbox permission verification."""
    pm = PermissionManager()
    sandbox = ToolSandbox()

    assert pm.check_permission("filesystem", "read_files") is True
    assert pm.check_permission("terminal", "read_files") is False

    # Execute inside sandbox with valid permission
    res_valid = sandbox.execute_in_sandbox("filesystem", "read_files", lambda: {"status": "ok"})
    assert res_valid["status"] == "success"

    # Execute inside sandbox with invalid permission
    res_invalid = sandbox.execute_in_sandbox("terminal", "unauthorized_perm", lambda: {"status": "ok"})
    assert res_invalid["status"] == "error"
    assert "Permission Denied" in res_invalid["message"]


def test_tool_execution_engine():
    """Test 5: ToolExecutionEngine dispatch, execution counts, and logging."""
    engine = ToolExecutionEngine()

    res = engine.execute_tool("filesystem", {"action": "list", "path": "."})
    assert res["status"] == "success"
    assert res["tool_name"] == "filesystem"

    logs = engine.get_execution_logs()
    assert len(logs) >= 1
    assert logs[-1]["tool_name"] == "filesystem"


def test_plugin_api_endpoints():
    """Test 6: FastAPI Plugin endpoints (/api/plugins, /api/plugins/execute, /api/plugins/logs, /api/plugins/disable)."""
    # 1. GET /api/plugins
    res_list = client.get("/api/plugins")
    assert res_list.status_code == 200
    assert len(res_list.json()["plugins"]) >= 4

    # 2. POST /api/plugins/execute
    res_exec = client.post("/api/plugins/execute", json={"plugin_id": "filesystem", "params": {"action": "list"}})
    assert res_exec.status_code == 200
    assert res_exec.json()["status"] == "success"

    # 3. GET /api/plugins/logs
    res_logs = client.get("/api/plugins/logs")
    assert res_logs.status_code == 200
    assert "logs" in res_logs.json()

    # 4. POST /api/plugins/disable & enable
    res_dis = client.post("/api/plugins/disable", json={"plugin_id": "postgres"})
    assert res_dis.status_code == 200
    assert res_dis.json()["status"] == "success"
