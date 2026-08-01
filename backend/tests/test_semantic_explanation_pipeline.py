"""
PyTest Unit Tests for Explanation Agent & Semantic Relevance Validation
========================================================================
Validates domain identification, semantic relevance checking, and elimination of software engineering template fallbacks.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import unittest
from backend.agents.explanation_agent import ExplanationAgent


class TestSemanticExplanationPipeline(unittest.TestCase):

    def setUp(self):
        self.agent = ExplanationAgent()

    def test_formula_1_explanation(self):
        prompt = "WHAT IS FORMULA 1"
        res = self.agent.process_explanation_request(prompt)
        text = res["response"]

        # Domain verification
        self.assertIn("Motorsport", res["domain"])
        self.assertTrue(res["validation_passed"])

        # Topic keyword checks
        self.assertTrue("Formula 1" in text or "racing" in text.lower())

        # Must NOT contain software engineering jargon
        self.assertNotIn("microservices", text.lower())
        self.assertNotIn("data structures", text.lower())
        self.assertNotIn("software engineering", text.lower())

    def test_photosynthesis_explanation(self):
        prompt = "What is Photosynthesis?"
        res = self.agent.process_explanation_request(prompt)
        text = res["response"]

        self.assertEqual(res["domain"], "Biology")
        self.assertIn("chlorophyll", text.lower())
        self.assertNotIn("microservices", text.lower())

    def test_inflation_explanation(self):
        prompt = "What is Inflation?"
        res = self.agent.process_explanation_request(prompt)
        text = res["response"]

        self.assertEqual(res["domain"], "Economics")
        self.assertIn("prices", text.lower())
        self.assertNotIn("microservices", text.lower())

    def test_kubernetes_explanation(self):
        prompt = "What is Kubernetes?"
        res = self.agent.process_explanation_request(prompt)
        text = res["response"]

        self.assertEqual(res["domain"], "Cloud Computing")
        self.assertIn("container", text.lower())

    def test_semantic_validation_rejection(self):
        # Testing semantic validator rejection when non-tech prompt receives software engineering jargon
        bad_response = "Overview of What is Formula 1\nCore Concept\nDetailed explanation regarding Formula 1.\nDomain Context"
        val = self.agent.validate_semantic_response("WHAT IS FORMULA 1", bad_response, "Sports / Motorsport")
        self.assertFalse(val["valid"])


if __name__ == "__main__":
    unittest.main()
