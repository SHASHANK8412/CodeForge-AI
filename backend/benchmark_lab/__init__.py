"""
AIForge Benchmark Lab
=====================
Automated evaluation, comparison, and optimization of AI software engineering workflows.
"""

from backend.benchmark_lab.models import (
    BenchmarkTask,
    BenchmarkConfig,
    BenchmarkRun,
    TaskRunResult,
    TaskDifficulty,
    TaskCategory,
    WorkflowType,
    EvaluationPriority,
)
from backend.benchmark_lab.tasks.library import get_all_tasks, get_task_by_id, ALL_BENCHMARK_TASKS
from backend.benchmark_lab.config_manager import global_config_manager
from backend.benchmark_lab.engine import global_benchmark_engine
from backend.benchmark_lab.evaluator import global_objective_evaluator
from backend.benchmark_lab.comparator import global_config_comparator
from backend.benchmark_lab.recommender import global_benchmark_recommender
from backend.benchmark_lab.reporter import global_benchmark_reporter
from backend.benchmark_lab.store import global_benchmark_store
from backend.benchmark_lab.routes import router as benchmark_lab_router

__all__ = [
    "BenchmarkTask",
    "BenchmarkConfig",
    "BenchmarkRun",
    "TaskRunResult",
    "TaskDifficulty",
    "TaskCategory",
    "WorkflowType",
    "EvaluationPriority",
    "get_all_tasks",
    "get_task_by_id",
    "ALL_BENCHMARK_TASKS",
    "global_config_manager",
    "global_benchmark_engine",
    "global_objective_evaluator",
    "global_config_comparator",
    "global_benchmark_recommender",
    "global_benchmark_reporter",
    "global_benchmark_store",
    "benchmark_lab_router",
]
