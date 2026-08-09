"""
Unit tests for Day 46 DistributedTracingEngine
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import unittest
from backend.monitoring.tracing import DistributedTracingEngine


class TestTracing(unittest.TestCase):

    def setUp(self):
        self.tracing = DistributedTracingEngine()

    def test_trace_creation_and_span_recording(self):
        trace_id = "trc_test_99"
        self.tracing.start_trace(trace_id, "TestWorkflow")
        span = self.tracing.record_agent_span(trace_id, "PlannerAgent", duration_ms=125.0, tokens=80)
        self.assertEqual(span["agent"], "PlannerAgent")

        fetched = self.tracing.get_trace(trace_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(len(fetched[0]["spans"]), 1)


if __name__ == "__main__":
    unittest.main()
