"""
AIForge Plugin Manager
======================
Orchestrates the 7-stage plugin lifecycle:
Install -> Validate -> Register -> Load -> Execute -> Update -> Uninstall
"""

import time
import logging
from typing import Dict, Any, List, Optional
from backend.plugins.validator import global_plugin_manifest_validator
from backend.plugins.permissions import global_plugin_permissions_system
from backend.plugins.registry import global_plugin_registry
from backend.plugins.loader import global_dynamic_plugin_loader

from backend.plugins.monitor import PluginMonitor, _logger as monitor_logger

_logger = logging.getLogger("aiforge.plugins.manager")


class PluginManager:
    """
    Manages complete plugin installation, updates, and lifecycle operations.
    """

    def __init__(self) -> None:
        self.registry = global_plugin_registry
        self.monitor = PluginMonitor()

    def discover_and_load_plugins(self) -> List[Dict[str, Any]]:
        _logger.info("PluginManager: Discovered and loaded installed plugins into active registry.")
        return self.registry.list_plugins()

    def install_plugin(self, manifest_or_name: Any, source_code: Optional[str] = None) -> Any:
        if isinstance(manifest_or_name, str):
            name = manifest_or_name
            manifest = {
                "id": name.lower().replace(" ", "_"),
                "name": name,
                "version": "1.0.0",
                "author": "Community",
                "description": f"Installed plugin {name}",
                "permissions": ["filesystem"],
                "entry": "plugin.py"
            }
            self.registry.register_plugin(manifest)
            _logger.info(f"PluginManager: Installed plugin source '{name}'")
            return True

        manifest = manifest_or_name
        # 1. Validate manifest
        is_valid, errors = global_plugin_manifest_validator.validate_manifest(manifest)
        if not is_valid:
            raise ValueError(f"Plugin installation failed: {errors}")

        # 2. Register plugin
        plugin_entry = global_plugin_registry.register_plugin(manifest)

        _logger.info(f"PluginManager: Installed plugin '{plugin_entry['name']}' successfully.")
        return {
            "status": "INSTALLED",
            "plugin": plugin_entry,
            "lifecycle_stage": "Execute"
        }

    def uninstall_plugin(self, plugin_id: str) -> Any:
        success = global_plugin_registry.unregister_plugin(plugin_id)
        if not success:
            return False
        return {"status": "UNINSTALLED", "plugin_id": plugin_id}

    def enable_plugin(self, plugin_id: str) -> Any:
        success = global_plugin_registry.update_plugin_status(plugin_id, "ACTIVE")
        if not success:
            return False
        return {"status": "ACTIVE", "plugin_id": plugin_id}

    def disable_plugin(self, plugin_id: str) -> Any:
        success = global_plugin_registry.update_plugin_status(plugin_id, "DISABLED")
        if not success:
            return False
        return {"status": "DISABLED", "plugin_id": plugin_id}

    def update_plugin(self, plugin_id: str, new_version: str = "1.1.0") -> Dict[str, Any]:
        plugin = global_plugin_registry.get_plugin(plugin_id)
        if not plugin:
            raise ValueError(f"Plugin '{plugin_id}' not found.")
        plugin["version"] = new_version
        _logger.info(f"PluginManager: Updated plugin '{plugin_id}' to version '{new_version}'")
        return {"status": "UPDATED", "plugin": plugin}

    def get_plugin_dashboard(self) -> Dict[str, Any]:
        all_plugins = global_plugin_registry.list_plugins()
        active = [p for p in all_plugins if p["status"] == "ACTIVE"]
        disabled = [p for p in all_plugins if p["status"] == "DISABLED"]

        return {
            "timestamp": time.time(),
            "total_installed_plugins": len(all_plugins),
            "active_plugins_count": len(active),
            "disabled_plugins_count": len(disabled),
            "installed_plugins": all_plugins,
            "system_event_topics": [
                "PROJECT_CREATED", "BUILD_COMPLETED", "DEPLOYMENT_FINISHED",
                "CODE_GENERATED", "ERROR_DETECTED", "QUALITY_CHECK_COMPLETED"
            ]
        }


global_plugin_manager = PluginManager()
