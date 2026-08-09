"""
AIForge MCP Tool Permission System (Day 45)
===========================================
Defines fine-grained permission levels (READ, WRITE, EXECUTE, ADMIN) and enforces authorization checks before tool invocation.
"""

import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.mcp.permissions")


class PermissionLevel:
    READ = "READ"
    WRITE = "WRITE"
    EXECUTE = "EXECUTE"
    ADMIN = "ADMIN"


class MCPPermissionsSystem:
    """
    Enforces authorization policy and permission validation for MCP tool executions.
    """

    def __init__(self):
        self.tool_permissions: Dict[str, str] = {
            "read_file": PermissionLevel.READ,
            "write_file": PermissionLevel.WRITE,
            "create_pr": PermissionLevel.WRITE,
            "push_commit": PermissionLevel.WRITE,
            "query_db": PermissionLevel.READ,
            "execute_db_migration": PermissionLevel.ADMIN,
            "build_docker": PermissionLevel.EXECUTE,
            "run_container": PermissionLevel.EXECUTE,
            "browser_search": PermissionLevel.READ,
            "terminal_run": PermissionLevel.EXECUTE,
            "aws_deploy": PermissionLevel.ADMIN,
            "jira_create": PermissionLevel.WRITE,
            "slack_notify": PermissionLevel.WRITE
        }

    def check_permission(self, tool_name: str, granted_permission: str) -> bool:
        """
        Validates if granted_permission satisfies the required permission level for tool_name.
        """
        req_level = self.tool_permissions.get(tool_name, PermissionLevel.EXECUTE)

        hierarchy = {
            PermissionLevel.READ: 1,
            PermissionLevel.WRITE: 2,
            PermissionLevel.EXECUTE: 3,
            PermissionLevel.ADMIN: 4
        }

        granted_rank = hierarchy.get(granted_permission, 1)
        req_rank = hierarchy.get(req_level, 3)

        allowed = granted_rank >= req_rank
        _logger.info(f"MCPPermissionsSystem: Checked '{tool_name}' (req: {req_level}, granted: {granted_permission}) -> Allowed: {allowed}")
        return allowed


global_mcp_permissions = MCPPermissionsSystem()
