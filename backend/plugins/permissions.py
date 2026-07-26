import logging
from typing import Dict, Any, List, Set

logger = logging.getLogger("aiforge.plugins.permissions")


class PermissionManager:
    """
    PermissionManager enforces fine-grained permission control before plugin tools execute.
    """

    ALLOWED_PERMISSIONS: Set[str] = {
        "read_files",
        "write_files",
        "execute_commands",
        "git_ops",
        "db_ops",
        "docker_ops",
        "browser_ops",
        "python_exec"
    }

    def __init__(self):
        self.granted_permissions: Dict[str, Set[str]] = {
            "filesystem": {"read_files", "write_files"},
            "terminal": {"execute_commands"},
            "git": {"git_ops"},
            "postgres": {"db_ops"},
            "docker": {"docker_ops"},
            "browser": {"browser_ops"},
            "python_runner": {"python_exec"}
        }

    def check_permission(self, plugin_name: str, required_permission: str) -> bool:
        """Verifies if plugin has been granted the required permission."""
        granted = self.granted_permissions.get(plugin_name, set())
        has_perm = required_permission in granted
        if not has_perm:
            logger.warning(f"Permission check failed for '{plugin_name}': Requires '{required_permission}'")
        return has_perm

    def grant_permission(self, plugin_name: str, permission: str) -> None:
        self.granted_permissions.setdefault(plugin_name, set()).add(permission)

    def revoke_permission(self, plugin_name: str, permission: str) -> None:
        if plugin_name in self.granted_permissions:
            self.granted_permissions[plugin_name].discard(permission)


# Global PermissionManager Instance
global_permission_manager = PermissionManager()
