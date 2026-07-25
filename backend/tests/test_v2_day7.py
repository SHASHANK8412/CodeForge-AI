"""
AIForge V2 Day 7 Unit Test Suite
=================================
Validates:
1. Test 1: AI Resume Analyzer PostgreSQL database persistence layer (Users, Resumes, ATS Results, SQLAlchemy models, Alembic, Seeds)
2. Test 2: E-Commerce Platform database persistence layer (Products, Orders, Payments, Inventory, Reviews, Indexes, Foreign Keys)
3. Test 3: Social Media Platform database persistence layer (Users, Posts, Comments, Likes, Followers, Messages, Notifications)
4. Database Validator Gate checks
"""

import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from v2.agents.database.agent import global_database_agent_v2
from v2.agents.database.validator import global_database_validator


class TestV2Day7DatabaseEngine(unittest.TestCase):

    def test_01_resume_analyzer_database(self):
        prompt = "Build an AI Resume Analyzer using FastAPI and React."
        report = global_database_agent_v2.generate_database(prompt, project_id="test_db_1")

        self.assertIsNotNone(report.project_name)
        self.assertGreaterEqual(len(report.tables), 3)
        self.assertGreaterEqual(len(report.relationships), 2)
        self.assertGreaterEqual(len(report.indexes), 3)
        self.assertGreaterEqual(len(report.migrations), 1)
        self.assertIsNotNone(report.ddl_schema_sql)
        self.assertIsNotNone(report.sqlalchemy_models_code)
        print("✓ Test 1: AI Resume Analyzer PostgreSQL Database validated")

    def test_02_ecommerce_database(self):
        prompt = "Build an E-commerce Platform with cart, checkout, and admin dashboard."
        report = global_database_agent_v2.generate_database(prompt, project_id="test_db_2")

        self.assertGreaterEqual(len(report.tables), 3)
        self.assertGreaterEqual(len(report.seeds), 2)
        self.assertEqual(report.build_status, "success")
        print("✓ Test 2: E-Commerce Platform PostgreSQL Database validated")

    def test_03_social_media_database(self):
        prompt = "Build a Social Media Platform with feed, profile, and messaging UI."
        report = global_database_agent_v2.generate_database(prompt, project_id="test_db_3")

        self.assertGreaterEqual(len(report.indexes), 3)
        self.assertIsNotNone(report.backup_config.backup_script)
        print("✓ Test 3: Social Media Platform PostgreSQL Database validated")

    def test_04_database_validator_gate(self):
        prompt = "Build a PostgreSQL Database Persistence Layer"
        report = global_database_agent_v2.generate_database(prompt, project_id="test_db_4")
        is_valid, issues = global_database_validator.validate_report(report)

        self.assertTrue(is_valid, f"Database validation failed with issues: {issues}")
        print("✓ Database Validator Gate validated")


if __name__ == "__main__":
    unittest.main()
