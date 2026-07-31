"""
Unit tests for Day 43 ModelManager
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import unittest
from backend.services.model_manager import ModelManager


class TestModelManager(unittest.TestCase):

    def setUp(self):
        self.manager = ModelManager()

    def test_model_registration_and_availability(self):
        self.assertTrue(self.manager.check_availability("qwen2.5-coder"))
        self.assertTrue(self.manager.check_availability("deepseek-coder"))
        self.assertTrue(self.manager.check_availability("codellama"))

    def test_task_aware_routing(self):
        self.assertEqual(self.manager.route_task("React UI"), "qwen2.5-coder")
        self.assertEqual(self.manager.route_task("Backend APIs"), "deepseek-coder")
        self.assertEqual(self.manager.route_task("SQL"), "deepseek-coder")
        self.assertEqual(self.manager.route_task("Debugging"), "codellama")

    def test_parallel_execution_and_fallback(self):
        results = self.manager.execute_models_in_parallel(
            prompt="Write a React component",
            models=["qwen2.5-coder", "deepseek-coder"],
            task_type="React UI",
            offline_models=["qwen2.5-coder"]  # Simulate Qwen offline -> trigger fallback
        )
        self.assertEqual(len(results), 2)
        # Ensure execution succeeds via fallback
        for r in results:
            self.assertEqual(r["status"], "SUCCESS")


if __name__ == "__main__":
    unittest.main()
