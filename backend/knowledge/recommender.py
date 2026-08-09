"""
AIForge Recommendation Engine
=============================
Analyzes project requirements and recommends proven reusable components, architectures, schemas, and deployment assets.
"""

import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.knowledge.recommender")


class RecommendationEngine:
    """
    Recommends reusable components and patterns for new projects.
    """

    def recommend_for_project(self, project_type: str = "web_app", description: str = "") -> Dict[str, Any]:
        text_lower = f"{project_type} {description}".lower()

        recommendations = [
            {"asset_name": "JWT Bearer Token Authentication", "category": "Security", "confidence": 0.98, "reusable": True},
            {"asset_name": "Production Dockerfile & Compose Template", "category": "DevOps", "confidence": 0.95, "reusable": True},
            {"asset_name": "PostgreSQL Relational Schema Blueprint", "category": "Database", "confidence": 0.92, "reusable": True},
            {"asset_name": "Structured Logging Module", "category": "Utilities", "confidence": 0.96, "reusable": True},
            {"asset_name": "10-Stage GitHub Actions CI/CD Workflow", "category": "CI/CD", "confidence": 0.94, "reusable": True}
        ]

        if "e-commerce" in text_lower or "delivery" in text_lower or "shop" in text_lower:
            recommendations.append({"asset_name": "Stripe/Razorpay Payment Gateway Adapter", "category": "Integration", "confidence": 0.90, "reusable": True})
        
        result = {
            "project_type": project_type,
            "recommended_assets_count": len(recommendations),
            "recommendations": recommendations,
            "summary": f"Recommended {len(recommendations)} proven engineering assets for {project_type}"
        }

        _logger.info(f"RecommendationEngine: Recommended {len(recommendations)} assets for '{project_type}'")
        return result


global_recommendation_engine = RecommendationEngine()
