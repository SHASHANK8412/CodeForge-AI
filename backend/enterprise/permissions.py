"""
AIForge RBAC Permissions Engine
===============================
Enforces Role-Based Access Control (RBAC) across enterprise roles:
Owner, Admin, Architect, Developer, QA Engineer, DevOps Engineer, Viewer.
"""

import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.enterprise.permissions")


class Role:
    OWNER = "Owner"
    ADMIN = "Admin"
    ARCHITECT = "Architect"
    DEVELOPER = "Developer"
    QA = "QA Engineer"
    DEVOPS = "DevOps Engineer"
    VIEWER = "Viewer"

    ALL_ROLES = [OWNER, ADMIN, ARCHITECT, DEVELOPER, QA, DEVOPS, VIEWER]


class RBACPermissionsEngine:
    """
    Enforces role-based permissions matrix.
    """

    PERMISSION_MATRIX = {
        Role.OWNER: ["create_project", "delete_project", "deploy", "manage_agents", "view_reports", "configure_models", "manage_roles", "manage_billing"],
        Role.ADMIN: ["create_project", "delete_project", "deploy", "manage_agents", "view_reports", "configure_models", "manage_roles"],
        Role.ARCHITECT: ["create_project", "deploy", "manage_agents", "view_reports", "configure_models"],
        Role.DEVELOPER: ["create_project", "deploy", "view_reports"],
        Role.QA: ["view_reports"],
        Role.DEVOPS: ["deploy", "view_reports", "configure_models"],
        Role.VIEWER: ["view_reports"]
    }

    def check_permission(self, role: str, action: str) -> bool:
        allowed_actions = self.PERMISSION_MATRIX.get(role, [])
        is_allowed = action in allowed_actions
        _logger.info(f"RBACPermissionsEngine: Checking permission '{action}' for role '{role}' -> {is_allowed}")
        return is_allowed

    def get_role_permissions(self, role: str) -> List[str]:
        return self.PERMISSION_MATRIX.get(role, [])


global_rbac_permissions_engine = RBACPermissionsEngine()
