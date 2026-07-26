import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("aiforge.plugins.registry")


class PluginRegistry:
    """
    PluginRegistry maintains plugin metadata, status (enabled/disabled), version, and permissions.
    """

    def __init__(self):
        self.plugins: Dict[str, Dict[str, Any]] = {
            "filesystem": {
                "name": "Filesystem Tool",
                "version": "1.0.0",
                "enabled": True,
                "permissions": ["read_files", "write_files"],
                "execution_count": 0
            },
            "terminal": {
                "name": "Terminal Command Execution",
                "version": "1.0.0",
                "enabled": True,
                "permissions": ["execute_commands"],
                "execution_count": 0
            },
            "git": {
                "name": "Git Repository Tool",
                "version": "1.0.0",
                "enabled": True,
                "permissions": ["git_ops"],
                "execution_count": 0
            },
            "postgres": {
                "name": "PostgreSQL Query Tool",
                "version": "1.0.0",
                "enabled": True,
                "permissions": ["db_ops"],
                "execution_count": 0
            },
            "docker": {
                "name": "Docker Container Lifecycle",
                "version": "1.0.0",
                "enabled": True,
                "permissions": ["docker_ops"],
                "execution_count": 0
            },
            "browser": {
                "name": "Browser & Documentation Web Scraper",
                "version": "1.0.0",
                "enabled": True,
                "permissions": ["browser_ops"],
                "execution_count": 0
            },
            "python_runner": {
                "name": "Python Code Execution Runner",
                "version": "1.0.0",
                "enabled": True,
                "permissions": ["python_exec"],
                "execution_count": 0
            }
        }

    def list_plugins(self) -> List[Dict[str, Any]]:
        """Returns list of registered plugins."""
        return [
            {"id": p_id, **meta}
            for p_id, meta in self.plugins.items()
        ]

    def get_all_registered(self) -> Dict[str, Dict[str, Any]]:
        """Returns map of all registered plugins."""
        return self.plugins

    def get_plugin(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        return self.plugins.get(plugin_id)

    def set_enabled(self, plugin_id: str, enabled: bool) -> bool:
        if plugin_id in self.plugins:
            self.plugins[plugin_id]["enabled"] = enabled
            return True
        return False

    def increment_execution(self, plugin_id: str) -> None:
        if plugin_id in self.plugins:
            self.plugins[plugin_id]["execution_count"] += 1


# Global PluginRegistry Instance
global_plugin_registry = PluginRegistry()
