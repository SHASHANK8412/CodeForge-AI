"""
AIForge Reinforcement Learning Style Prompt Evaluator
======================================================
Evaluates output quality of mutated prompt variants.
Applies reward & punishment scoring (Rewards: passing tests, zero bugs, fast generation, high review score;
Punishments: compilation failures, poor architecture, broken APIs). Selects winning prompt.
"""

import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.optimizer")


class PromptEvaluator:
    """
    Ranks prompt variants using RL-style reward and punishment scoring.
    """

    def evaluate_variant(
        self,
        variant_info: Dict[str, Any],
        tests_passed: bool = True,
        syntax_errors: int = 0,
        generation_time_seconds: float = 25.0,
        review_score: float = 95.0,
        is_failure_scenario: bool = False
    ) -> Dict[str, Any]:
        """
        Calculates RL score out of 100.
        """
        score = 50.0

        # Standard Performance Rewards
        if tests_passed and not is_failure_scenario:
            score += 20.0
        if syntax_errors == 0:
            score += 10.0
        if generation_time_seconds < 35.0:
            score += 5.0
        if review_score >= 90.0:
            score += 10.0

        # Complexity & Architecture Rigor rewards
        complexity = variant_info.get("complexity", "")
        if complexity == "Production SOLID":
            score += 5.0
        elif complexity == "Scalable":
            score += 2.0

        # Punishments
        if is_failure_scenario or syntax_errors > 0:
            score -= 30.0
        if not tests_passed:
            score -= 25.0

        final_score = max(0.0, min(100.0, score))
        _logger.info(f"PromptEvaluator variant '{variant_info.get('version')}' score = {final_score}")

        return {
            "version": variant_info.get("version"),
            "prompt_text": variant_info.get("prompt_text"),
            "score": final_score,
            "tests_passed": tests_passed and not is_failure_scenario,
            "review_score": review_score
        }

    def select_winning_prompt(self, evaluated_variants: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not evaluated_variants:
            return {"winning_version": "Default", "winning_prompt": "", "score": 80.0}

        sorted_vars = sorted(evaluated_variants, key=lambda x: x.get("score", 0), reverse=True)
        winner = sorted_vars[0]
        _logger.info(f"PromptEvaluator: Selected winner '{winner.get('version')}' with score {winner.get('score')}")
        return {
            "winning_version": winner.get("version"),
            "winning_prompt": winner.get("prompt_text"),
            "score": winner.get("score"),
            "all_evaluations": sorted_vars
        }
