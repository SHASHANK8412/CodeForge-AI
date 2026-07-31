"""
Unit tests for Day 45 ServerRegistry
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import unittest
from backend.mcp.server_registry import ServerRegistry


class TestServerRegistry(unittest.TestCase):

    def setUp(self):
        self.registry = ServerRegistry()

    def test_registered_mcp_servers(self):
        servers = self.registry.get_all_servers()
        self.assertEqual(len(servers), 12)
        self.assertIn("github", servers)
        self.assertIn("postgres", servers)

    def test_status_update(self):
        self.registry.set_server_status("docker", "offline", latency_ms=0)
        s = self.registry.get_server_status("docker")
        self.assertEqual(s["status"], "offline")


if __name__ == "__main__":
    unittest.main()
