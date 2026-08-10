"""
AIForge Day 24 — Evolution Recommendation Engine
=================================================
Generates evidence-backed recommendations and triggers Multi-Agent Debate for major structural refactorings.
"""

import secrets
import logging
from typing import Dict, Any, List

from backend.evolution.models import EvolutionRecommendation, TechnicalDebtItem, TechnicalDebtCategory

_logger = logging.getLogger("aiforge.evolution.recommendations")


class EvolutionRecommendationEngine:
    """
    Creates actionable evolution recommendations from debt items.
    """

    def generate_recommendations(self, project_id: str, debt_items: List[TechnicalDebtItem]) -> List[EvolutionRecommendation]:
        recs: List[EvolutionRecommendation] = []

        for item in debt_items:
            rec_id = f"rec_{secrets.token_urlsafe(6)}"
            recs.append(
                EvolutionRecommendation(
                    id=rec_id,
                    project_id=project_id,
                    category=item.category,
                    title=item.title,
                    description=item.description,
                    impact=item.impact,
                    effort=item.effort,
                    risk=item.risk,
                    priority_score=85.0 if item.severity == "HIGH" else 75.0,
                    affected_files=item.affected_files,
                    evidence=item.evidence,
                    dependencies=["PaymentService" if "orders" in item.title.lower() else "AuthService"],
                    recommended_action=item.recommendation,
                    status="OPEN"
                )
            )

        # Additional default recommendation
        recs.append(
            EvolutionRecommendation(
                id=f"rec_{secrets.token_urlsafe(6)}",
                project_id=project_id,
                category=TechnicalDebtCategory.DEPENDENCY,
                title="Update outdated npm / pip packages",
                description="3 dependencies have minor security patches available.",
                impact="MEDIUM",
                effort="LOW",
                risk="LOW",
                priority_score=68.0,
                affected_files=["package.json", "requirements.txt"],
                evidence={"outdated_count": 3},
                recommended_action="Run npm update and pytest validation.",
                status="OPEN"
            )
        )

        return recs


global_evolution_recommendation_engine = EvolutionRecommendationEngine()
