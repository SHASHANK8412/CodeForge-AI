"""
Unit tests for Day 48 AI Project Refactoring Engine
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import unittest
from backend.refactoring.quality_scorer import QualityScorer
from backend.refactoring.refactoring_agent import RefactoringAgent


class TestDay48Refactoring(unittest.TestCase):

    def setUp(self):
        self.scorer = QualityScorer()
        self.agent = RefactoringAgent()

    def test_quality_scorer(self):
        sample_files = {"main.py": "def test(): pass"}
        res = self.scorer.evaluate_quality(sample_files)
        self.assertGreaterEqual(res["overall_score"], 80.0)

    def test_refactoring_agent(self):
        sample_files = {"main.py": "def process(): return True"}
        res = self.agent.refactor_project(sample_files)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertGreater(res["after_score"], res["before_score"])


if __name__ == "__main__":
    unittest.main()
