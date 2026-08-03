"""
Unit Tests for AIForge Central Output Validator
================================================
Validates all Day 4 output quality gates, deterministic checks, contract checks,
repetition scoring, prompt/traceback leak checks, false-positive resistance,
and the critical Formula 1 bad-response simulation.
"""

import sys
import unittest
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.quality.output_validator import OutputValidator
from backend.quality.validation_models import QualityConfig


class TestOutputValidator(unittest.TestCase):

    def setUp(self):
        self.validator = OutputValidator(QualityConfig())

    def test_empty_response_rejected(self):
        res = self.validator.validate("Explain Formula 1", "", intent="EXPLANATION")
        self.assertFalse(res.is_valid)
        self.assertTrue(res.should_regenerate)
        self.assertEqual(res.severity, "critical")
        self.assertIn("non_empty", res.checks)
        self.assertFalse(res.checks["non_empty"])

    def test_explanation_with_def_solve_rejected(self):
        bad_output = (
            "## Algorithmic Approach\n\n"
            "Formula 1 can be solved using the following algorithm.\n\n"
            "```python\n"
            "def solve():\n"
            "    print('Formula 1')\n"
            "```"
        )
        res = self.validator.validate("Explain Formula 1", bad_output, intent="EXPLANATION")
        self.assertFalse(res.is_valid)
        self.assertTrue(res.should_regenerate)
        self.assertIn(res.severity, ["high", "critical"])
        self.assertTrue(any("template" in issue.lower() or "contract" in issue.lower() for issue in res.issues))

    def test_explanation_natural_accepted(self):
        good_output = (
            "## What is Formula 1?\n\n"
            "**Formula 1 (F1)** is the highest class of international single-seater auto racing "
            "governed by the Fédération Internationale de l'Automobile (FIA).\n\n"
            "### Key Highlights\n"
            "- **Grand Prix Racing**: World Championship featuring 24+ Grand Prix races worldwide.\n"
            "- **Constructors**: Iconic teams including Scuderia Ferrari, Red Bull Racing, and Mercedes."
        )
        res = self.validator.validate("Explain Formula 1", good_output, intent="EXPLANATION")
        self.assertTrue(res.is_valid)
        self.assertFalse(res.should_regenerate)
        self.assertGreaterEqual(res.score, 0.75)

    def test_coding_request_with_valid_code_accepted(self):
        code_output = (
            "## Binary Search in Python\n\n"
            "```python\n"
            "def binary_search(arr: list[int], target: int) -> int:\n"
            "    left, right = 0, len(arr) - 1\n"
            "    while left <= right:\n"
            "        mid = (left + right) // 2\n"
            "        if arr[mid] == target:\n"
            "            return mid\n"
            "        elif arr[mid] < target:\n"
            "            left = mid + 1\n"
            "        else:\n"
            "            right = mid - 1\n"
            "    return -1\n"
            "```"
        )
        res = self.validator.validate("Write binary search in Python", code_output, intent="CODING")
        self.assertTrue(res.is_valid)
        self.assertFalse(res.should_regenerate)

    def test_coding_request_missing_code_penalized(self):
        text_only = "Binary search repeatedly halves the search space until the element is found."
        res = self.validator.validate("Write binary search in Python", text_only, intent="CODING")
        self.assertFalse(res.checks.get("language_match", True))
        self.assertLess(res.score, 0.85)

    def test_repetition_detected(self):
        repeated_text = "Formula 1 is racing.\n" * 10
        res = self.validator.validate("Explain Formula 1", repeated_text, intent="EXPLANATION")
        self.assertFalse(res.is_valid)
        self.assertTrue(res.should_regenerate)

    def test_unbalanced_code_fence_detected(self):
        unbalanced = "Here is Python code:\n```python\ndef add(a, b):\n    return a + b\n"
        res = self.validator.validate("Write add function in Python", unbalanced, intent="CODING")
        self.assertFalse(res.checks.get("no_truncation", True))

    def test_system_prompt_leak_detected(self):
        leaked_output = "SYSTEM PROMPT: You are AIForge's Explanation Agent. Here is the answer."
        res = self.validator.validate("Tell me a story", leaked_output, intent="GENERAL_QA")
        self.assertFalse(res.is_valid)
        self.assertTrue(res.should_regenerate)
        self.assertEqual(res.severity, "high")

    def test_raw_traceback_leak_detected(self):
        raw_traceback = (
            "Traceback (most recent call last):\n"
            "  File \"backend/main.py\", line 45, in <module>\n"
            "ConnectionRefusedError: Failed to connect to DB"
        )
        res = self.validator.validate("Search users", raw_traceback, intent="GENERAL_QA")
        self.assertFalse(res.is_valid)
        self.assertTrue(res.should_regenerate)
        self.assertEqual(res.severity, "critical")

    def test_false_positive_time_complexity_allowed(self):
        explanation = (
            "## Time Complexity Explanation\n\n"
            "Time Complexity describes how the runtime of an algorithm scales with input size n. "
            "For example, O(1) is constant time while O(n) is linear time."
        )
        res = self.validator.validate("Explain time complexity", explanation, intent="EXPLANATION")
        self.assertTrue(res.is_valid)
        self.assertFalse(res.should_regenerate)

    def test_false_positive_def_solve_context_allowed(self):
        explanation = (
            "## What is def solve() in Competitive Programming?\n\n"
            "In competitive programming, def solve() is a common convention used to group "
            "the solution logic for a single test case."
        )
        res = self.validator.validate("Explain what def solve() means in competitive programming", explanation, intent="EXPLANATION")
        self.assertTrue(res.is_valid)
        self.assertFalse(res.should_regenerate)

    def test_critical_formula_1_simulation(self):
        """CRITICAL REQUIREMENT: Formula 1 bad output simulation MUST BE REJECTED."""
        prompt = "Explain Formula 1"
        bad_model_output = (
            "## Algorithmic Approach\n\n"
            "Formula 1 can be solved using the following algorithm.\n\n"
            "```python\n"
            "def solve():\n"
            "    print('Formula 1')\n"
            "```"
        )
        bad_res = self.validator.validate(prompt, bad_model_output, intent="EXPLANATION")
        self.assertFalse(bad_res.is_valid)
        self.assertTrue(bad_res.should_regenerate)
        self.assertEqual(bad_res.severity, "high")

        good_model_output = (
            "## What is Formula 1?\n\n"
            "Formula 1 (F1) is the highest class of international single-seater auto racing."
        )
        good_res = self.validator.validate(prompt, good_model_output, intent="EXPLANATION")
        self.assertTrue(good_res.is_valid)
        self.assertFalse(good_res.should_regenerate)


if __name__ == "__main__":
    unittest.main()
