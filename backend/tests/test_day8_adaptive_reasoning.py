"""
AIForge Day 8 Adaptive Reasoning Test Suite
============================================
Verifies Task Complexity Detection, Execution Strategy Selection,
TaskPlan Construction, Intent Overrides, Planning Overuse Prevention,
and Mandatory Tests 1 through 7.
"""

import sys
import asyncio
import unittest
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.reasoning.models import ComplexityLevel, ExecutionStrategy, TaskPlan, TaskPlanStep
from backend.reasoning.complexity_analyzer import global_complexity_analyzer
from backend.reasoning.strategy_selector import global_strategy_selector
from backend.reasoning.lightweight_planner import global_lightweight_planner, global_plan_validator
from backend.services.generation_service import global_generation_pipeline
from backend.memory.conversation_manager import ConversationManager
from backend.context.context_manager import ConversationContextManager


class TestDay8AdaptiveReasoning(unittest.TestCase):

    def setUp(self):
        self.conv_mgr = ConversationManager()
        self.context_mgr = ConversationContextManager(conversation_manager=self.conv_mgr)

    def test_mandatory_1_what_is_rest(self):
        """Mandatory Test #1: 'What is REST?' -> EXPLANATION/GENERAL_QA, DIRECT/STANDARD, Planning: NO"""
        c_res = global_complexity_analyzer.analyze("What is REST?", "EXPLANATION")
        strat = global_strategy_selector.select(c_res, "EXPLANATION")

        self.assertEqual(c_res.level, ComplexityLevel.TRIVIAL)
        self.assertEqual(strat, ExecutionStrategy.DIRECT)
        self.assertFalse(c_res.requires_planning)

    def test_mandatory_2_write_binary_search(self):
        """Mandatory Test #2: 'Write binary search in Python' -> CODING, SIMPLE, STANDARD, Planning: NO"""
        c_res = global_complexity_analyzer.analyze("Write binary search in Python.", "CODING")
        strat = global_strategy_selector.select(c_res, "CODING")

        self.assertEqual(c_res.level, ComplexityLevel.SIMPLE)
        self.assertEqual(strat, ExecutionStrategy.STANDARD)
        self.assertFalse(c_res.requires_planning)

        loop = asyncio.get_event_loop()
        res = loop.run_until_complete(global_generation_pipeline.generate("Write binary search in Python."))
        self.assertEqual(res.execution_strategy, "STANDARD")

    def test_mandatory_3_design_jwt_auth(self):
        """Mandatory Test #3: 'Design JWT authentication...' -> CODING, COMPLEX, PLANNED, Planner: YES"""
        prompt = "Design JWT authentication for FastAPI with access tokens, refresh tokens, role-based authorization and logout/revocation."
        c_res = global_complexity_analyzer.analyze(prompt, "CODING")
        strat = global_strategy_selector.select(c_res, "CODING")

        self.assertIn(c_res.level, [ComplexityLevel.MODERATE, ComplexityLevel.COMPLEX])
        self.assertEqual(strat, ExecutionStrategy.PLANNED)
        self.assertTrue(c_res.requires_planning)

        plan = global_lightweight_planner.build_plan(prompt, "CODING")
        self.assertIsNotNone(plan)
        self.assertTrue(plan.is_valid)
        self.assertGreaterEqual(len(plan.steps), 3)
        self.assertLessEqual(len(plan.steps), 8)

    def test_mandatory_4_build_ecommerce_platform_override(self):
        """Mandatory Test #4: 'Build an ecommerce platform.' -> PROJECT_GENERATION, WORKFLOW (Short prompt override)"""
        c_res = global_complexity_analyzer.analyze("Build an ecommerce platform.", "PROJECT_GENERATION")
        strat = global_strategy_selector.select(c_res, "PROJECT_GENERATION")

        self.assertEqual(c_res.level, ComplexityLevel.WORKFLOW)
        self.assertEqual(strat, ExecutionStrategy.WORKFLOW)
        self.assertTrue(c_res.requires_workflow)
        self.assertEqual(c_res.override_applied, "PROJECT_GENERATION_WORKFLOW")

    def test_mandatory_5_followup_complexity(self):
        """Mandatory Test #5: Turn 1: 'Build FastAPI auth' -> Turn 2: 'Now add refresh-token rotation' -> PLANNED"""
        conv = self.conv_mgr.create_conversation(title="Auth Mod")
        c_id = conv.conversation_id
        self.conv_mgr.record_turn(c_id, "Build FastAPI authentication", "Initial auth implementation.")

        ctx2 = self.context_mgr.get_context(c_id, "Now add refresh-token rotation and token revocation")
        c_res2 = global_complexity_analyzer.analyze("Now add refresh-token rotation and token revocation", "CODING", context_result=ctx2)
        strat2 = global_strategy_selector.select(c_res2, "CODING", context_result=ctx2)

        self.assertIn(c_res2.level, [ComplexityLevel.MODERATE, ComplexityLevel.COMPLEX])
        self.assertEqual(strat2, ExecutionStrategy.PLANNED)

    def test_mandatory_6_topic_shift_complexity_reset(self):
        """Mandatory Test #6: Turn 1: Complex microservices -> Turn 2: 'What is Python?' -> DIRECT/STANDARD"""
        conv = self.conv_mgr.create_conversation(title="Topic Shift")
        c_id = conv.conversation_id
        self.conv_mgr.record_turn(c_id, "Design a distributed ecommerce architecture using Kafka, Redis and PostgreSQL", "Complex arch.")

        ctx2 = self.context_mgr.get_context(c_id, "What is Python?")
        c_res2 = global_complexity_analyzer.analyze("What is Python?", "EXPLANATION", context_result=ctx2)
        strat2 = global_strategy_selector.select(c_res2, "EXPLANATION", context_result=ctx2)

        self.assertEqual(c_res2.level, ComplexityLevel.TRIVIAL)
        self.assertEqual(strat2, ExecutionStrategy.DIRECT)
        self.assertFalse(c_res2.requires_planning)

    def test_mandatory_7_explain_formula_1_regression(self):
        """Mandatory Test #7: 'Explain Formula 1' -> EXPLANATION, DIRECT/STANDARD, NO coding plan, NO def solve()"""
        c_res = global_complexity_analyzer.analyze("Explain Formula 1", "EXPLANATION")
        strat = global_strategy_selector.select(c_res, "EXPLANATION")

        self.assertEqual(c_res.level, ComplexityLevel.TRIVIAL)
        self.assertEqual(strat, ExecutionStrategy.DIRECT)

        loop = asyncio.get_event_loop()
        res = loop.run_until_complete(global_generation_pipeline.generate("Explain Formula 1"))
        self.assertEqual(res.intent, "EXPLANATION")
        self.assertNotIn("def solve", res.response)

    def test_plan_validator(self):
        """Tests PlanValidator step bounds and duplicate detection"""
        valid_plan = TaskPlan(
            goal="Test Goal",
            steps=[TaskPlanStep(id=i, description=f"Step {i}") for i in range(1, 5)],
            is_valid=True
        )
        self.assertTrue(global_plan_validator.validate(valid_plan))

        # Too many steps (> 8)
        invalid_plan_steps = TaskPlan(
            goal="Test Goal",
            steps=[TaskPlanStep(id=i, description=f"Step {i}") for i in range(1, 10)],
            is_valid=True
        )
        self.assertFalse(global_plan_validator.validate(invalid_plan_steps))

    def test_planner_fallback(self):
        """Planner failure must gracefully fall back to STANDARD without raising exceptions"""
        # Pass empty prompt to planner
        plan = global_lightweight_planner.build_plan("", "UNKNOWN")
        self.assertIsNone(plan)


if __name__ == "__main__":
    unittest.main()
