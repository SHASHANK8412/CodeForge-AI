"""
AIForge Day 19 — Transparent Readiness Scoring System
======================================================
Weighted Criteria:
- Security:              20%
- Testing:               20%
- Requirements:          15%
- Performance:           10%
- Architecture:          10%
- Code Quality:          10%
- Browser Testing:        5%
- Database:               5%
- Documentation:          3%
- Deployment:             2%
"""

from typing import Dict, List
from backend.readiness.models import CheckStatus, ReadinessCheck

CATEGORY_WEIGHTS: Dict[str, float] = {
    "Security": 0.20,
    "Testing": 0.20,
    "Requirements": 0.15,
    "Performance": 0.10,
    "Architecture": 0.10,
    "Code Quality": 0.10,
    "Browser Testing": 0.05,
    "Database": 0.05,
    "Documentation": 0.03,
    "Deployment": 0.02,
}


class ReadinessScoringEngine:
    """
    Calculates weighted overall readiness score from individual category checks.
    """

    def calculate_score(self, checks: List[ReadinessCheck]) -> float:
        """Weighted average over the categories that have evidence; NOT_AVAILABLE checks and missing
        categories are left out (never assumed). 0.0 when nothing was evaluated - see evidence_coverage."""
        cat_scores: Dict[str, List[float]] = {}
        for c in checks:
            if c.status == CheckStatus.NOT_AVAILABLE:
                continue
            cat_name = c.category
            if cat_name not in cat_scores:
                cat_scores[cat_name] = []
            cat_scores[cat_name].append(c.score)

        weighted_total = 0.0
        weight_sum = 0.0

        for cat, weight in CATEGORY_WEIGHTS.items():
            if cat in cat_scores:
                avg_cat = sum(cat_scores[cat]) / len(cat_scores[cat])
                weighted_total += avg_cat * weight
                weight_sum += weight

        if weight_sum > 0:
            final_score = weighted_total / weight_sum
            return round(final_score, 1)

        return 0.0

    def evidence_coverage(self, checks: List[ReadinessCheck]) -> float:
        """Share (0-100) of the scoring weight that is backed by evidence."""
        evaluated = {c.category for c in checks if c.status != CheckStatus.NOT_AVAILABLE}
        return round(100.0 * sum(w for cat, w in CATEGORY_WEIGHTS.items() if cat in evaluated) / sum(CATEGORY_WEIGHTS.values()), 1)


global_scoring_engine = ReadinessScoringEngine()
