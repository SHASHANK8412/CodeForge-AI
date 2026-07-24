"""
AIForge Day 96 & 97 Test Suite: Long-Term Project Memory Storage
"""

import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from backend.learning.project_memory import global_project_memory_store


class TestMemoryStore(unittest.TestCase):

    def test_01_store_and_retrieve_project(self):
        rec = global_project_memory_store.store_project(
            prompt="Build a SaaS Analytics Portal",
            architecture="React + FastAPI + PostgreSQL",
            review_score=96.5
        )
        self.assertIn("id", rec)
        self.assertEqual(rec["prompt"], "Build a SaaS Analytics Portal")

        projects = global_project_memory_store.get_all_projects()
        self.assertGreater(len(projects), 0)
        print("✓ Memory storage and retrieval test passed")

    def test_02_search_memory_by_query(self):
        matches = global_project_memory_store.search_projects("Analytics")
        self.assertGreater(len(matches), 0)
        self.assertIn("SaaS Analytics Portal", matches[0]["prompt"])
        print("✓ Memory search test passed")


if __name__ == "__main__":
    unittest.main()
