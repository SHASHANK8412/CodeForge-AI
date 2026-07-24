"""
AIForge Day 101 Automated Roadmap Generator Service
===================================================
Generates prioritized sprint roadmaps (Sprint 1, Sprint 2, Sprint 3)
based on feature urgency, business impact, and technical complexity.
"""

import logging
from typing import Dict, Any, List, Optional
from backend.services.feedback_service import global_feedback_service

_logger = logging.getLogger("aiforge.services.roadmap")


class RoadmapService:
    """
    Automated Feature Roadmap Generator.
    """

    def generate_sprint_roadmap(self, features: List[str]) -> Dict[str, Any]:
        _logger.info(f"RoadmapService: Generating sprint roadmap for {len(features)} feature requests...")

        scored_features = []
        for f in features:
            bv = global_feedback_service.calculate_business_value(f)
            sentiment = global_feedback_service.analyze_sentiment(f)
            scored_features.append({
                "feature": f,
                "urgency": sentiment["urgency"],
                "impact": bv["business_impact"],
                "complexity": bv["technical_complexity"],
                "priority": bv["overall_priority"],
                "score": bv["value_score"]
            })

        # Sort by urgency and score
        scored_features.sort(key=lambda x: (x["urgency"] == "Urgent", x["priority"] == "High", x["score"]), reverse=True)

        sprint_1 = [f["feature"] for f in scored_features[:2]] or ["Fix login & crash bugs"]
        sprint_2 = [f["feature"] for f in scored_features[2:4]] or ["Dark mode integration"]
        sprint_3 = [f["feature"] for f in scored_features[4:]] or ["Notifications & UI Polish"]

        return {
            "total_features_planned": len(scored_features),
            "roadmap": {
                "Sprint 1": sprint_1,
                "Sprint 2": sprint_2,
                "Sprint 3": sprint_3
            },
            "backlog_queue": scored_features
        }


global_roadmap_service = RoadmapService()
