"""
PyTest Unit Tests for P0 Intelligent Algorithm Execution Pipeline & Output Validation
========================================================================================
Validates that algorithms generate clean, accurate code, correct complexity, and NO placeholder templates.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import unittest
from backend.agents.coding_agent import CodingAgent
from backend.agents.router_agent import RouterAgent, IntentCategory


class TestP0CodingPipeline(unittest.TestCase):

    def setUp(self):
        self.coding_agent = CodingAgent()
        self.router = RouterAgent()

    def test_binary_search_pipeline(self):
        prompt = "Binary Search Code"
        routing = self.router.classify_intent(prompt)
        self.assertEqual(routing["intent"], IntentCategory.CODING)

        res = self.coding_agent.process_coding_request(prompt)
        text = res["response"]

        # Requirements Validation
        self.assertIn("binary_search", text)
        self.assertIn("O(\\log n)", text)
        self.assertIn("O(1)", text)

        # Must NOT contain forbidden hardcoded templates
        self.assertNotIn("sorted(data)", text)
        self.assertNotIn("def solution(", text)
        self.assertNotIn("Efficient single-file solution", text)

    def test_linked_list_insertion_pipeline(self):
        prompt = "Linked List Insertion"
        routing = self.router.classify_intent(prompt)
        self.assertEqual(routing["intent"], IntentCategory.CODING)

        res = self.coding_agent.process_coding_request(prompt)
        text = res["response"]

        # Requirements Validation
        self.assertIn("Node", text)
        self.assertIn("next", text)
        self.assertIn("insert", text.lower())

        # Must NOT contain forbidden hardcoded templates
        self.assertNotIn("sorted(data)", text)
        self.assertNotIn("def solution(", text)

    def test_merge_sort_pipeline(self):
        prompt = "Merge Sort"
        routing = self.router.classify_intent(prompt)
        self.assertEqual(routing["intent"], IntentCategory.CODING)

        res = self.coding_agent.process_coding_request(prompt)
        text = res["response"]

        self.assertIn("merge", text.lower())
        self.assertNotIn("sorted(data)", text)

    def test_bubble_sort_pipeline(self):
        prompt = "Bubble Sort"
        routing = self.router.classify_intent(prompt)
        self.assertEqual(routing["intent"], IntentCategory.CODING)

        res = self.coding_agent.process_coding_request(prompt)
        text = res["response"]

        self.assertIn("swap", text.lower())
        self.assertNotIn("sorted(data)", text)

    def test_validation_rejection(self):
        # Testing validation rule rejection
        bad_response = "def solution(data):\n    return sorted(data)"
        val = self.coding_agent.validate_output("Binary Search Code", bad_response)
        self.assertFalse(val["valid"])
        self.assertIn("forbidden", val["reason"].lower())


if __name__ == "__main__":
    unittest.main()
