import logging
from typing import Dict, Any, Callable

from backend.plugins.permissions import global_permission_manager

logger = logging.getLogger("aiforge.plugins.sandbox")


class ToolSandbox:
    """
    ToolSandbox provides a secure execution container verifying permission tokens
    and catching unhandled exceptions before tool execution.
    """

    def execute_in_sandbox(
        self,
        plugin_name: str,
        required_permission: str,
        action_fn: Callable[[], Dict[str, Any]]
    ) -> Dict[str, Any]:
        if not global_permission_manager.check_permission(plugin_name, required_permission):
            return {
                "status": "error",
                "message": f"Permission Denied: Plugin '{plugin_name}' lacks required permission '{required_permission}'.",
                "result": None
            }

        try:
            result = action_fn()
            return {
                "status": "success",
                "message": "Tool executed successfully within sandbox.",
                "result": result
            }
        except Exception as e:
            logger.error(f"Sandbox execution error for '{plugin_name}': {e}")
            return {
                "status": "error",
                "message": f"Sandbox Execution Error: {str(e)}",
                "result": None
            }


# Global ToolSandbox Instance
global_tool_sandbox = ToolSandbox()
