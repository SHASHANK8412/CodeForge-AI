"""
Unit tests for Day 43 BenchmarkTracker
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import unittest
from backend.services.benchmark import BenchmarkTracker


class TestBenchmarkTracker(unittest.TestCase):

    def setUp(self):
        self.tracker = BenchmarkTracker()

    def test_record_run_and_summary(self):
        rec = self.tracker.record_run(
            model_name="qwen2.5-coder",
            latency=2.1,
            tokens_used=150,
            quality_score=95.0,
            is_winner=True,
            is_error=False
        )
        self.assertIn("total_runs", rec)

        summary = self.tracker.get_dashboard_summary()
        self.assertIn("total_runs", summary)
        self.assertIn("overall_success_rate", summary)
        self.assertIn("model_statistics", summary)


if __name__ == "__main__":
    unittest.main()
