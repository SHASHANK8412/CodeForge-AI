"""
Unit tests for Day 45 MCPManager
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import unittest
from backend.mcp.mcp_manager import MCPManager


class TestMCPManager(unittest.TestCase):

    def setUp(self):
        self.manager = MCPManager()

    def test_mcp_discovery_and_execution(self):
        tools = self.manager.discover_tools("github")
        self.assertIn("github", tools)

        res = self.manager.execute_tool_call("github", "create_pr", {"title": "New Feature"}, user_permission="WRITE")
        self.assertEqual(res["status"], "SUCCESS")

    def test_permission_denied(self):
        res = self.manager.execute_tool_call("postgres", "execute_db_migration", {"sql": "DROP TABLE users"}, user_permission="READ")
        self.assertEqual(res["status"], "PERMISSION_DENIED")

    def test_offline_fallback_execution(self):
        res = self.manager.execute_tool_call("slack", "slack_notify", {"message": "hello"}, user_permission="WRITE")
        self.assertEqual(res["status"], "FALLBACK_EXECUTED")


if __name__ == "__main__":
    unittest.main()
