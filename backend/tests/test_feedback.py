"""
AIForge Day 96 & 97 Test Suite: Feedback & Failure Improvement
"""

import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from backend.learning.feedback import global_feedback_engine
from backend.learning.improvement_engine import global_improvement_engine


class TestFeedbackAndImprovement(unittest.TestCase):

    def test_01_record_feedback_mistake(self):
        rec = global_feedback_engine.record_mistake("Unindexed DB search column", "Add database index on search column")
        self.assertIn("occurrences", rec)
        self.assertGreaterEqual(rec["occurrences"], 1)
        print("✓ Feedback mistake recording test passed")

    def test_02_extract_lessons_learned(self):
        res = global_improvement_engine.analyze_and_extract_lessons()
        self.assertGreater(res["total_lessons_learned"], 0)
        self.assertIn("lessons", res)
        print("✓ Lessons learned extraction test passed")


if __name__ == "__main__":
    unittest.main()
