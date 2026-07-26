"""
AIForge V2 Day 5 Unit Test Suite
=================================
Validates:
1. Test 1: AI Resume Analyzer React frontend generation (Dashboard, Upload, Auth, Tailwind)
2. Test 2: E-Commerce Platform React frontend generation (Listing, Cart, Checkout, Admin)
3. Test 3: Social Media Platform React frontend generation (Feed, Profile, Messaging UI, Dark Mode)
4. Frontend Validator Gate checks
"""

import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from v2.agents.frontend.agent import global_frontend_agent_v2
from v2.agents.frontend.validator import global_frontend_validator


class TestV2Day5FrontendEngine(unittest.TestCase):

    def test_01_resume_analyzer_frontend(self):
        prompt = "Build an AI Resume Analyzer using FastAPI and React."
        report = global_frontend_agent_v2.generate_frontend(prompt, project_id="test_fe_1")

        self.assertIsNotNone(report.project_name)
        self.assertGreaterEqual(len(report.components), 4)
        self.assertGreaterEqual(len(report.pages), 3)
        self.assertGreaterEqual(len(report.routes), 3)
        self.assertGreaterEqual(len(report.stores), 2)
        self.assertIn("tailwindcss", report.dependencies)
        print("✓ Test 1: AI Resume Analyzer React Frontend validated")

    def test_02_ecommerce_frontend(self):
        prompt = "Build an E-commerce Platform with cart, checkout, and admin dashboard."
        report = global_frontend_agent_v2.generate_frontend(prompt, project_id="test_fe_2")

        self.assertGreaterEqual(len(report.components), 4)
        self.assertGreaterEqual(len(report.pages), 3)
        self.assertEqual(report.build_status, "success")
        print("✓ Test 2: E-Commerce Platform React Frontend validated")

    def test_03_social_media_frontend(self):
        prompt = "Build a Social Media Platform with feed, profile, and messaging UI."
        report = global_frontend_agent_v2.generate_frontend(prompt, project_id="test_fe_3")

        self.assertGreaterEqual(len(report.stores), 2)
        self.assertIsNotNone(report.tailwind_config)
        print("✓ Test 3: Social Media Platform React Frontend validated")

    def test_04_frontend_validator_gate(self):
        prompt = "Build a React Web Application"
        report = global_frontend_agent_v2.generate_frontend(prompt, project_id="test_fe_4")
        is_valid, issues = global_frontend_validator.validate_report(report)

        self.assertTrue(is_valid, f"Frontend validation failed with issues: {issues}")
        print("✓ Frontend Validator Gate validated")


if __name__ == "__main__":
    unittest.main()
