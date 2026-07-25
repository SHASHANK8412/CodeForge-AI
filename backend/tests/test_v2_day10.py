"""
AIForge V2 Day 10 Unit Test Suite
==================================
Validates:
1. Test 1: AI Resume Analyzer documentation generation (Complete README, API Reference, Setup Guide, User Manual, Mermaid diagrams)
2. Test 2: E-Commerce Platform documentation generation (Deployment Guide, DB Docs, Architecture diagrams, Release Notes)
3. Test 3: Social Media Platform documentation generation (Developer Guide, API Docs, User Manual, Sequence diagrams)
4. Documentation Validator Gate checks
"""

import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from v2.agents.documentation.agent import global_documentation_agent_v2
from v2.agents.documentation.validator import global_documentation_validator


class TestV2Day10DocumentationEngine(unittest.TestCase):

    def test_01_resume_analyzer_documentation(self):
        prompt = "Generate documentation package for an AI Resume Analyzer project."
        report = global_documentation_agent_v2.generate_documentation(prompt, project_id="test_doc_1")

        self.assertIsNotNone(report.project_name)
        self.assertGreaterEqual(len(report.files), 5)
        self.assertGreaterEqual(len(report.diagrams), 1)
        self.assertIsNotNone(report.readme_markdown)
        self.assertIsNotNone(report.developer_docs_markdown)
        self.assertEqual(report.build_status, "success")
        print("✓ Test 1: AI Resume Analyzer Documentation validated")

    def test_02_ecommerce_documentation(self):
        prompt = "Generate documentation package for an E-commerce Platform project."
        report = global_documentation_agent_v2.generate_documentation(prompt, project_id="test_doc_2")

        self.assertGreaterEqual(len(report.files), 5)
        self.assertIsNotNone(report.deployment_docs_markdown)
        self.assertIsNotNone(report.release_notes.version)
        print("✓ Test 2: E-Commerce Platform Documentation validated")

    def test_03_social_media_documentation(self):
        prompt = "Generate documentation package for a Social Media Platform project."
        report = global_documentation_agent_v2.generate_documentation(prompt, project_id="test_doc_3")

        self.assertGreaterEqual(len(report.diagrams), 1)
        self.assertIsNotNone(report.user_manual_markdown)
        print("✓ Test 3: Social Media Platform Documentation validated")

    def test_04_documentation_validator_gate(self):
        prompt = "Generate full-stack software documentation package"
        report = global_documentation_agent_v2.generate_documentation(prompt, project_id="test_doc_4")
        is_valid, issues = global_documentation_validator.validate_report(report)

        self.assertTrue(is_valid, f"Documentation validation failed with issues: {issues}")
        print("✓ Documentation Validator Gate validated")


if __name__ == "__main__":
    unittest.main()
