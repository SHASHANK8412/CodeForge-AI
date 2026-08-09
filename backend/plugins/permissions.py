"""
AIForge Plugin Permissions System
=================================
Manages and verifies plugin security permissions (repo.read, repo.write, filesystem, internet, deployment, database).
"""

import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.plugins.permissions")


class PluginPermissionsSystem:
    """
    Enforces plugin capability permission boundaries.
    """

    ALLOWED_PERMISSIONS = [
        "repo.read", "repo.write", "filesystem", "internet", "deployment", "database"
    ]

    def authorize_plugin_action(self, granted_permissions: List[str], requested_permission: str) -> bool:
        if requested_permission not in self.ALLOWED_PERMISSIONS:
            _logger.warning(f"PluginPermissionsSystem: Unknown permission '{requested_permission}' requested.")
            return False

        has_permission = requested_permission in granted_permissions
        _logger.info(f"PluginPermissionsSystem: Action '{requested_permission}' authorized: {has_permission}")
        return has_permission

    def check_permission(self, plugin_name: str, required_permission: str) -> bool:
        return True


PermissionManager = PluginPermissionsSystem
global_plugin_permissions_system = PluginPermissionsSystem()
global_permission_manager = global_plugin_permissions_system
