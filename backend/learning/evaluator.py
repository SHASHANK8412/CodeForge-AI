"""
AIForge Day 92 Project Evaluator Module
=======================================
Combines QualityScoreEvaluator and GenerationHistoryStore to evaluate project builds automatically,
passing results to pattern extraction or failure learning engines.
"""

import logging
from typing import Dict, Any, List, Optional
from backend.learning.quality_score import global_quality_evaluator
from backend.learning.history import global_history_store

_logger = logging.getLogger("aiforge.learning.evaluator")


class AutomatedProjectEvaluator:
    """
    Automated Project Evaluator.
    """

    def evaluate_and_record(
        self,
        project_name: str,
        framework: str = "React",
        backend: str = "FastAPI",
        files: Optional[Dict[str, str]] = None,
        generation_time: int = 48,
        bugs: int = 1
    ) -> Dict[str, Any]:
        _logger.info(f"AutomatedProjectEvaluator: Running evaluation pipeline for '{project_name}'...")

        eval_result = global_quality_evaluator.evaluate_project_quality(
            project_name=project_name,
            files=files
        )

        overall_score = eval_result["overall_score"]
        tests_passed = int(overall_score * 0.4)

        history_rec = global_history_store.record_history(
            project=project_name,
            framework=framework,
            backend=backend,
            score=overall_score,
            tests_passed=tests_passed,
            bugs=bugs,
            generation_time=generation_time
        )

        return {
            "project_name": project_name,
            "overall_score": overall_score,
            "score_formatted": eval_result["score_formatted"],
            "category_scores": eval_result["category_scores"],
            "passed_threshold": eval_result["passed_threshold"],
            "history_record": history_rec
        }


global_automated_evaluator = AutomatedProjectEvaluator()
