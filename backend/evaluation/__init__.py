"""
AIForge Evaluation & Autonomous Self-Repair Engine Package
"""

from backend.evaluation.models import (
    EvaluationScoreBreakdown,
    EvaluationTestSummary,
    ProjectEvaluationResult,
    EvaluateProjectRequest
)
from backend.evaluation.scoring import ProjectScoreCalculator, global_project_score_calculator
from backend.evaluation.test_runner import EvaluationTestRunner, global_evaluation_test_runner
from backend.evaluation.repair_engine import AutonomousSelfRepairEngine, global_self_repair_engine
from backend.evaluation.evaluator import ProjectEvaluator, global_project_evaluator

__all__ = [
    "EvaluationScoreBreakdown",
    "EvaluationTestSummary",
    "ProjectEvaluationResult",
    "EvaluateProjectRequest",
    "ProjectScoreCalculator",
    "global_project_score_calculator",
    "EvaluationTestRunner",
    "global_evaluation_test_runner",
    "AutonomousSelfRepairEngine",
    "global_self_repair_engine",
    "ProjectEvaluator",
    "global_project_evaluator",
]
