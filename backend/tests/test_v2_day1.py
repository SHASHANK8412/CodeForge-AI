"""
AIForge V2 Day 1 Unit Test Suite
=================================
Validates:
1. Centralized configuration system (LLM, DB, Redis, VectorDB, Security)
2. Structured audit logging engine
3. Inter-agent communication protocol and contract models
4. CEO Agent request evaluation and Project Specification generation
5. Project Manager Agent task decomposition
6. Asynchronous Event Bus subscription and publishing
7. Database schema models
"""

import sys
import asyncio
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from v2.configs.config import global_v2_config
from v2.logs.logger import global_v2_logger
from v2.agents.protocol import AgentRole, TaskStatus, AgentMessage
from v2.agents.ceo.ceo_agent import global_ceo_agent
from v2.agents.manager.manager_agent import global_manager_agent
from v2.events.event_bus import global_event_bus
from v2.database.schema_v2 import ProjectRecord, TaskRecord, AgentRecord


class TestV2Day1Foundation(unittest.TestCase):

    def test_01_central_config(self):
        self.assertEqual(global_v2_config.app_name, "AIForge V2 Enterprise")
        self.assertEqual(global_v2_config.version, "2.0.0")
        self.assertEqual(global_v2_config.llm.default_model, "qwen2.5-coder:latest")
        self.assertTrue(global_v2_config.redis.enabled)
        print("✓ Central Config validated")

    def test_02_structured_audit_logger(self):
        record = global_v2_logger.log_agent_action(
            agent_name="ceo",
            input_text="Build Full Stack E-Commerce App",
            output_text="ProjectSpecification generated",
            execution_time_ms=120.5,
            tokens_used=150
        )
        self.assertEqual(record["agent"], "ceo")
        self.assertEqual(record["execution_time_ms"], 120.5)
        print("✓ Enterprise Structured Logger validated")

    def test_03_ceo_and_manager_agents(self):
        spec = global_ceo_agent.evaluate_request("Build SaaS Real-Time Dashboard")
        self.assertIsNotNone(spec.project_id)
        self.assertGreaterEqual(spec.complexity_score, 1.0)

        tasks = global_manager_agent.plan_project_tasks(spec)
        self.assertGreaterEqual(len(tasks), 6)
        self.assertEqual(tasks[0].assigned_agent, AgentRole.PLANNER)
        print("✓ CEO & Project Manager Agents validated")

    def test_04_async_event_bus(self):
        received_events = []

        async def listener(event):
            received_events.append(event)

        global_event_bus.subscribe("ProjectStarted", listener)

        async def _run():
            await global_event_bus.publish("ProjectStarted", {"project_id": "p1"}, sender="ceo")

        asyncio.run(_run())
        self.assertEqual(len(received_events), 1)
        self.assertEqual(received_events[0].topic, "ProjectStarted")
        print("✓ Asynchronous Event Bus validated")

    def test_05_database_schema_models(self):
        proj = ProjectRecord(id="p100", name="Test Proj", client_prompt="Prompt", complexity_score=7.0)
        task = TaskRecord(id="t100", project_id="p100", assigned_agent="backend", title="Task 1")
        self.assertEqual(proj.name, "Test Proj")
        self.assertEqual(task.assigned_agent, "backend")
        print("✓ Database Schema ORM models validated")


if __name__ == "__main__":
    unittest.main()
