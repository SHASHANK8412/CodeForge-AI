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

    # Permissions that let a caller run code or commands, or reach containers and databases.
    HIGH_RISK_PERMISSIONS = {"python_exec", "execute_commands", "docker_ops", "db_ops"}

    def check_permission(self, plugin_name: str, required_permission: str) -> bool:
        if required_permission in self.HIGH_RISK_PERMISSIONS:
            from backend.tools.python_runner import code_tools_enabled
            if not code_tools_enabled():
                _logger.warning("Denied '%s' for plugin '%s': code tools are disabled", required_permission, plugin_name)
                return False
        return True


class PermissionValidator:
    """
    Sandbox permission gate for plugin capabilities (the Day 23 plugin API): only permissions in
    VALID_PERMISSIONS can be granted, and a request passes only if every item was granted.
    """

    VALID_PERMISSIONS = {"filesystem:read", "filesystem:write", "network:outbound", "env:read", "subprocess:run"}

    def __init__(self, allowed_permissions: Optional[List[str]] = None) -> None:
        allowed_permissions = ["filesystem:read"] if allowed_permissions is None else allowed_permissions
        self.allowed = {p for p in allowed_permissions if p in self.VALID_PERMISSIONS}

    def verify_permissions(self, requested: List[str]) -> bool:
        for req in requested:
            if req not in self.allowed:
                _logger.warning("Permission blocked: sandbox rejected access to '%s'", req)
                return False
        return True

    def has_permission(self, permission: str) -> bool:
        return permission in self.allowed


PermissionManager = PluginPermissionsSystem
global_plugin_permissions_system = PluginPermissionsSystem()
global_permission_manager = global_plugin_permissions_system
