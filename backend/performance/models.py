"""
AIForge Quality Recovery & Day 18 Autonomous Performance Engineer Models
========================================================================
Typed data models for execution policy, tracing, metrics, caching, 
resilience, checkpoints, error taxonomy, and Day 18 Performance Engineering.
"""

import time
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class PipelinePath(str, Enum):
    """Execution path determined by ExecutionPolicyEngine."""
    FAST = "FAST"
    FAST_CODING = "FAST_CODING"
    STANDARD = "STANDARD"
    RETRIEVAL = "RETRIEVAL"
    REPOSITORY = "REPOSITORY"
    ENGINEERING_WORKFLOW = "ENGINEERING_WORKFLOW"


class ErrorCategory(str, Enum):
    """Standardized error taxonomy."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MODEL_ERROR = "MODEL_ERROR"
    MODEL_TIMEOUT = "MODEL_TIMEOUT"
    RETRIEVAL_ERROR = "RETRIEVAL_ERROR"
    EXECUTION_ERROR = "EXECUTION_ERROR"
    TEST_FAILURE = "TEST_FAILURE"
    REPOSITORY_ERROR = "REPOSITORY_ERROR"
    GIT_ERROR = "GIT_ERROR"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    SECURITY_BLOCK = "SECURITY_BLOCK"
    RESOURCE_LIMIT = "RESOURCE_LIMIT"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class HealthStatus(str, Enum):
    """Service health state."""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"


class RequestBudget(BaseModel):
    """Resource budget allocated to a single request."""
    max_total_ms: float = 60000.0
    max_model_calls: int = 10
    max_tool_calls: int = 20
    max_retries: int = 3
    max_review_cycles: int = 2
    max_debug_cycles: int = 2


class ExecutionPlan(BaseModel):
    """
    Deterministic execution plan output by ExecutionPolicyEngine.
    Specifies exactly which pipeline stages are enabled.
    """
    path: PipelinePath = PipelinePath.STANDARD
    use_planner: bool = True
    use_rag: bool = False
    use_repository: bool = False
    use_review: bool = True
    use_execution: bool = True
    use_tests: bool = False
    use_grounding: bool = False
    use_git: bool = False
    allow_parallel: bool = True
    model_tier: str = "standard"  # "fast", "standard", "strong"
    budgets: RequestBudget = Field(default_factory=RequestBudget)
    reasoning: str = ""


class StageTrace(BaseModel):
    """Latency and status trace for an individual pipeline stage."""
    stage: str
    started_at: float
    ended_at: Optional[float] = None
    duration_ms: float = 0.0
    status: str = "SUCCESS"  # SUCCESS, FAILED, SKIPPED, CACHED
    cache_hit: bool = False
    model: Optional[str] = None
    attempt: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RequestTrace(BaseModel):
    """Coherent request-level telemetry trace."""
    request_id: str
    session_id: Optional[str] = None
    workflow_id: Optional[str] = None
    start_time: float
    end_time: Optional[float] = None
    total_ms: float = 0.0
    status: str = "IN_PROGRESS"  # IN_PROGRESS, COMPLETED, FAILED, CANCELLED
    path: PipelinePath = PipelinePath.STANDARD
    stages: List[StageTrace] = Field(default_factory=list)
    model_calls: int = 0
    tool_calls: int = 0
    cache_hits: int = 0
    errors: List[Dict[str, Any]] = Field(default_factory=dict)


class ProgressEvent(BaseModel):
    """Progress event payload for frontend telemetry."""
    request_id: str
    workflow_id: Optional[str] = None
    stage: str
    message: str
    timestamp: float = Field(default_factory=time.time)
    category: str = "INFO"  # INFO, WARNING, ERROR, SUCCESS


class AuditEvent(BaseModel):
    """Security and compliance audit event."""
    event_id: str
    request_id: str
    workflow_id: Optional[str] = None
    action: str
    result: str
    timestamp: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowCheckpoint(BaseModel):
    """Workflow state checkpoint for crash recovery."""
    workflow_id: str
    stage: str  # ANALYZED, PLANNED, PATCHED, TESTED, REVIEWED, COMMITTED
    state_reference: Dict[str, Any] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)
    version: str = "1.0"
    repository_fingerprint: str = ""


# =========================================================================
# Day 18 — Autonomous Performance Engineer Models
# =========================================================================

class PerformanceSnapshot(BaseModel):
    snapshot_id: str
    project_id: str
    generation_id: str = "aiforge-demo"
    version: int = 1
    timestamp: str = ""
    api_latency_ms: float = 420.0
    p95_latency_ms: float = 610.0
    throughput_req_sec: float = 84.0
    error_rate_percent: float = 0.0
    bundle_size_mb: float = 2.8
    db_query_count: int = 34
    db_latency_ms: float = 240.0
    memory_usage_mb: float = 412.0
    cpu_usage_percent: float = 18.5


class PerformanceBottleneck(BaseModel):
    bottleneck_id: str
    name: str  # e.g., "N+1 database queries"
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    affected_files: List[str] = Field(default_factory=list)
    impact_summary: str
    evidence: str  # e.g., "34 queries/request"
    recommendation: str
    risk: str = "MEDIUM"


class OptimizationPlan(BaseModel):
    plan_id: str
    bottleneck_id: str
    title: str
    patch_summary: str
    affected_files: List[str] = Field(default_factory=list)
    proposed_code_changes: Dict[str, str] = Field(default_factory=dict)
    expected_latency_reduction_percent: float = 50.0


class PerformanceDiff(BaseModel):
    baseline_snapshot: PerformanceSnapshot
    optimized_snapshot: PerformanceSnapshot
    latency_improvement_percent: float = 0.0
    db_query_reduction_percent: float = 0.0
    bundle_size_reduction_percent: float = 0.0
    unit_tests_status: str = "PASS"
    security_status: str = "PASS"
    browser_status: str = "PASS"
    decision: str = "KEEP"  # KEEP, ROLLBACK


class PerformanceReport(BaseModel):
    project_id: str
    overall_performance_score: float = 88.0
    latest_snapshot: PerformanceSnapshot
    bottlenecks: List[PerformanceBottleneck] = Field(default_factory=list)
    applied_optimizations_count: int = 0
    created_at: str = ""


class PerformanceHistory(BaseModel):
    project_id: str
    snapshots: List[PerformanceSnapshot] = Field(default_factory=list)
