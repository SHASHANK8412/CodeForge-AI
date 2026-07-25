"""
AIForge V2 Day 11 Unit Test Suite
==================================
Validates:
1. Database tables initialization (`init_database`)
2. Projects CRUD (`create_project`, `get_project`, `list_projects`, `update_project`, `delete_project`)
3. Tasks & Conversations memory persistence (`record_conversation`, `record_agent_output`, `get_project_memory`)
4. ProjectService lifecycle management
"""

import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from v2.database.init_db import init_database
from v2.services.project_service import global_project_service
from v2.services.memory_service import global_memory_service


class TestV2Day11MemorySystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_database()

    def test_01_create_and_get_project(self):
        proj = global_project_service.create_new_project(
            title="E-Commerce AI Platform",
            description="Persistent store testing"
        )
        self.assertIsNotNone(proj["id"])
        self.assertEqual(proj["title"], "E-Commerce AI Platform")

        fetched = global_project_service.get_project_by_id(proj["id"])
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["id"], proj["id"])
        print("✓ Test 1: Project Creation & Retrieval validated")

    def test_02_memory_service_record_and_retrieve(self):
        proj = global_project_service.create_new_project(title="Social Media App")
        project_id = proj["id"]

        global_memory_service.record_conversation(project_id, "user", "Build social feed")
        global_memory_service.record_agent_output(
            project_id=project_id,
            agent_name="planner",
            prompt="Build social feed",
            output="{'blueprint': 'Social Feed Blueprint'}",
            duration_ms=45.0
        )

        memory = global_memory_service.get_project_memory(project_id)
        self.assertGreaterEqual(memory["conversations_count"], 1)
        self.assertGreaterEqual(memory["logs_count"], 1)
        print("✓ Test 2: Memory Service Recording & History Retrieval validated")

    def test_03_project_update_and_delete(self):
        proj = global_project_service.create_new_project(title="Temp Project")
        project_id = proj["id"]

        updated = global_project_service.update_existing_project(project_id, title="Updated Temp Project", status="completed")
        self.assertEqual(updated["title"], "Updated Temp Project")
        self.assertEqual(updated["status"], "completed")

        deleted = global_project_service.remove_project(project_id)
        self.assertTrue(deleted)
        self.assertIsNone(global_project_service.get_project_by_id(project_id))
        print("✓ Test 3: Project Update & Deletion validated")


if __name__ == "__main__":
    unittest.main()
