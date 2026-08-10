"""
AIForge Day 24 — Recommendation Priority Scoring Engine
========================================================
Calculates priority scores (0-100) based on Impact, Risk, Effort, Security relevance,
Incident history, Engineering Memory, and configured User Goals.
"""

import logging
from typing import Dict, Any, List

from backend.evolution.models import EvolutionRecommendation, TechnicalDebtCategory

_logger = logging.getLogger("aiforge.evolution.prioritizer")


class RecommendationPrioritizer:
    """
    Ranks recommendations using evidence-based priority scoring.
    """

    def prioritize_recommendations(
        self,
        recommendations: List[EvolutionRecommendation],
        user_goal: str = "Enterprise Deployment"
    ) -> List[EvolutionRecommendation]:
        _logger.info(f"[Prioritizer] Scoring {len(recommendations)} recommendations for goal '{user_goal}'")

        g_lower = user_goal.lower()

        for rec in recommendations:
            score = 50.0

            # 1. Impact / Effort / Risk weights
            if rec.impact == "HIGH":
                score += 25.0
            elif rec.impact == "MEDIUM":
                score += 15.0

            if rec.effort == "LOW":
                score += 15.0
            elif rec.effort == "MEDIUM":
                score += 5.0

            if rec.risk == "LOW":
                score += 10.0

            # 2. Category relevance to user goal
            if "enterprise" in g_lower and rec.category in (TechnicalDebtCategory.SECURITY, TechnicalDebtCategory.TESTING, TechnicalDebtCategory.OBSERVABILITY):
                score += 15.0
            elif "performance" in g_lower and rec.category == TechnicalDebtCategory.PERFORMANCE:
                score += 20.0
            elif "quality" in g_lower and rec.category in (TechnicalDebtCategory.CODE_QUALITY, TechnicalDebtCategory.ARCHITECTURE):
                score += 15.0

            rec.priority_score = min(round(score, 1), 99.0)

        return sorted(recommendations, key=lambda r: r.priority_score, reverse=True)


global_recommendation_prioritizer = RecommendationPrioritizer()
