"""
AIForge Best Response Selector
==============================
Compares original candidate response against refined candidate response.
Ensures invalid or degraded refinements can never replace a valid original response.
"""

import logging
from typing import Tuple, Any

_logger = logging.getLogger("aiforge.review.best_response_selector")


class BestResponseSelector:
    """
    Selects the highest quality valid candidate response.
    """

    def select_best(
        self,
        original_response: str,
        original_validation: Any,
        refined_response: str,
        refined_validation: Any,
        improvement_made: bool = False
    ) -> Tuple[str, Any, str]:
        """
        Returns (best_response_text, best_validation_result, selected_source_label).
        """
        orig_valid = getattr(original_validation, "is_valid", True)
        orig_score = getattr(original_validation, "score", 0.0)

        ref_valid = getattr(refined_validation, "is_valid", False)
        ref_score = getattr(refined_validation, "score", 0.0)

        # Rule 1: Refinement was not performed or failed internally -> ORIGINAL wins
        if not improvement_made or not refined_response:
            return original_response, original_validation, "original"

        # Rule 2: Refined response failed Day 4 OutputValidator -> ORIGINAL wins
        if not ref_valid:
            _logger.warning("[BestResponseSelector] Refined response failed validation; selecting ORIGINAL response")
            return original_response, original_validation, "original"

        # Rule 3: Refined response score degraded compared to original -> ORIGINAL wins
        if ref_score < orig_score:
            _logger.info(f"[BestResponseSelector] Refined score ({ref_score}) < Original score ({orig_score}); selecting ORIGINAL response")
            return original_response, original_validation, "original"

        # Rule 4: Refined response is valid and equal or higher quality -> REFINED wins
        _logger.info(f"[BestResponseSelector] Selecting REFINED response (Refined Score: {ref_score} >= Orig Score: {orig_score})")
        return refined_response, refined_validation, "refined"


global_best_response_selector = BestResponseSelector()
