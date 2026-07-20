import logging
from typing import Dict, Any

_logger = logging.getLogger("aiforge.learning")

class ConfidenceScorer:
    """
    Computes code artifact confidence scores based on test validation logs,
    reviewer remarks, and container compiler checks.
    """

    def __init__(self) -> None:
        pass

    def calculate_confidence(
        self,
        file_path: str,
        review_passed: bool = True,
        tests_passed: bool = True,
        deployment_passed: bool = True,
        syntax_errors_count: int = 0
    ) -> float:
        """
        Calculates confidence score (0.0 to 100.0) for a given code file.
        """
        # Base confidence starts at 60.0%
        score = 60.0

        if review_passed:
            score += 15.0  # static peer review OK
        else:
            score -= 20.0

        if tests_passed:
            score += 15.0  # passes unit verification
        else:
            score -= 25.0

        if deployment_passed:
            score += 10.0  # starts/binds correctly
        else:
            score -= 10.0

        # Syntax checks weight
        score -= (syntax_errors_count * 15.0)

        # Restrict values within bounds
        score = max(0.0, min(100.0, score))
        
        _logger.info(f"Confidence score for '{file_path}': {score:.1f}%")
        return score
