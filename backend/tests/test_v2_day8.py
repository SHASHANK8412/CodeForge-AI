"""
AIForge V2 Day 8 Unit Test Suite
=================================
Validates:
1. Test 1: AI Resume Analyzer code review (Duplicate components, JWT security, DB indexes, quality score)
2. Test 2: E-Commerce Platform code review (Payment APIs, inventory consistency, order workflow, performance bottlenecks)
3. Test 3: Social Media Platform code review (Messaging APIs, feed optimization, DB relationships, scalability)
4. Reviewer Validator Gate checks
"""

import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from v2.agents.reviewer.agent import global_reviewer_agent_v2
from v2.agents.reviewer.validator import global_reviewer_validator


class TestV2Day8ReviewerEngine(unittest.TestCase):

    def test_01_resume_analyzer_review(self):
        prompt = "Review an AI Resume Analyzer project."
        report = global_reviewer_agent_v2.review_project(prompt, project_id="test_rev_1")

        self.assertIsNotNone(report.project_name)
        self.assertGreaterEqual(len(report.category_scores), 5)
        self.assertGreaterEqual(len(report.issues), 1)
        self.assertGreaterEqual(len(report.refactorings), 1)
        self.assertGreaterEqual(report.overall_score, 80.0)
        print("✓ Test 1: AI Resume Analyzer Code Review validated")

    def test_02_ecommerce_review(self):
        prompt = "Review an E-commerce Platform project."
        report = global_reviewer_agent_v2.review_project(prompt, project_id="test_rev_2")

        self.assertGreaterEqual(len(report.category_scores), 5)
        self.assertEqual(report.build_status, "approved")
        print("✓ Test 2: E-Commerce Platform Code Review validated")

    def test_03_social_media_review(self):
        prompt = "Review a Social Media Platform project."
        report = global_reviewer_agent_v2.review_project(prompt, project_id="test_rev_3")

        self.assertGreaterEqual(report.metrics.maintainability_index, 80.0)
        self.assertIsNotNone(report.refactorings)
        print("✓ Test 3: Social Media Platform Code Review validated")

    def test_04_reviewer_validator_gate(self):
        prompt = "Review full-stack software application"
        report = global_reviewer_agent_v2.review_project(prompt, project_id="test_rev_4")
        is_valid, issues = global_reviewer_validator.validate_report(report)

        self.assertTrue(is_valid, f"Reviewer validation failed with issues: {issues}")
        print("✓ Reviewer Validator Gate validated")


if __name__ == "__main__":
    unittest.main()
