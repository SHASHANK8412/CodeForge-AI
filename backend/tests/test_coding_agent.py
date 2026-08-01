"""
Unit tests for CodingAgent
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import unittest
from backend.agents.coding_agent import CodingAgent


class TestCodingAgent(unittest.TestCase):

    def setUp(self):
        self.agent = CodingAgent()

    def test_binary_search_response(self):
        res = self.agent.process_coding_request("BINARY SEARCH CODE")
        self.assertIn("def binary_search", res["response"])
        self.assertIn("O(\\log n)", res["response"])
        self.assertEqual(res["intent"], "CODING")


if __name__ == "__main__":
    unittest.main()
