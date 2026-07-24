"""
AIForge Day 101 Test Suite: Product Manager Agent & Requirements Engine
========================================================================
Tests:
✓ Product Manager prioritizes features based on impact and effort
✓ Sentiment analysis correctly classifies user feedback
✓ Duplicate issues detected using semantic similarity
✓ Automated roadmap generation produces prioritized sprints
"""

import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from backend.agents.product_manager import global_product_manager_agent
from backend.services.feedback_service import global_feedback_service
from backend.services.roadmap_service import global_roadmap_service


class TestDay101ProductManager(unittest.TestCase):

    def test_01_sentiment_analysis(self):
        res_neg = global_feedback_service.analyze_sentiment("The app keeps crashing on dashboard load")
        self.assertEqual(res_neg["sentiment"], "Negative")
        self.assertEqual(res_neg["urgency"], "Urgent")

        res_pos = global_feedback_service.analyze_sentiment("Love the new UI features!")
        self.assertEqual(res_pos["sentiment"], "Positive")
        print("✓ Sentiment analysis test passed")

    def test_02_duplicate_issue_detection(self):
        issues = ["Login broken", "Can't sign in", "Dashboard crash"]
        dups = global_feedback_service.detect_duplicate_issues(issues)
        self.assertGreater(len(dups), 0)
        self.assertTrue(any(d["merged_count"] > 1 for d in dups))
        print("✓ Duplicate issue detection test passed")

    def test_03_business_value_scoring(self):
        bv = global_feedback_service.calculate_business_value("Dark Mode")
        self.assertEqual(bv["overall_priority"], "High")
        self.assertIn("value_score", bv)
        print("✓ Business value scoring test passed")

    def test_04_sprint_roadmap_generation(self):
        rm = global_roadmap_service.generate_sprint_roadmap(["Fix login", "Dark mode", "Notifications"])
        self.assertIn("Sprint 1", rm["roadmap"])
        self.assertIn("Sprint 2", rm["roadmap"])
        print("✓ Sprint roadmap generation test passed")

    def test_05_product_manager_agent(self):
        pm_res = global_product_manager_agent.analyze_feedback_and_plan()
        self.assertEqual(pm_res["status"], "success")
        self.assertIn("sprint_roadmap", pm_res)
        print("✓ Product Manager Agent test passed")


def main():
    print("\n" + "="*60)
    print(" Running Day 101 Product Manager Tests...")
    print("="*60 + "\n")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDay101ProductManager)
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    if result.wasSuccessful():
        print("\n" + "="*60)
        print(" ALL TESTS PASSED")
        print("="*60 + "\n")
        return True
    return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
