"""
AIForge Review Policy
=====================
Determines when self-review and critique is justified to avoid unnecessary LLM overhead
and prevent uncontrolled reflection loops.
"""

import os
import logging
from typing import Optional, Any
from backend.review.models import ReviewDecision

_logger = logging.getLogger("aiforge.review.policy")


class ReviewPolicy:
    """
    Centralized policy engine controlling when ResponseCritic should be invoked.
    """

    def __init__(self):
        self.enabled = os.environ.get("AIFORGE_SELF_REVIEW_ENABLED", "true").lower() in ["true", "1", "yes"]

    def should_review(
        self,
        intent: str,
        complexity_level: str,
        execution_strategy: str,
        validation_result: Optional[Any] = None,
        task_metadata: Optional[dict] = None
    ) -> ReviewDecision:
        enabled = os.environ.get("AIFORGE_SELF_REVIEW_ENABLED", "true").lower() in ["true", "1", "yes"]
        if not enabled:
            return ReviewDecision(should_review=False, reason="FEATURE_DISABLED", priority="none")

        # Policy Rule 1: DIRECT strategy -> NEVER REVIEW (e.g., "What is Python?", "What is REST?")
        if execution_strategy == "DIRECT":
            return ReviewDecision(should_review=False, reason="DIRECT_STRATEGY", priority="none")

        # Policy Rule 2: WORKFLOW strategy -> Handled at project workflow boundaries
        if execution_strategy == "WORKFLOW":
            return ReviewDecision(should_review=False, reason="WORKFLOW_MANAGED", priority="none")

        # Policy Rule 3: PLANNED strategy -> ALWAYS REVIEW
        if execution_strategy == "PLANNED":
            return ReviewDecision(should_review=True, reason="PLANNED_EXECUTION", priority="high")

        # Policy Rule 4: COMPLEX task level -> ALWAYS REVIEW
        if complexity_level in ["MODERATE", "COMPLEX"]:
            return ReviewDecision(should_review=True, reason="COMPLEX_TASK", priority="medium")

        # Policy Rule 5: STANDARD strategy with Borderline Quality Score (< 0.85) -> REVIEW
        if validation_result and hasattr(validation_result, "score"):
            if validation_result.score < 0.85:
                return ReviewDecision(should_review=True, reason="BORDERLINE_QUALITY", priority="medium")

        # Policy Rule 6: STANDARD strategy with Strong Quality Score (>= 0.85) -> NO REVIEW
        return ReviewDecision(should_review=False, reason="STRONG_STANDARD_RESPONSE", priority="none")


global_review_policy = ReviewPolicy()
