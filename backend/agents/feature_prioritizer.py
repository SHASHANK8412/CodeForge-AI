"""
AIForge Day 83 Feature Prioritizer Agent
========================================
Categorizes product features using MoSCoW framework (Must Have, Should Have, Could Have) for MVP product launches.
"""

import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.agents")


class FeaturePrioritizerAgent:
    """
    Prioritizes product features using MoSCoW methodology.
    """

    def prioritize_features(self, product_name: str) -> Dict[str, Any]:
        _logger.info(f"FeaturePrioritizerAgent categorizing features for '{product_name}'")

        must_have = [
            "User Authentication & Role-based Authorization",
            "Core Workspace / Booking Management Engine",
            "Stripe Payment Gateway Integration",
            "User & Admin Management Dashboard"
        ]

        should_have = [
            "Real-time Email & In-App Notifications",
            "Analytics Dashboard & Usage Metrics",
            "PDF Export & Invoice Generation"
        ]

        could_have = [
            "AI-Powered Smart Recommendations",
            "Multi-language i18n Internationalization",
            "Custom Dark Mode Theme Switcher"
        ]

        return {
            "product_name": product_name,
            "must_have": must_have,
            "should_have": should_have,
            "could_have": could_have,
            "mvp_features_count": len(must_have)
        }


global_feature_prioritizer = FeaturePrioritizerAgent()
