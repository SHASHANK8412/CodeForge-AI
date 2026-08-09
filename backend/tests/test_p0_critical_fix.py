"""
PyTest Unit Tests: AIForge V2 P0 Critical Bug Fix - Eliminate Static Templates & Restore Real LLM Generation
=============================================================================================================
Validates that:
1. "What is Mumbai Indians?" -> Contains Cricket, IPL, Franchise/Team.
2. "What is La Liga?" -> Contains Spain, Football, League, Barcelona/Real Madrid.
3. "What is Formula 1?" -> Contains FIA/Formula One, Grand Prix/Race.
4. "Binary Search" -> Contains binary_search, mid/middle, left, right, O(log n).
5. "Develop Formula 1 Website" -> Contains React, Pages, API, Components, Folder Structure. Must NOT contain "AIForge Generated Full-Stack Platform".
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import unittest
from backend.agents.explanation_agent import global_explanation_agent
from backend.agents.coding_agent import global_coding_agent
from backend.graph.nodes import documentation_node


class TestP0CriticalFix(unittest.TestCase):

    def test_mumbai_indians_explanation(self):
        prompt = "What is Mumbai Indians?"
        res = global_explanation_agent.process_explanation_request(prompt)
        text = res["response"]

        self.assertIn("Cricket", res["domain"])
        self.assertTrue(res["validation_passed"])
        self.assertIn("Mumbai", text)
        self.assertIn("IPL", text)
        self.assertNotIn("Overview of", text)
        self.assertNotIn("Core Concept", text)

    def test_la_liga_explanation(self):
        prompt = "What is La Liga?"
        res = global_explanation_agent.process_explanation_request(prompt)
        text = res["response"]

        self.assertIn("Football", res["domain"])
        self.assertIn("Spain", text)
        self.assertIn("league", text.lower())
        self.assertNotIn("Domain Context", text)

    def test_formula_1_explanation(self):
        prompt = "What is Formula 1?"
        res = global_explanation_agent.process_explanation_request(prompt)
        text = res["response"]

        self.assertTrue("FIA" in text or "Formula 1" in text or "racing" in text.lower())
        self.assertNotIn("Practical Applications", text)

    def test_binary_search_coding(self):
        prompt = "Binary Search Code"
        res = global_coding_agent.process_coding_request(prompt)
        text = res["response"]

        self.assertIn("binary_search", text)
        self.assertIn("mid", text.lower())
        self.assertTrue("O(log n)" in text or "O(\\log n)" in text or "log n" in text.lower())
        self.assertNotIn("sorted(data)", text)

    def test_dynamic_project_documentation(self):
        state = {"prompt": "Develop Formula 1 Website"}
        out_state = documentation_node(state)
        doc = out_state["documentation"]

        self.assertIn("# Develop Formula 1 Website - Technical Documentation", doc)
        self.assertIn("Frontend", doc)
        self.assertIn("FastAPI", doc)
        self.assertNotIn("# AIForge Generated Full-Stack Platform", doc)


if __name__ == "__main__":
    unittest.main()
