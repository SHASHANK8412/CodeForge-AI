"""
Unit tests for Day 46 AlertEngine and Autonomous Operations
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import unittest
from backend.monitoring.alerts import AlertEngine


class TestAlerts(unittest.TestCase):

    def setUp(self):
        self.alerts = AlertEngine()

    def test_alert_threshold_and_remediation(self):
        metrics_high_mem = {"memory_usage_mb": 1200, "agent_latency_avg_ms": 200}
        alts = self.alerts.evaluate_system_alerts(metrics_high_mem)
        self.assertEqual(len(alts), 1)
        self.assertEqual(alts[0]["severity"], "CRITICAL")
        self.assertEqual(alts[0]["auto_remediation"], "RESTART_WORKER_AND_RESUME")

        rec = self.alerts.trigger_autonomous_recovery("HIGH_MEMORY")
        self.assertEqual(rec["status"], "RECOVERED")


if __name__ == "__main__":
    unittest.main()
