"""
AIForge Benchmark Lab — Data Models & Schemas
==============================================
Defines tasks, configurations, metrics, run records, comparisons, and recommendations.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class TaskDifficulty(str, Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class TaskCategory(str, Enum):
    GENERATION = "GENERATION"
    BUG_FIX = "BUG_FIX"
    REFACTORING = "REFACTORING"
    FEATURE_ADDITION = "FEATURE_ADDITION"
    VALIDATION = "VALIDATION"
    DOCUMENTATION = "DOCUMENTATION"


class WorkflowType(str, Enum):
    DIRECT = "DIRECT"
    PLANNER_CODER = "PLANNER_CODER"
    PLANNER_CODER_REVIEWER = "PLANNER_CODER_REVIEWER"
    FULL_PIPELINE = "FULL_PIPELINE"


class BenchmarkTask(BaseModel):
    id: str
    name: str
    description: str
    category: TaskCategory = TaskCategory.GENERATION
    difficulty: TaskDifficulty = TaskDifficulty.MEDIUM
    language: str = "python"
    framework: str = "pytest"
    template: str = "python-standard"
    requirements: List[str] = Field(default_factory=list)
    required_artifacts: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)
    timeout_seconds: float = 30.0
    initial_files: Dict[str, str] = Field(default_factory=dict)
    validation_procedure: str = "pytest"
    hidden_test_files: Dict[str, str] = Field(default_factory=dict)


class BenchmarkConfig(BaseModel):
    id: str
    name: str
    provider: str = "Ollama"
    model_name: str = "qwen2.5-coder:latest"
    prompt_version: str = "v1.0"
    workflow: WorkflowType = WorkflowType.FULL_PIPELINE
    review_enabled: bool = True
    testing_enabled: bool = True
    max_repair_attempts: int = 3
    timeout_seconds: float = 60.0
    temperature: float = 0.2
    num_ctx: int = 8192
    is_available: bool = True
    availability_reason: Optional[str] = None


class TaskMetricScores(BaseModel):
    functional_correctness: float = 0.0  # 0 to 100
    tests_passed: int = 0
    tests_total: int = 0
    build_success: bool = False
    requirement_adherence: float = 0.0  # 0 to 100
    criteria_met: int = 0
    criteria_total: int = 0
    code_quality: float = 0.0  # 0 to 100
    syntax_valid: bool = False
    lint_clean: bool = False
    type_check_passed: bool = False
    reliability: float = 0.0  # 0 to 100
    repair_attempts: int = 0
    regressions: int = 0
    duration_seconds: float = 0.0
    model_time_seconds: float = 0.0
    test_time_seconds: float = 0.0
    model_calls: int = 0
    token_count: Optional[int] = None
    overall_score: float = 0.0  # 0 to 100


class TaskRunResult(BaseModel):
    task_id: str
    task_name: str
    config_id: str
    run_iteration: int = 1
    status: str = "PENDING"  # PENDING, RUNNING, COMPLETED, FAILED, TIMED_OUT, CANCELLED, NOT_RUN
    metrics: TaskMetricScores = Field(default_factory=TaskMetricScores)
    generated_files: Dict[str, str] = Field(default_factory=dict)
    validation_stdout: str = ""
    validation_stderr: str = ""
    error_message: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class EvaluationPriority(str, Enum):
    MAX_CORRECTNESS = "MAX_CORRECTNESS"
    FASTEST_EXECUTION = "FASTEST_EXECUTION"
    LOWEST_RESOURCES = "LOWEST_RESOURCES"
    BEST_QUALITY = "BEST_QUALITY"
    BEST_OVERALL = "BEST_OVERALL"


class ComparisonWeights(BaseModel):
    correctness: float = 0.40
    adherence: float = 0.20
    quality: float = 0.15
    reliability: float = 0.15
    speed: float = 0.10


class BenchmarkRun(BaseModel):
    id: str
    name: str
    created_at: str
    status: str = "PENDING"  # PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
    configurations: List[BenchmarkConfig] = Field(default_factory=list)
    task_ids: List[str] = Field(default_factory=list)
    repeated_runs: int = 1
    priority: EvaluationPriority = EvaluationPriority.BEST_OVERALL
    weights: Optional[ComparisonWeights] = None
    results: List[TaskRunResult] = Field(default_factory=list)
    aggregate_metrics: Dict[str, Any] = Field(default_factory=dict)
    comparison: Optional[Dict[str, Any]] = None
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None
    completed_at: Optional[str] = None
