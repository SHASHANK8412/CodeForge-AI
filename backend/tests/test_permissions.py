"""
Unit tests for Day 45 MCPPermissionsSystem
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import unittest
from backend.mcp.permissions import MCPPermissionsSystem, PermissionLevel


class TestPermissions(unittest.TestCase):

    def setUp(self):
        self.perms = MCPPermissionsSystem()

    def test_permission_hierarchy(self):
        self.assertTrue(self.perms.check_permission("read_file", PermissionLevel.READ))
        self.assertTrue(self.perms.check_permission("read_file", PermissionLevel.ADMIN))
        self.assertFalse(self.perms.check_permission("aws_deploy", PermissionLevel.READ))
        self.assertTrue(self.perms.check_permission("aws_deploy", PermissionLevel.ADMIN))


if __name__ == "__main__":
    unittest.main()
