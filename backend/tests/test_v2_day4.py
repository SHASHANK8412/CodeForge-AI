"""
AIForge V2 Day 4 Unit Test Suite
=================================
Validates:
1. Test 1: AI Resume Analyzer technical architecture generation (FastAPI, React, PostgreSQL, Docker)
2. Test 2: E-Commerce Platform technical architecture generation (Payment module, Inventory, Orders)
3. Test 3: Social Media Platform technical architecture generation (Feed service, WebSockets, Media storage)
4. Architecture Validator Gate checks
"""

import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from v2.agents.architect.agent import global_architect_agent_v2
from v2.agents.architect.validator import global_architecture_validator


class TestV2Day4ArchitectEngine(unittest.TestCase):

    def test_01_resume_analyzer_architecture(self):
        prompt = "Build an AI Resume Analyzer using FastAPI and React."
        report = global_architect_agent_v2.design_architecture(prompt, project_id="test_arch_1")

        self.assertIsNotNone(report.high_level_architecture)
        self.assertGreaterEqual(len(report.apis), 4)
        self.assertGreaterEqual(len(report.database.tables), 3)
        self.assertGreaterEqual(len(report.components), 3)
        self.assertIn("backend/", report.folder_structure)
        print("✓ Test 1: AI Resume Analyzer Architecture validated")

    def test_02_ecommerce_platform_architecture(self):
        prompt = "Build an E-commerce Platform with payments, inventory, and orders."
        report = global_architect_agent_v2.design_architecture(prompt, project_id="test_arch_2")

        self.assertGreaterEqual(len(report.apis), 5)
        self.assertGreaterEqual(len(report.database.tables), 4)
        self.assertEqual(report.caching.engine, "Redis")
        print("✓ Test 2: E-Commerce Platform Architecture validated")

    def test_03_social_media_architecture(self):
        prompt = "Build a Social Media Platform with feed service, messaging, and media storage."
        report = global_architect_agent_v2.design_architecture(prompt, project_id="test_arch_3")

        self.assertGreaterEqual(len(report.components), 5)
        self.assertEqual(report.vector_store.engine, "ChromaDB")
        print("✓ Test 3: Social Media Platform Architecture validated")

    def test_04_architecture_validator_gate(self):
        prompt = "Build an AI SaaS application"
        report = global_architect_agent_v2.design_architecture(prompt, project_id="test_arch_4")
        is_valid, issues = global_architecture_validator.validate_report(report)

        self.assertTrue(is_valid, f"Architecture validation failed with issues: {issues}")
        print("✓ Architecture Validator Gate validated")


if __name__ == "__main__":
    unittest.main()
