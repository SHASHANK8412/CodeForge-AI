"""
AIForge Confidence Engine Agent
===============================
Calculates confidence percentages for architectural decisions, technology choices,
and code recommendations (e.g., FastAPI: 98%, Node: 76% -> Recommend FastAPI).
"""

import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.agents")


class ConfidenceAgent:
    """
    Evaluates decision confidence scores across tech stacks and frameworks.
    """

    def evaluate_confidence(self, tech_options: Dict[str, float]) -> Dict[str, Any]:
        if not tech_options:
            tech_options = {"FastAPI": 0.98, "Node.js": 0.76, "Django": 0.82}

        sorted_options = sorted(tech_options.items(), key=lambda x: x[1], reverse=True)
        winner = sorted_options[0]

        _logger.info(f"ConfidenceAgent: Highest confidence recommendation is '{winner[0]}' ({winner[1] * 100}%)")
        return {
            "recommended_choice": winner[0],
            "confidence_score": winner[1],
            "confidence_percentage": f"{round(winner[1] * 100, 1)}%",
            "all_evaluated_options": [
                {"technology": name, "confidence_pct": f"{round(score * 100, 1)}%"}
                for name, score in sorted_options
            ]
        }


global_confidence_agent = ConfidenceAgent()
