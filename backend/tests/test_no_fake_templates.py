"""
PyTest Unit Tests: Purge of Fake Explanation Templates & Semantic Knowledge Validation
========================================================================================
Validates that fake template headers (Overview of, Core Concept, Domain Context, Practical Applications)
are 100% eliminated and real domain knowledge is generated.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import unittest
from backend.agents.explanation_agent import ExplanationAgent


class TestNoFakeTemplates(unittest.TestCase):

    def setUp(self):
        self.agent = ExplanationAgent()

    def test_la_liga_explanation(self):
        prompt = "What is La Liga?"
        res = self.agent.process_explanation_request(prompt)
        text = res["response"]

        # Real domain knowledge assertions
        self.assertIn("Spain", text)
        self.assertIn("football", text.lower())
        self.assertIn("league", text.lower())

        # ABSOLUTE FORBIDDEN TEMPLATE STRINGS ASSERTIONS
        self.assertNotIn("Domain Context", text)
        self.assertNotIn("Core Concept", text)
        self.assertNotIn("Detailed explanation regarding", text)
        self.assertNotIn("Overview of", text)
        self.assertNotIn("Practical Applications", text)

    def test_chennai_super_kings_explanation(self):
        prompt = "WHAT IS CHENNAI SUPER KINGS"
        res = self.agent.process_explanation_request(prompt)
        text = res["response"]

        # Domain verification
        self.assertIn("Cricket", res["domain"])
        self.assertTrue(res["validation_passed"])

        # Real knowledge assertions
        self.assertIn("Chennai", text)
        self.assertIn("IPL", text)

        # ABSOLUTE FORBIDDEN TEMPLATE HEADERS ASSERTIONS
        self.assertNotIn("Domain Context", text)
        self.assertNotIn("Core Concept", text)
        self.assertNotIn("Detailed explanation regarding", text)
        self.assertNotIn("Overview of", text)
        self.assertNotIn("Practical Applications", text)
        self.assertNotIn("Comprehensive answer for", text)
        self.assertNotIn("Fundamental explanation and real-world context", text)

    def test_mumbai_indians_explanation(self):
        prompt = "WHAT IS MUMBAI INDIANS"
        res = self.agent.process_explanation_request(prompt)
        text = res["response"]

        # Domain verification
        self.assertIn("Cricket", res["domain"])
        self.assertTrue(res["validation_passed"])

        # Real knowledge assertions
        self.assertIn("Mumbai", text)
        self.assertIn("IPL", text)

        # ABSOLUTE FORBIDDEN TEMPLATE HEADERS ASSERTIONS
        self.assertNotIn("Domain Context", text)
        self.assertNotIn("Core Concept", text)
        self.assertNotIn("Detailed explanation regarding", text)
        self.assertNotIn("Overview of", text)
        self.assertNotIn("Practical Applications", text)

    def test_formula_1_explanation(self):
        prompt = "What is Formula 1?"
        res = self.agent.process_explanation_request(prompt)
        text = res["response"]

        self.assertTrue("FIA" in text or "Formula 1" in text or "racing" in text.lower())
        self.assertNotIn("Domain Context", text)
        self.assertNotIn("Core Concept", text)

    def test_binary_search_explanation(self):
        prompt = "What is Binary Search?"
        res = self.agent.process_explanation_request(prompt)
        text = res["response"]

        self.assertIn("sorted", text.lower())
        self.assertIn("O(\\log n)", text)
        self.assertNotIn("Domain Context", text)
        self.assertNotIn("Core Concept", text)

    def test_python_explanation(self):
        prompt = "What is Python?"
        res = self.agent.process_explanation_request(prompt)
        text = res["response"]

        self.assertIn("programming language", text.lower())
        self.assertNotIn("Domain Context", text)
        self.assertNotIn("Core Concept", text)

    def test_validator_template_rejection(self):
        # Testing semantic validator rejection when fake template headers are present
        fake_template_text = "## Overview of What is La Liga\n### Core Concept\nDetailed explanation regarding La Liga.\n### Domain Context"
        val = self.agent.validate_semantic_response("What is La Liga?", fake_template_text, "Sports / Football")
        self.assertFalse(val["valid"])
        self.assertIn("forbidden fake template header", val["reason"].lower())


if __name__ == "__main__":
    unittest.main()
