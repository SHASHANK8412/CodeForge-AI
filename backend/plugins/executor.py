import time
import logging
from typing import Dict, Any, List

from backend.plugins.registry import global_plugin_registry
from backend.plugins.sandbox import global_tool_sandbox
from backend.tools import (
    global_filesystem_tool,
    global_terminal_tool,
    global_git_tool,
    global_postgres_tool,
    global_docker_tool,
    global_browser_tool,
    global_python_runner_tool
)

logger = logging.getLogger("aiforge.plugins.executor")


class ToolExecutionEngine:
    """
    ToolExecutionEngine dispatches agent tool calls to registered plugin implementations,
    verifying permissions in ToolSandbox and recording telemetry logs.
    """

    TOOL_MAP = {
        "filesystem": (global_filesystem_tool, "read_files"),
        "terminal": (global_terminal_tool, "execute_commands"),
        "git": (global_git_tool, "git_ops"),
        "postgres": (global_postgres_tool, "db_ops"),
        "docker": (global_docker_tool, "docker_ops"),
        "browser": (global_browser_tool, "browser_ops"),
        "python_runner": (global_python_runner_tool, "python_exec")
    }

    def __init__(self):
        self.logs: List[Dict[str, Any]] = []

    def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches tool execution safely through ToolSandbox."""
        start_time = time.time()
        tool_meta = global_plugin_registry.get_plugin(tool_name)

        if not tool_meta:
            return {"status": "error", "message": f"Tool '{tool_name}' not found in registry."}

        if not tool_meta.get("enabled", True):
            return {"status": "error", "message": f"Tool '{tool_name}' is currently disabled."}

        tool_tuple = self.TOOL_MAP.get(tool_name)
        if not tool_tuple:
            return {"status": "error", "message": f"No implementation handler for tool '{tool_name}'."}

        tool_instance, req_permission = tool_tuple

        # Execute inside ToolSandbox
        sandbox_res = global_tool_sandbox.execute_in_sandbox(
            plugin_name=tool_name,
            required_permission=req_permission,
            action_fn=lambda: tool_instance.execute(params)
        )

        elapsed = round(time.time() - start_time, 3)
        global_plugin_registry.increment_execution(tool_name)

        log_entry = {
            "tool_name": tool_name,
            "status": sandbox_res["status"],
            "execution_time_seconds": elapsed,
            "params": params,
            "timestamp": time.time()
        }
        self.logs.append(log_entry)

        logger.info(f"Executed tool '{tool_name}' in {elapsed}s (Status: {sandbox_res['status']})")
        return {
            "tool_name": tool_name,
            "status": sandbox_res["status"],
            "result": sandbox_res.get("result"),
            "message": sandbox_res.get("message"),
            "execution_time_seconds": elapsed
        }

    def get_execution_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns recent tool execution logs."""
        return self.logs[-limit:]


# Global ToolExecutionEngine Instance
global_tool_execution_engine = ToolExecutionEngine()
