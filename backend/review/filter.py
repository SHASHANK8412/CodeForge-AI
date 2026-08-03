"""
AIForge Critique Filter
=======================
Filters out vague, stylistic, or unrequested feature demands from ResponseCritic output.
Ensures refinement instructions remain strictly scoped to original user requirements.
"""

import re
import logging
from typing import List
from backend.review.models import CritiqueResult, CritiqueIssue

_logger = logging.getLogger("aiforge.review.filter")


class CritiqueFilter:
    """
    Filters and sanitizes CritiqueResult issues.
    """

    IRRELEVANT_FEATURE_PATTERNS = [
        r"\bkubernetes\b|\bk8s\b", r"\bdocker\b", r"\bkafka\b", r"\bmicroservices\b",
        r"\baws\b", r"\bgcp\b", r"\bazure\b", r"\bgraphql\b", r"\bci/cd\b"
    ]

    VAGUE_STYLE_PATTERNS = [
        r"could be better", r"add nicer headings", r"make it prettier",
        r"more detailed comments", r"add docstrings", r"formatting could be improved"
    ]

    def filter_critique(
        self,
        user_prompt: str,
        critique: CritiqueResult
    ) -> CritiqueResult:
        if not critique or not critique.issues:
            return critique

        prompt_clean = user_prompt.lower()
        filtered_issues: List[CritiqueIssue] = []
        seen_descriptions = set()

        for issue in critique.issues:
            desc = issue.description.strip()
            desc_lower = desc.lower()

            if not desc:
                continue

            # Check 1: Deduplication
            if desc_lower in seen_descriptions:
                continue
            seen_descriptions.add(desc_lower)

            # Check 2: Reject vague style complaints
            if any(re.search(pat, desc_lower) for pat in self.VAGUE_STYLE_PATTERNS):
                _logger.info(f"[CritiqueFilter] Filtered out vague style issue: '{desc}'")
                continue

            # Check 3: Reject unrequested feature demands
            is_unrequested = False
            for pat in self.IRRELEVANT_FEATURE_PATTERNS:
                if re.search(pat, desc_lower) and not re.search(pat, prompt_clean):
                    _logger.info(f"[CritiqueFilter] Filtered out unrequested feature demand: '{desc}'")
                    is_unrequested = True
                    break

            if is_unrequested:
                continue

            filtered_issues.append(issue)

        # Update needs_revision status based on filtered issues
        has_high_or_medium = any(iss.severity in ["high", "medium"] for iss in filtered_issues)
        has_missing_reqs = len(critique.missing_requirements) > 0

        needs_rev = (len(filtered_issues) > 0 and (has_high_or_medium or has_missing_reqs or critique.score < 0.85))

        return CritiqueResult(
            needs_revision=needs_rev,
            score=critique.score,
            issues=filtered_issues,
            strengths=critique.strengths,
            missing_requirements=critique.missing_requirements,
            priority=critique.priority,
            is_valid=critique.is_valid
        )


global_critique_filter = CritiqueFilter()
