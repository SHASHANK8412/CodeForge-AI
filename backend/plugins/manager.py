import logging
from typing import Dict, Any, List, Optional

from backend.plugins.registry import global_plugin_registry
from backend.plugins.executor import global_tool_execution_engine

logger = logging.getLogger("aiforge.plugins.manager")


class PluginManager:
    """
    PluginManager discovers, enables, disables, installs, and manages lifecycle
    for built-in and third-party SDK plugins.
    """

    def list_all_plugins(self) -> List[Dict[str, Any]]:
        """Lists all registered plugins and execution metrics."""
        return global_plugin_registry.list_plugins()

    def enable_plugin(self, plugin_id: str) -> bool:
        """Enables a plugin."""
        return global_plugin_registry.set_enabled(plugin_id, True)

    def disable_plugin(self, plugin_id: str) -> bool:
        """Disables a plugin."""
        return global_plugin_registry.set_enabled(plugin_id, False)

    def install_plugin(self, name: str, version: str = "1.0.0", permissions: List[str] = None) -> Dict[str, Any]:
        """Installs a custom third-party SDK plugin into registry."""
        safe_id = name.lower().replace(" ", "_")
        global_plugin_registry.plugins[safe_id] = {
            "name": name,
            "version": version,
            "enabled": True,
            "permissions": permissions or ["read_files"],
            "execution_count": 0
        }
        logger.info(f"PluginManager installed custom plugin '{name}' ({safe_id})")
        return {"status": "success", "plugin_id": safe_id}

    def execute_plugin(self, plugin_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a plugin tool via ToolExecutionEngine."""
        return global_tool_execution_engine.execute_tool(plugin_id, params)

    def get_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns execution logs."""
        return global_tool_execution_engine.get_execution_logs(limit)


# Global PluginManager Instance
global_plugin_manager = PluginManager()
