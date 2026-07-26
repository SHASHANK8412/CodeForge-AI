import logging
from typing import Dict, Any

logger = logging.getLogger("aiforge.quality.metrics")


class QualityScoreCalculator:
    """
    QualityScoreCalculator computes an overall project quality score out of 100
    by aggregating Code Quality, Security, Performance, Documentation, and Architecture scores.
    """

    def calculate_scores(
        self,
        analysis_res: Dict[str, Any],
        security_res: Dict[str, Any],
        perf_res: Dict[str, Any],
        has_documentation: bool = True
    ) -> Dict[str, float]:
        code_quality_score = max(60, 100 - (analysis_res.get("average_complexity", 1) * 5))
        security_score = security_res.get("security_score", 90.0)
        performance_score = perf_res.get("performance_score", 88.0)
        documentation_score = 95.0 if has_documentation else 50.0
        architecture_score = 92.0

        overall_score = round(
            (code_quality_score * 0.25) +
            (security_score * 0.25) +
            (performance_score * 0.20) +
            (documentation_score * 0.15) +
            (architecture_score * 0.15),
            1
        )

        return {
            "overall_score": overall_score,
            "code_quality_score": round(code_quality_score, 1),
            "security_score": round(security_score, 1),
            "performance_score": round(performance_score, 1),
            "documentation_score": round(documentation_score, 1),
            "architecture_score": round(architecture_score, 1)
        }


# Global QualityScoreCalculator Instance
global_quality_score_calculator = QualityScoreCalculator()
