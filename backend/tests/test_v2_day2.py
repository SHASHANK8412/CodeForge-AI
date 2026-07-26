"""
AIForge V2 Day 2 Test Suite
============================
Validates:
1. Test 1: Medium complexity project evaluation ("Build an AI Resume Analyzer using FastAPI and React.")
2. Test 2: Enterprise complexity project evaluation ("Build a social media platform similar to Instagram.")
3. Test 3: Low complexity project evaluation ("Create a calculator app.")
4. Project Manager Agent task breakdown and priority mapping
5. Inter-Agent Dispatcher message routing
"""

import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from v2.agents.ceo.agent import global_ceo_agent_v2
from v2.agents.ceo.models import ComplexityTier
from v2.agents.manager.agent import global_manager_agent_v2
from v2.core.message import CoreAgentMessage
from v2.core.dispatcher import global_event_dispatcher


class TestV2Day2Orchestration(unittest.TestCase):

    def test_01_medium_complexity_resume_analyzer(self):
        prompt = "Build an AI Resume Analyzer using FastAPI and React."
        evaluation = global_ceo_agent_v2.evaluate_project(prompt)
        self.assertEqual(evaluation.complexity_tier, ComplexityTier.MEDIUM)
        self.assertIn("frontend", evaluation.required_teams)
        self.assertIn("backend", evaluation.required_teams)

        tasks = global_manager_agent_v2.generate_task_breakdown(evaluation)
        self.assertGreaterEqual(len(tasks), 5)
        print("✓ Test 1: Medium Complexity AI Resume Analyzer validated")

    def test_02_enterprise_complexity_instagram(self):
        prompt = "Build a social media platform similar to Instagram."
        evaluation = global_ceo_agent_v2.evaluate_project(prompt)
        self.assertEqual(evaluation.complexity_tier, ComplexityTier.ENTERPRISE)
        self.assertGreaterEqual(evaluation.complexity_score, 8.0)
        self.assertIn("devops", evaluation.required_teams)

        tasks = global_manager_agent_v2.generate_task_breakdown(evaluation)
        self.assertGreaterEqual(len(tasks), 7)
        print("✓ Test 2: Enterprise Complexity Social Media Platform validated")

    def test_03_low_complexity_calculator(self):
        prompt = "Create a calculator app."
        evaluation = global_ceo_agent_v2.evaluate_project(prompt)
        self.assertEqual(evaluation.complexity_tier, ComplexityTier.LOW)
        self.assertLessEqual(evaluation.complexity_score, 4.0)

        tasks = global_manager_agent_v2.generate_task_breakdown(evaluation)
        self.assertLessEqual(len(tasks), 6)
        print("✓ Test 3: Low Complexity Calculator App validated")

    def test_04_event_dispatcher_routing(self):
        msg = CoreAgentMessage(
            message_id="msg_100",
            sender="ceo",
            receiver="manager",
            task_id="t1",
            payload={"action": "schedule_sprint"}
        )
        logs_before = len(global_event_dispatcher.get_log())

        import asyncio

        async def _run():
            await global_event_dispatcher.dispatch(msg)

        asyncio.run(_run())
        self.assertEqual(len(global_event_dispatcher.get_log()), logs_before + 1)
        print("✓ Inter-Agent Event Dispatcher validated")


if __name__ == "__main__":
    unittest.main()
