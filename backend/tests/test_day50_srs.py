"""
Unit tests for Day 50 AI Product Manager (Requirement Intelligence)
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import unittest
from backend.product_manager.requirement_agent import RequirementIntelligenceAgent


class TestDay50SRS(unittest.TestCase):

    def setUp(self):
        self.agent = RequirementIntelligenceAgent()

    def test_srs_generation(self):
        res = self.agent.analyze_and_generate_srs("Airbnb-like booking platform")
        self.assertIn("user_stories", res)
        self.assertGreaterEqual(len(res["functional_requirements"]), 3)
        self.assertIn("# Software Requirement Specification", res["markdown_export"])


if __name__ == "__main__":
    unittest.main()
