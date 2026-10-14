"""
AIForge Day 16 — Configurable Evaluation Criteria Engine
=========================================================
Default Criteria Weights:
- Requirements Fit:       25%
- Scalability:            15%
- Security:               15%
- Maintainability:       15%
- Performance:            10%
- Complexity:             10%
- Cost:                    5%
- AIForge Compatibility:   5%
"""

from typing import Dict, Any

DEFAULT_CRITERIA_WEIGHTS: Dict[str, float] = {
    "requirements_fit": 0.25,
    "scalability": 0.15,
    "security": 0.15,
    "maintainability": 0.15,
    "performance": 0.10,
    "complexity": 0.10,
    "cost": 0.05,
    "aiforge_fit": 0.05,
}


class CriteriaEngine:
    """
    Calculates weighted architecture scores.
    """

    def calculate_total_score(
        self,
        req_fit: float,
        scalability: float,
        security: float,
        maintainability: float,
        perf: float,
        complexity: float,
        cost: float,
        aiforge_fit: float,
        weights: Dict[str, float] = None
    ) -> float:
        w = weights or DEFAULT_CRITERIA_WEIGHTS
        total = (
            req_fit * w["requirements_fit"] +
            scalability * w["scalability"] +
            security * w["security"] +
            maintainability * w["maintainability"] +
            perf * w["performance"] +
            complexity * w["complexity"] +
            cost * w["cost"] +
            aiforge_fit * w["aiforge_fit"]
        )
        return round(total, 1)


global_criteria_engine = CriteriaEngine()
