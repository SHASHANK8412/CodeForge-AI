import logging
from typing import List, Set

_logger = logging.getLogger("aiforge.plugins")

class PermissionValidator:
    """
    Enforces sandbox permission gates (verifies filesystem, network, and system access constraints).
    """

    VALID_PERMISSIONS = {
        "filesystem:read",
        "filesystem:write",
        "network:outbound",
        "env:read",
        "subprocess:run"
    }

    def __init__(self, allowed_permissions: List[str] = None) -> None:
        if allowed_permissions is None:
            # Safe defaults (read filesystem only)
            allowed_permissions = ["filesystem:read"]
        self.allowed: Set[str] = {p for p in allowed_permissions if p in self.VALID_PERMISSIONS}

    def verify_permissions(self, requested: List[str]) -> bool:
        """
        Validates whether requested permissions fall under the allowed sandbox limits.
        """
        for req in requested:
            if req not in self.allowed:
                _logger.warning(f"Permission Blocked: Sandbox rejected access to '{req}'")
                return False
        return True

    def has_permission(self, permission: str) -> bool:
        return permission in self.allowed
