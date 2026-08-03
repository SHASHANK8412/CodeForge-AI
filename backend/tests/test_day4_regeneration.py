"""
Unit Tests for AIForge Regeneration Controller
================================================
Tests bounded regeneration attempts, corrective prompt generation,
and safe fallback behavior under mocked LLM outputs.
"""

import sys
import unittest
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.quality.output_validator import OutputValidator
from backend.quality.regeneration_controller import RegenerationController
from backend.quality.validation_models import QualityConfig, ValidationResult
from backend.quality.safe_fallback import get_safe_fallback_response


class TestRegenerationController(unittest.TestCase):

    def setUp(self):
        self.config = QualityConfig(max_regenerations=1)
        self.validator = OutputValidator(self.config)
        self.controller = RegenerationController(self.config)

    def test_should_regenerate_first_attempt(self):
        result = ValidationResult(
            is_valid=False,
            score=0.30,
            severity="high",
            should_regenerate=True,
            issues=["Unexpected coding template for explanation intent"]
        )
        should_regen = self.controller.should_regenerate(result, attempt=0)
        self.assertTrue(should_regen)

    def test_should_not_regenerate_when_max_attempts_exceeded(self):
        result = ValidationResult(
            is_valid=False,
            score=0.30,
            severity="high",
            should_regenerate=True,
            issues=["Unexpected coding template"]
        )
        # attempt=1 means initial generation (0) + 1 retry already attempted
        should_regen = self.controller.should_regenerate(result, attempt=1)
        self.assertFalse(should_regen)

    def test_build_corrective_prompt_preserves_original_user_prompt(self):
        user_prompt = "Explain Formula 1"
        failed_response = "def solve(): print('F1')"
        result = self.validator.validate(user_prompt, failed_response, intent="EXPLANATION")

        rules, wrapped_prompt = self.controller.build_corrective_prompt(
            user_prompt=user_prompt,
            failed_response=failed_response,
            result=result,
            intent="EXPLANATION"
        )

        self.assertIn("Explain Formula 1", wrapped_prompt)
        self.assertIn("CORRECTIVE INSTRUCTION FOR REGENERATION", wrapped_prompt)
        self.assertIn("Do NOT generate programming source code", rules)

    def test_mock_llm_regeneration_recovery_flow(self):
        """Simulate LLM generation flow: Attempt 1 bad -> Attempt 2 good -> Accepted."""
        user_prompt = "Explain Formula 1"
        attempt_1_response = (
            "## Algorithmic Approach\n\n"
            "```python\n"
            "def solve():\n"
            "    print('Formula 1')\n"
            "```"
        )

        val_1 = self.validator.validate(user_prompt, attempt_1_response, intent="EXPLANATION")
        self.assertFalse(val_1.is_valid)

        # Attempt 1 -> Regeneration allowed
        self.assertTrue(self.controller.should_regenerate(val_1, attempt=0))

        attempt_2_response = (
            "## What is Formula 1?\n\n"
            "Formula 1 is the premier category of open-wheel single-seater motorsport."
        )

        val_2 = self.validator.validate(user_prompt, attempt_2_response, intent="EXPLANATION")
        self.assertTrue(val_2.is_valid)

    def test_mock_llm_all_failed_returns_safe_fallback(self):
        """Simulate LLM generation flow: Attempt 1 bad -> Attempt 2 bad -> Safe fallback returned."""
        user_prompt = "Explain Formula 1"
        bad_response = "def solve(): print('F1')"

        val = self.validator.validate(user_prompt, bad_response, intent="EXPLANATION")
        self.assertFalse(val.is_valid)

        fallback = get_safe_fallback_response("EXPLANATION", user_prompt, val.issues)
        self.assertIn("I was unable to generate a clean explanation", fallback)
        self.assertNotIn("def solve()", fallback)


if __name__ == "__main__":
    unittest.main()
