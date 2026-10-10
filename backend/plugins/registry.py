"""
AIForge Plugin Registry
=======================
Stores installed, active, and disabled plugin metadata, versions, and capabilities.
"""

import time
import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.plugins.registry")


class PluginRegistry:
    """
    Registry maintaining installed plugin metadata.
    """

    def __init__(self) -> None:
        self.plugins: Dict[str, Dict[str, Any]] = {
            "github_plugin": {
                "id": "github_plugin",
                "name": "GitHub Integration Plugin",
                "version": "1.0.0",
                "author": "AIForge Core",
                "description": "Integrates GitHub Repositories, PRs, and Actions",
                "category": "Integrations",
                "status": "ACTIVE",
                "permissions": ["repo.read", "repo.write", "internet"],
                "installed_at": time.time() - 86400 * 5
            },
            "slack_plugin": {
                "id": "slack_plugin",
                "name": "Slack Notifications Plugin",
                "version": "1.2.0",
                "author": "AIForge Core",
                "description": "Dispatches real-time project alerts to Slack channels",
                "category": "Productivity",
                "status": "ACTIVE",
                "permissions": ["internet"],
                "installed_at": time.time() - 86400 * 3
            }
        }

    def _key(self, plugin_id: str) -> Optional[str]:
        """The stored key for a plugin id or name, matched case-insensitively."""
        if plugin_id in self.plugins:
            return plugin_id
        lowered = str(plugin_id).lower().replace(" ", "_")
        return lowered if lowered in self.plugins else None

    def register_plugin(self, manifest: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        register_plugin(manifest) installs an active plugin. The original call form
        register_plugin(name, metadata) registers it disabled until enable_plugin/update_status.
        """
        if isinstance(manifest, str):
            entry = self.register_plugin({**(metadata or {}), "name": (metadata or {}).get("name", manifest)})
            entry["status"] = "Disabled"
            return entry
        p_id = manifest.get("id") or manifest.get("name", "plugin").lower().replace(" ", "_")
        entry = {
            "id": p_id,
            "name": manifest.get("name"),
            "version": manifest.get("version", "1.0.0"),
            "author": manifest.get("author", "Community"),
            "description": manifest.get("description", ""),
            "category": manifest.get("category", "General"),
            "status": "ACTIVE",
            "permissions": manifest.get("permissions", []),
            "installed_at": time.time()
        }
        self.plugins[p_id] = entry
        _logger.info(f"PluginRegistry: Registered plugin '{entry['name']}' (ID: {p_id})")
        return entry

    def unregister_plugin(self, plugin_id: str) -> bool:
        plugin_id = self._key(plugin_id) or plugin_id
        if plugin_id in self.plugins:
            del self.plugins[plugin_id]
            _logger.info(f"PluginRegistry: Unregistered plugin '{plugin_id}'")
            return True
        return False

    def update_plugin_status(self, plugin_id: str, new_status: str) -> bool:
        plugin_id = self._key(plugin_id) or plugin_id
        if plugin_id in self.plugins:
            self.plugins[plugin_id]["status"] = new_status
            _logger.info(f"PluginRegistry: Plugin '{plugin_id}' status updated to '{new_status}'")
            return True
        return False

    def list_plugins(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        results = list(self.plugins.values())
        if status:
            results = [p for p in results if p["status"].lower() == status.lower()]
        return results

    update_status = update_plugin_status

    def get_plugin(self, plugin_id: str) -> Dict[str, Any]:
        """The plugin's entry, or {} when it isn't registered."""
        key = self._key(plugin_id)
        return self.plugins[key] if key else {}

    def get_all_registered(self) -> Dict[str, Dict[str, Any]]:
        return self.plugins


global_plugin_registry = PluginRegistry()
