"""
Unit tests for RouterAgent Intent Classification
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import unittest
from backend.agents.router_agent import RouterAgent, IntentCategory


class TestRouterAgent(unittest.TestCase):

    def setUp(self):
        self.router = RouterAgent()

    def test_dsa_coding_intent(self):
        res1 = self.router.classify_intent("BINARY SEARCH CODE")
        self.assertEqual(res1["intent"], IntentCategory.CODING)

        res2 = self.router.classify_intent("write quicksort algorithm in python")
        self.assertEqual(res2["intent"], IntentCategory.CODING)

    def test_explanation_intent(self):
        res = self.router.classify_intent("explain how JWT authentication works")
        self.assertEqual(res["intent"], IntentCategory.EXPLANATION)

    def test_project_generation_intent(self):
        res = self.router.classify_intent("Build a Food Delivery App with FastAPI and React")
        self.assertEqual(res["intent"], IntentCategory.PROJECT_GENERATION)


if __name__ == "__main__":
    unittest.main()
