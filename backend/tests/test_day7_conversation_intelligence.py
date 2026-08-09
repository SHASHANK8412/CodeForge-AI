"""
AIForge Day 7 Multi-Turn Conversation Intelligence Test Suite
=============================================================
Verifies multi-turn context management, follow-up detection, reference resolution,
topic tracking, topic shifts, agent switching, cross-conversation isolation, and context budgeting.
"""

import sys
import asyncio
import unittest
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.memory.conversation_manager import ConversationManager
from backend.context.context_manager import ConversationContextManager, global_context_manager
from backend.context.followup_detector import global_followup_detector
from backend.context.reference_resolver import global_reference_resolver
from backend.context.topic_tracker import global_topic_tracker
from backend.services.generation_service import global_generation_pipeline


class TestDay7ConversationIntelligence(unittest.TestCase):

    def setUp(self):
        self.conv_mgr = ConversationManager()
        self.context_mgr = ConversationContextManager(conversation_manager=self.conv_mgr)

    def test_mandatory_1_explanation_followup(self):
        """Mandatory Test #1: 'Explain Formula 1' -> 'How does qualifying work?'"""
        conv = self.conv_mgr.create_conversation(title="F1 Chat")
        c_id = conv.conversation_id

        # Turn 1
        self.conv_mgr.record_turn(c_id, "Explain Formula 1", "Formula 1 is motorsport racing.")

        # Turn 2 Context
        ctx = self.context_mgr.get_context(c_id, "How does qualifying work?")
        self.assertTrue(ctx.is_follow_up)
        self.assertFalse(ctx.topic_shift)
        self.assertEqual(ctx.topic, "Formula 1")
        self.assertIn("Formula 1", ctx.resolved_prompt)

    def test_mandatory_2_coding_followup_make_it_java(self):
        """Mandatory Test #2: 'Write binary search in Python' -> 'Make it Java'"""
        conv = self.conv_mgr.create_conversation(title="Binary Search Chat")
        c_id = conv.conversation_id

        # Turn 1
        self.conv_mgr.record_turn(c_id, "Write binary search in Python", "def binary_search(arr, target): pass")

        # Turn 2 Context & Generation
        ctx = self.context_mgr.get_context(c_id, "Make it Java")
        self.assertTrue(ctx.is_follow_up)
        self.assertIn("Java", ctx.resolved_prompt)

        loop = asyncio.get_event_loop()
        res = loop.run_until_complete(global_generation_pipeline.generate("Make it Java", conversation_id=c_id))
        self.assertEqual(res.intent, "CODING")
        self.assertEqual(res.agent, "CodingAgent")

    def test_mandatory_3_agent_switching_sequence(self):
        """Mandatory Test #3: ExplanationAgent -> CodingAgent -> DebugAgent"""
        conv = self.conv_mgr.create_conversation(title="Agent Switch Chat")
        c_id = conv.conversation_id

        # Turn 1: Explanation
        self.conv_mgr.record_turn(c_id, "Explain binary search", "Binary search finds items in sorted arrays.")
        ctx1 = self.context_mgr.get_context(c_id, "Explain binary search")

        # Turn 2: Coding
        self.conv_mgr.record_turn(c_id, "Implement it in Python", "def binary_search(arr, target): pass")
        ctx2 = self.context_mgr.get_context(c_id, "Implement it in Python")
        self.assertTrue(ctx2.is_follow_up)

        # Turn 3: Debugging
        ctx3 = self.context_mgr.get_context(c_id, "Why does this fail on an empty list?")
        self.assertTrue(ctx3.is_follow_up)

        loop = asyncio.get_event_loop()
        res3 = loop.run_until_complete(global_generation_pipeline.generate("Why does this fail on an empty list?", conversation_id=c_id))
        self.assertEqual(res3.intent, "DEBUGGING")
        self.assertEqual(res3.agent, "DebugAgent")

    def test_mandatory_4_topic_shift_prevents_code_leakage(self):
        """Mandatory Test #4: 'Write merge sort in Python' -> 'Explain Formula 1' (Topic Shift)"""
        conv = self.conv_mgr.create_conversation(title="Topic Shift Chat")
        c_id = conv.conversation_id

        # Turn 1: Coding
        self.conv_mgr.record_turn(c_id, "Write merge sort in Python", "def merge_sort(arr): return arr")

        # Turn 2: Topic Shift to Formula 1
        ctx = self.context_mgr.get_context(c_id, "Explain Formula 1")
        self.assertTrue(ctx.topic_shift)
        self.assertFalse(ctx.is_follow_up)
        self.assertEqual(len(ctx.selected_messages), 0)

        loop = asyncio.get_event_loop()
        res = loop.run_until_complete(global_generation_pipeline.generate("Explain Formula 1", conversation_id=c_id))
        self.assertEqual(res.intent, "EXPLANATION")
        self.assertEqual(res.agent, "ExplanationAgent")

        # Verify no Python or merge sort in response
        resp_lower = res.response.lower()
        self.assertNotIn("def merge_sort", resp_lower)
        self.assertNotIn("def solve", resp_lower)

    def test_mandatory_5_cross_conversation_isolation(self):
        """Mandatory Test #5: Zero cross-contamination between Chat A (Python) and Chat B (Formula 1)"""
        conv_a = self.conv_mgr.create_conversation(title="Chat A Python")
        c_id_a = conv_a.conversation_id
        self.conv_mgr.record_turn(c_id_a, "Explain Python", "Python is an interpreted programming language.")

        conv_b = self.conv_mgr.create_conversation(title="Chat B Formula 1")
        c_id_b = conv_b.conversation_id
        self.conv_mgr.record_turn(c_id_b, "Explain Formula 1", "Formula 1 is motorsport racing.")

        ctx_a = self.context_mgr.get_context(c_id_a, "Explain it more simply")
        ctx_b = self.context_mgr.get_context(c_id_b, "Explain it more simply")

        self.assertIn("Python", ctx_a.resolved_prompt)
        self.assertNotIn("Formula 1", ctx_a.resolved_prompt)

        self.assertIn("Formula 1", ctx_b.resolved_prompt)
        self.assertNotIn("Python", ctx_b.resolved_prompt)

    def test_mandatory_6_long_conversation_budget_compliance(self):
        """Mandatory Test #6: 50-turn simulated conversation enforces token budget & recency selection"""
        conv = self.conv_mgr.create_conversation(title="Long Chat")
        c_id = conv.conversation_id

        # Record 50 turns
        for i in range(1, 51):
            self.conv_mgr.record_turn(c_id, f"Turn {i}: Discuss module {i}", f"Response for module {i}")

        ctx = self.context_mgr.get_context(c_id, "What about module 50?")
        self.assertLessEqual(len(ctx.selected_messages), 6)
        self.assertLessEqual(ctx.estimated_tokens, 2000)


if __name__ == "__main__":
    unittest.main()
