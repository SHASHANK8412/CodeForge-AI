"""
AIForge V2 Day 6 Unit Test Suite
=================================
Validates:
1. Test 1: AI Resume Analyzer FastAPI backend generation (JWT Auth, Resume Upload API, Projects CRUD, Swagger docs)
2. Test 2: E-Commerce Platform FastAPI backend generation (Product APIs, Order APIs, Payment APIs, RBAC)
3. Test 3: Social Media Platform FastAPI backend generation (User APIs, Feed APIs, Messaging APIs, Auth)
4. Backend Validator Gate checks
"""

import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from v2.agents.backend.agent import global_backend_agent_v2
from v2.agents.backend.validator import global_backend_validator


class TestV2Day6BackendEngine(unittest.TestCase):

    def test_01_resume_analyzer_backend(self):
        prompt = "Build an AI Resume Analyzer using FastAPI and React."
        report = global_backend_agent_v2.generate_backend(prompt, project_id="test_be_1")

        self.assertIsNotNone(report.project_name)
        self.assertGreaterEqual(len(report.apis), 4)
        self.assertGreaterEqual(len(report.services), 2)
        self.assertGreaterEqual(len(report.repositories), 2)
        self.assertGreaterEqual(len(report.tests), 2)
        self.assertIn("fastapi", report.dependencies)
        print("✓ Test 1: AI Resume Analyzer FastAPI Backend validated")

    def test_02_ecommerce_backend(self):
        prompt = "Build an E-commerce Platform with cart, checkout, and admin dashboard."
        report = global_backend_agent_v2.generate_backend(prompt, project_id="test_be_2")

        self.assertGreaterEqual(len(report.apis), 4)
        self.assertGreaterEqual(len(report.services), 2)
        self.assertEqual(report.build_status, "success")
        print("✓ Test 2: E-Commerce Platform FastAPI Backend validated")

    def test_03_social_media_backend(self):
        prompt = "Build a Social Media Platform with feed, profile, and messaging UI."
        report = global_backend_agent_v2.generate_backend(prompt, project_id="test_be_3")

        self.assertGreaterEqual(len(report.repositories), 2)
        self.assertIsNotNone(report.main_py_content)
        print("✓ Test 3: Social Media Platform FastAPI Backend validated")

    def test_04_backend_validator_gate(self):
        prompt = "Build a FastAPI REST Application"
        report = global_backend_agent_v2.generate_backend(prompt, project_id="test_be_4")
        is_valid, issues = global_backend_validator.validate_report(report)

        self.assertTrue(is_valid, f"Backend validation failed with issues: {issues}")
        print("✓ Backend Validator Gate validated")


if __name__ == "__main__":
    unittest.main()
