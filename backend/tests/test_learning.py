"""
AIForge Day 93 Test Suite: Learning Engine & Continuous Improvement
====================================================================
Tests:
✓ Project evaluated
✓ Metrics calculated
✓ Similar projects retrieved
✓ Knowledge updated
✓ Mistakes stored
✓ Best practices stored
✓ Learning score generated
✓ Recommendations generated
"""

import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from backend.learning.learner import global_master_learner
from backend.agents.learning_agent import global_learning_agent


class TestDay93LearningEngine(unittest.TestCase):

    def test_01_project_evaluated(self):
        eval_res = global_master_learner.evaluate_project("Todo App")
        self.assertIn("learning_score", eval_res)
        self.assertEqual(eval_res["project_name"], "Todo App")
        print("✓ Project evaluated")

    def test_02_metrics_calculated(self):
        metrics = global_master_learner.calculate_metrics()
        self.assertIn("projects_generated", metrics)
        self.assertIn("generation_time_sec", metrics)
        self.assertEqual(metrics["success_rate_pct"], 96.0)
        print("✓ Metrics calculated")

    def test_03_similar_projects_retrieved(self):
        similar = global_master_learner.retrieve_similar_projects("Build Netflix clone app")
        self.assertGreater(len(similar), 0)
        self.assertIn("similarity_score_pct", similar[0])
        print("✓ Similar projects retrieved")

    def test_04_knowledge_updated(self):
        train_res = global_master_learner.update_knowledge("Movie Streaming Portal", learning_score=96)
        self.assertEqual(train_res["status"], "trained")
        self.assertGreater(train_res["total_stored_projects"], 0)
        print("✓ Knowledge updated")

    def test_05_mistakes_stored(self):
        rec = global_master_learner.record_mistake(
            problem="Missing import in component / route",
            solution="Automatically add import",
            category="imports"
        )
        self.assertIn("occurrences", rec)
        self.assertGreaterEqual(rec["occurrences"], 1)
        print("✓ Mistakes stored")

    def test_06_best_practices_stored(self):
        bps = global_master_learner.get_best_practices()
        self.assertGreater(len(bps), 0)
        self.assertTrue(any(b.get("name") == "React Folder Structure" for b in bps))
        print("✓ Best practices stored")

    def test_07_learning_score_generated(self):
        score_res = global_master_learner.evaluate_project("Blog Platform")
        self.assertIn("score_formatted", score_res)
        self.assertIn("Learning Score", score_res["score_formatted"])
        print("✓ Learning score generated")

    def test_08_recommendations_generated(self):
        recs = global_master_learner.generate_recommendations(current_coverage_pct=65.0)
        self.assertIn("improvement_suggestions", recs)
        self.assertEqual(recs["expected_coverage_pct"], 92.0)
        print("✓ Recommendations generated")


def main():
    print("\n" + "="*60)
    print(" Running Day 93 Learning & Continuous Improvement Tests...")
    print("="*60 + "\n")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDay93LearningEngine)
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
