"""
AIForge V2 Day 3 Unit Test Suite
=================================
Validates:
1. Test 1: Medium complexity product blueprint generation ("Build an AI Resume Analyzer")
2. Test 2: Enterprise complexity product blueprint generation ("Build an Uber-like ride-sharing platform")
3. Test 3: Low complexity product blueprint generation ("Build a Calculator App")
4. Planner Report Validator gate checks
5. Planner Service requirement pipeline integration
"""

import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from v2.agents.planner.agent import global_planner_agent_v2
from v2.agents.planner.planner_service import global_planner_service
from v2.agents.planner.validator import global_planner_validator


class TestV2Day3PlannerEngine(unittest.TestCase):

    def test_01_medium_resume_analyzer_blueprint(self):
        prompt = "Build an AI Resume Analyzer"
        report = global_planner_agent_v2.generate_blueprint(prompt, project_id="test_p1")

        self.assertIsNotNone(report.business_analysis.business_goal)
        self.assertGreaterEqual(len(report.functional_requirements), 2)
        self.assertGreaterEqual(len(report.user_stories), 1)
        self.assertGreaterEqual(len(report.sprint_plan), 1)
        self.assertGreaterEqual(len(report.risk_analysis), 1)
        print("✓ Test 1: Medium Complexity AI Resume Analyzer Blueprint validated")

    def test_02_enterprise_ubersharing_blueprint(self):
        prompt = "Build an Uber-like ride-sharing platform with payments and driver tracking."
        report = global_planner_agent_v2.generate_blueprint(prompt, project_id="test_p2")

        self.assertGreaterEqual(len(report.functional_requirements), 2)
        self.assertGreaterEqual(len(report.risk_analysis), 1)
        self.assertIn("React", report.tech_recommendations[0].technology + " " + report.tech_recommendations[1].technology)
        print("✓ Test 2: Enterprise Complexity Ride-Sharing Blueprint validated")

    def test_03_low_calculator_blueprint(self):
        prompt = "Build a Calculator App"
        report = global_planner_agent_v2.generate_blueprint(prompt, project_id="test_p3")

        self.assertIsNotNone(report.project_name)
        self.assertGreaterEqual(len(report.functional_requirements), 1)
        print("✓ Test 3: Low Complexity Calculator Blueprint validated")

    def test_04_validator_gate(self):
        prompt = "Build an AI-powered e-commerce platform with recommendations, payments, analytics, and admin dashboard."
        report = global_planner_service.analyze_project(prompt, project_id="test_p4")
        is_valid, issues = global_planner_validator.validate_report(report)

        self.assertTrue(is_valid, f"Report validation failed with issues: {issues}")
        print("✓ Report Validator Gate validated")


if __name__ == "__main__":
    unittest.main()
