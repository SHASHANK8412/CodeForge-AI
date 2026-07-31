import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import unittest
from backend.agents.self_healing import SelfHealingAgent
from backend.services.retry_manager import RetryManagerService


class TestSelfHealing(unittest.TestCase):

    def setUp(self):
        self.agent = SelfHealingAgent()
        self.retry_service = RetryManagerService(max_retries=3)

    def test_high_confidence_fix_application(self):
        log = "ModuleNotFoundError: No module named 'fastapi'"
        result = self.agent.attempt_fix(log)
        self.assertTrue(result["success"])
        self.assertGreaterEqual(result["confidence"], 60)
        self.assertEqual(result["status"], "FIX_APPLIED")

    def test_low_confidence_abort(self):
        log = "Unclassified random strange crash error 9821379"
        result = self.agent.attempt_fix(log)
        self.assertFalse(result["success"])
        self.assertLess(result["confidence"], 60)
        self.assertEqual(result["status"], "ABORTED_LOW_CONFIDENCE")
        self.assertIn("Diagnostic Report", result["human_readable_report"])

    def test_retry_manager_pipeline_success(self):
        log = "ModuleNotFoundError: No module named 'fastapi'"
        res = self.retry_service.run_self_healing_pipeline(log, project_id="test_proj_01")
        self.assertEqual(res["status"], "SUCCESS")
        self.assertLessEqual(res["total_retries"], 3)
        self.assertGreaterEqual(res["final_confidence"], 60)

    def test_retry_manager_pipeline_low_confidence_stop(self):
        log = "Unclassified random strange crash error 9821379"
        res = self.retry_service.run_self_healing_pipeline(log, project_id="test_proj_02")
        self.assertEqual(res["status"], "FAILED")
        self.assertEqual(res["reason"], "CONFIDENCE_BELOW_THRESHOLD")
        self.assertLess(res["final_confidence"], 60)


if __name__ == "__main__":
    unittest.main()
