"""
AIForge Day 93 Learning Score Evaluator
=======================================
Calculates weighted Learning Score across 6 dimensions:
- Architecture: 30%
- Code Quality: 20%
- Tests: 20%
- Performance: 15%
- Documentation: 10%
- Security: 5%

Produces Overall Learning Score (e.g., Learning Score 94/100).
"""

import logging
from typing import Dict, Any, Optional

_logger = logging.getLogger("aiforge.learning.evaluator")


class LearningScoreEvaluator:
    """
    Weighted Learning Score Evaluator.
    """

    def evaluate_learning_score(
        self,
        project_name: str,
        architecture_score: float = 95.0,
        code_quality_score: float = 92.0,
        tests_score: float = 94.0,
        performance_score: float = 96.0,
        documentation_score: float = 90.0,
        security_score: float = 98.0
    ) -> Dict[str, Any]:
        _logger.info(f"LearningScoreEvaluator: Calculating weighted learning score for '{project_name}'...")

        weights = {
            "architecture": 0.30,
            "code_quality": 0.20,
            "tests": 0.20,
            "performance": 0.15,
            "documentation": 0.10,
            "security": 0.05
        }

        scores = {
            "architecture": max(0.0, min(100.0, architecture_score)),
            "code_quality": max(0.0, min(100.0, code_quality_score)),
            "tests": max(0.0, min(100.0, tests_score)),
            "performance": max(0.0, min(100.0, performance_score)),
            "documentation": max(0.0, min(100.0, documentation_score)),
            "security": max(0.0, min(100.0, security_score))
        }

        overall_score = round(
            sum(scores[cat] * weights[cat] for cat in weights), 1
        )

        return {
            "project_name": project_name,
            "learning_score": int(overall_score),
            "score_formatted": f"Learning Score {int(overall_score)}/100",
            "breakdown": {
                "architecture_30pct": scores["architecture"],
                "code_quality_20pct": scores["code_quality"],
                "tests_20pct": scores["tests"],
                "performance_15pct": scores["performance"],
                "documentation_10pct": scores["documentation"],
                "security_5pct": scores["security"]
            },
            "passed": overall_score >= 90.0
        }


global_learning_evaluator = LearningScoreEvaluator()
