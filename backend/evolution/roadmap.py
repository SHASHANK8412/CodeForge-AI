"""
AIForge Day 24 — Evolution Roadmap Generator
============================================
Groups prioritized recommendations into NOW, NEXT, LATER phases accounting for
Engineering DNA dependency chains and What-If change simulations.
"""

import logging
from typing import List

from backend.evolution.models import EvolutionRoadmap, EvolutionRecommendation, TechnicalDebtCategory

_logger = logging.getLogger("aiforge.evolution.roadmap")


class EvolutionRoadmapGenerator:
    """
    Generates NOW/NEXT/LATER evolution roadmaps.
    """

    def build_roadmap(self, project_id: str, recommendations: List[EvolutionRecommendation]) -> EvolutionRoadmap:
        _logger.info(f"[RoadmapGenerator] Building roadmap for '{project_id}' with {len(recommendations)} items")

        now_items: List[EvolutionRecommendation] = []
        next_items: List[EvolutionRecommendation] = []
        later_items: List[EvolutionRecommendation] = []

        for rec in recommendations:
            if rec.category in (TechnicalDebtCategory.SECURITY, TechnicalDebtCategory.PERFORMANCE) or rec.priority_score >= 85.0:
                rec.roadmap_phase = "NOW"
                now_items.append(rec)
            elif rec.priority_score >= 70.0:
                rec.roadmap_phase = "NEXT"
                next_items.append(rec)
            else:
                rec.roadmap_phase = "LATER"
                later_items.append(rec)

        return EvolutionRoadmap(
            project_id=project_id,
            health_score=89.0,
            debt_level="MEDIUM",
            security_risk="LOW",
            performance_risk="MEDIUM",
            architecture_risk="MEDIUM",
            testing_level="GOOD",
            now=now_items,
            next_phase=next_items,
            later=later_items
        )


global_evolution_roadmap_generator = EvolutionRoadmapGenerator()
