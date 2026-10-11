"""
Records of the AIForge Performance Engineer.

The states are kept apart: a static *warning* or *hypothesis* comes from reading the code; a
*measured* bottleneck comes from a workload run; an optimization is *proposed* by a plan, *applied*
by an approved execution, and *verified* only when before/after measurements support it.
Every number here comes from a run that actually happened; a metric that could not be measured is
None (never a default value).
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from backend.evolution.autopilot.models import now_iso

MAX_ENDPOINTS = 10
MAX_CONCURRENCY = 16
MAX_REQUESTS = 2000
MAX_REPETITIONS = 5


class Endpoint(BaseModel):
    method: str = "GET"
    path: str
    body: Optional[Dict[str, Any]] = None


class Workload(BaseModel):
    """What is sent to the app, identically before and after a change."""
    endpoints: List[Endpoint] = Field(default_factory=list, max_length=MAX_ENDPOINTS)
    requests_per_endpoint: int = Field(200, ge=10, le=MAX_REQUESTS)
    concurrency: int = Field(4, ge=1, le=MAX_CONCURRENCY)
    warmup_requests: int = Field(20, ge=0, le=200)
    repetitions: int = Field(3, ge=1, le=MAX_REPETITIONS)
    request_timeout_seconds: float = Field(10.0, gt=0, le=60)
    max_seconds_per_endpoint: float = Field(20.0, ge=1, le=120)   # per repetition; slow endpoints send fewer requests
    health_path: Optional[str] = None


class Thresholds(BaseModel):
    """Acceptance rules for an optimization (all configurable per plan)."""
    min_improvement_pct: float = Field(10.0, ge=1, le=90)     # median latency of the target endpoints
    max_regression_pct: float = Field(10.0, ge=1, le=200)     # any endpoint's median latency
    max_error_rate_increase_pp: float = Field(1.0, ge=0, le=100)
    max_memory_increase_pct: float = Field(20.0, ge=0, le=500)
    max_throughput_drop_pct: float = Field(10.0, ge=0, le=100)
    noise_factor: float = Field(2.0, ge=1, le=10)            # a change must exceed this x run-to-run spread
    require_tests_pass: bool = True                           # tests that passed before must pass after


class EndpointStats(BaseModel):
    method: str
    path: str
    requests: int
    errors: int
    error_rate_pct: float
    status_codes: Dict[str, int] = Field(default_factory=dict)
    mean_ms: Optional[float] = None
    median_ms: Optional[float] = None
    p95_ms: Optional[float] = None
    p99_ms: Optional[float] = None
    min_ms: Optional[float] = None
    max_ms: Optional[float] = None
    throughput_rps: Optional[float] = None
    rep_medians_ms: List[float] = Field(default_factory=list)   # one per repetition, for run-to-run spread
    rep_throughput_rps: List[float] = Field(default_factory=list)
    spread_pct: Optional[float] = None                            # (max - min) / median of rep_medians


class Resources(BaseModel):
    samples: int = 0
    cpu_avg_pct: Optional[float] = None
    cpu_max_pct: Optional[float] = None
    mem_avg_mb: Optional[float] = None
    mem_max_mb: Optional[float] = None
    method: str = "docker stats (container), sampled while the workload ran"


class Measurement(BaseModel):
    label: str                                   # baseline | candidate
    status: str = "pending"                      # measured | failed | unavailable | cancelled
    error: Optional[str] = None
    startup_seconds: Optional[float] = None      # container start -> first healthy answer (install excluded)
    readiness_probe: Optional[str] = None
    endpoints: List[EndpointStats] = Field(default_factory=list)
    resources: Resources = Field(default_factory=Resources)
    logs_tail: str = ""


class Environment(BaseModel):
    method: str
    image: str = ""
    limits: Dict[str, str] = Field(default_factory=dict)
    load_generator: str = ""
    host: Dict[str, Any] = Field(default_factory=dict)
    profiling: str = "function-level profiling: not available for containerized runs (not run)"
    notes: List[str] = Field(default_factory=list)


class PerfRun(BaseModel):
    id: str
    project_id: str
    user_id: str
    kind: str = "baseline"                       # baseline (one measurement)
    status: str = "queued"                       # queued | running | completed | failed | unavailable | cancelled
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    workload: Workload
    environment: Optional[Environment] = None
    measurement: Optional[Measurement] = None
    stages: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None
    cancel_requested: bool = False


class PerfFinding(BaseModel):
    id: str
    project_id: str
    rule_id: str
    category: str               # n_plus_one | pagination | blocking_async | repeated_query | repeated_api_call |
                                # rerender | serialization | startup | dependency | caching | slow_endpoint | errors
    title: str
    severity: str               # high | medium | low
    evidence_kind: str          # static_warning | hypothesis | measured
    detection: str              # how it was found
    confidence: str             # low | medium | high
    file: Optional[str] = None
    line: Optional[int] = None
    endpoint: Optional[str] = None
    evidence: str = ""
    impact: str = ""
    recommendation: str = ""
    validation: str = ""
    measured_ms: Optional[float] = None          # for measured findings: the endpoint's median latency
    linked: List[str] = Field(default_factory=list)   # static findings in the handler of a measured endpoint
    status: str = "open"                         # open | planned | verified | not_improved | dismissed


class PerfAnalysis(BaseModel):
    id: str
    project_id: str
    user_id: str
    status: str = "queued"
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    stack: List[str] = Field(default_factory=list)
    supported: bool = False
    support_reason: str = ""
    suggested_workload: Optional[Workload] = None
    finding_ids: List[str] = Field(default_factory=list)
    baseline_run_id: Optional[str] = None
    error: Optional[str] = None


class PerfPlan(BaseModel):
    id: str
    project_id: str
    user_id: str
    finding_id: str
    problem: str
    evidence: str
    proposed_change: str
    expected_benefit: str                        # an estimate, labelled as such
    files: List[str]
    risks: List[str]
    tests: List[str]
    workload: Workload
    thresholds: Thresholds
    target_endpoints: List[str]                  # "METHOD /path" judged for improvement
    rollback: str
    completion_criteria: List[str]
    rank_score: float = 0.0
    rank_reasons: List[str] = Field(default_factory=list)
    autopilot_plan_id: Optional[str] = None
    created_at: str = Field(default_factory=now_iso)


class Comparison(BaseModel):
    """Before/after verdict of the performance gate for one optimization."""
    id: str = ""                                 # the Autopilot execution it belongs to
    plan_id: Optional[str] = None                # the PerfPlan
    created_at: str = Field(default_factory=now_iso)
    decision: str                                # improved | regressed | inconclusive | not_measured
    reasons: List[str] = Field(default_factory=list)
    per_endpoint: List[Dict[str, Any]] = Field(default_factory=list)
    resources: Dict[str, Any] = Field(default_factory=dict)
    baseline: Optional[Measurement] = None
    candidate: Optional[Measurement] = None
    environment: Optional[Environment] = None
    thresholds: Optional[Thresholds] = None
