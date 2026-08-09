"""
Unit tests for Day 49 AI Architecture Optimizer
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import unittest
from backend.architecture.optimizer_agent import ArchitectureOptimizerAgent
from backend.architecture.cost_estimator import CostEstimator


class TestDay49Architecture(unittest.TestCase):

    def setUp(self):
        self.optimizer = ArchitectureOptimizerAgent()
        self.estimator = CostEstimator()

    def test_cost_estimator(self):
        cost = self.estimator.estimate_monthly_cost(1000000)
        self.assertGreater(cost["total_monthly_usd"], 100.0)

    def test_architecture_optimization(self):
        res = self.optimizer.optimize_architecture("Food Delivery App", 10000000)
        self.assertIn("frontend", res["recommended_stack"])
        self.assertEqual(res["target_users"], 10000000)


if __name__ == "__main__":
    unittest.main()
