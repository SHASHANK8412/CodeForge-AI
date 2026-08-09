"""
AIForge Role-Based Access Control (RBAC) Manager
================================================
Defines system roles and permission checks for enterprise governance:
Administrator, Project Manager, Developer, Reviewer, QA Engineer, Viewer.
"""

from typing import Dict, Any, List, Set


class RBACManager:
    """
    Manages roles, permissions, and access verification.
    """

    ROLES: Dict[str, Set[str]] = {
        "Administrator": {
            "create_project", "delete_project", "switch_project", "manage_roles",
            "approve_requirements", "approve_architecture", "approve_code", "approve_deployment", "approve_production",
            "view_audit", "write_comments", "trigger_build", "view_dashboard"
        },
        "Project Manager": {
            "create_project", "switch_project",
            "approve_requirements", "approve_architecture", "approve_deployment",
            "view_audit", "write_comments", "trigger_build", "view_dashboard"
        },
        "Developer": {
            "switch_project", "write_comments", "trigger_build", "view_dashboard", "edit_code"
        },
        "Reviewer": {
            "switch_project", "approve_architecture", "approve_code", "approve_deployment",
            "view_audit", "write_comments", "view_dashboard"
        },
        "QA Engineer": {
            "switch_project", "approve_code", "write_comments", "trigger_build", "view_dashboard"
        },
        "Viewer": {
            "switch_project", "view_dashboard"
        }
    }

    def __init__(self) -> None:
        self.user_roles: Dict[str, str] = {
            "admin_user": "Administrator",
            "pm_user": "Project Manager",
            "reviewer_user": "Reviewer",
            "dev_user": "Developer"
        }

    def get_role_permissions(self, role: str) -> List[str]:
        if role in self.ROLES:
            return sorted(list(self.ROLES[role]))
        raise ValueError(f"Role '{role}' not defined. Allowed: {list(self.ROLES.keys())}")

    def assign_user_role(self, user_id: str, role: str) -> Dict[str, Any]:
        if role not in self.ROLES:
            raise ValueError(f"Invalid role '{role}'. Allowed: {list(self.ROLES.keys())}")
        self.user_roles[user_id] = role
        return {"user_id": user_id, "role": role, "permissions": self.get_role_permissions(role)}

    def check_permission(self, user_id_or_role: str, permission: str) -> bool:
        # Check if user_id_or_role is directly a role name
        if user_id_or_role in self.ROLES:
            return permission in self.ROLES[user_id_or_role]
        
        # Look up role for user_id
        role = self.user_roles.get(user_id_or_role, "Viewer")
        return permission in self.ROLES.get(role, set())

    def get_all_roles(self) -> List[Dict[str, Any]]:
        return [
            {"role": r, "permissions": sorted(list(perms))}
            for r, perms in self.ROLES.items()
        ]


global_rbac_manager = RBACManager()
