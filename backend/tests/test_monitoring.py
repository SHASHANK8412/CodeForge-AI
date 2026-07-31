"""
Unit tests for Day 46 MetricsCollector and SystemHealthChecker
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import unittest
from backend.monitoring.metrics import MetricsCollector
from backend.monitoring.health import SystemHealthChecker


class TestMonitoring(unittest.TestCase):

    def setUp(self):
        self.metrics = MetricsCollector()
        self.health = SystemHealthChecker()

    def test_metrics_collection(self):
        data = self.metrics.collect_system_metrics()
        self.assertIn("memory_usage_mb", data)
        self.assertIn("cpu_utilization_pct", data)
        self.assertIn("gpu_utilization_pct", data)

    def test_health_checks(self):
        h = self.health.check_all_components()
        self.assertEqual(h["status"], "healthy")
        self.assertIn("model_providers", h["components"])


if __name__ == "__main__":
    unittest.main()
