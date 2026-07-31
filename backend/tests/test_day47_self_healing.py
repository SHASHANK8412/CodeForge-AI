"""
Unit tests for Day 47 Autonomous Bug Detection & Self-Healing Pipeline
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import unittest
from backend.self_healing.debug_pipeline import DebugPipelineEngine
from backend.self_healing.build_validator import BuildValidator


class TestDay47SelfHealing(unittest.TestCase):

    def setUp(self):
        self.pipeline = DebugPipelineEngine()
        self.validator = BuildValidator()

    def test_build_validation_pass(self):
        valid_files = {"main.py": "def hello():\n    return 'world'\n"}
        res = self.validator.validate_project_build(valid_files)
        self.assertTrue(res["build_passed"])

    def test_debug_and_repair_loop(self):
        buggy_files = {"App.jsx": "export default function App() {\n  return <div>App</div>\n"}
        res = self.pipeline.run_debug_and_repair_loop(buggy_files)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertTrue(res["build_passed"])


if __name__ == "__main__":
    unittest.main()
