"""
AIForge Role-Based Access Control (RBAC) Permissions Manager
============================================================
Enforces role-based permissions across team members:
Roles: Owner, Maintainer, Developer, Reviewer, Viewer.
Operations: edit_code, deploy, review, view_only.
"""

import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.collaboration")


class RBACPermissionsManager:
    """
    Enforces role permissions across workspace operations.
    """

    def __init__(self) -> None:
        self.role_permissions = {
            "Owner": ["edit_code", "deploy", "review", "view_only", "manage_roles", "delete_project"],
            "Maintainer": ["edit_code", "deploy", "review", "view_only"],
            "Developer": ["edit_code", "review", "view_only"],
            "Reviewer": ["review", "view_only"],
            "Viewer": ["view_only"]
        }

    def check_permission(self, role: str, action: str) -> bool:
        allowed_actions = self.role_permissions.get(role, ["view_only"])
        has_permission = action in allowed_actions
        if not has_permission:
            _logger.warning(f"RBACPermissionsManager: Action '{action}' DENIED for role '{role}'")
        return has_permission


global_permissions_manager = RBACPermissionsManager()
