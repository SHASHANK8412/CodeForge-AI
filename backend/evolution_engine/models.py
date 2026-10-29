"""
AIForge Evolution Engine records. Measured values and model-written text are kept apart: everything
under `measurements`, `checks`, `security` and `performance` comes from executions; `rationale` and
`model` describe what the model was asked and said, and are never used as evidence.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from backend.evolution.autopilot.models import CheckResult, now_iso
from backend.performance.engineer.models import Thresholds, Workload

OUTCOMES = ("validated_improvement", "no_improvement", "regression", "failed", "inconclusive", "awaiting_approval")


class Opportunity(BaseModel):
    id: str
    project_id: str
    category: str                                   # n_plus_one (the vertical slice); others are listed, not run
    title: str
    evidence: List[Dict[str, Any]] = Field(default_factory=list)    # {kind: static|measured|history, source, detail}
    file: Optional[str] = None
    line: Optional[int] = None
    endpoint: Optional[str] = None                  # "GET /api/x" the change should speed up
    components: List[str] = Field(default_factory=list)             # Digital Twin: the file and its dependents
    hypothesis: str = ""
    expected_benefit: str = ""                      # a prediction until measured
    possible_regressions: List[str] = Field(default_factory=list)
    confidence: str = "low"                         # low | medium | high
    validation: str = ""
    experimentable: bool = False
    not_experimentable_reason: Optional[str] = None
    priority: float = 0.0
    priority_factors: Dict[str, float] = Field(default_factory=dict)
    history: List[Dict[str, Any]] = Field(default_factory=list)     # related past experiments (Engineering Memory)
    discovered_at: str = Field(default_factory=now_iso)


class Strategy(BaseModel):
    id: str                                         # join_query | batch_in_query | eager_load_selectin | ...
    title: str
    instructions: str
    memory_note: Optional[str] = None               # why memory moved it up/down, if it did


class Weights(BaseModel):
    """Ranking weights among candidates that pass every mandatory constraint (normalized at use)."""
    performance: float = Field(0.5, ge=0, le=1)
    security: float = Field(0.15, ge=0, le=1)
    reliability: float = Field(0.15, ge=0, le=1)
    maintainability: float = Field(0.1, ge=0, le=1)
    resource_efficiency: float = Field(0.1, ge=0, le=1)


class ExperimentPlan(BaseModel):
    hypothesis: str
    baseline: str                                   # what the candidates are compared against
    strategies: List[Strategy] = Field(default_factory=list)
    environment: str = ""
    required_tests: List[str] = Field(default_factory=list)
    metrics: List[str] = Field(default_factory=list)
    workload: Workload
    thresholds: Thresholds = Field(default_factory=Thresholds)
    target_endpoints: List[str] = Field(default_factory=list)
    weights: Weights = Field(default_factory=Weights)
    allowed_files: List[str] = Field(default_factory=list)
    safety: List[str] = Field(default_factory=list)
    max_seconds: int = 3600
    resource_limits: Dict[str, str] = Field(default_factory=dict)
    cleanup: List[str] = Field(default_factory=list)
    rejected_reasons: List[str] = Field(default_factory=list)       # why the experiment cannot be evaluated reliably
    context: Dict[str, Any] = Field(default_factory=dict)           # stack facts used by Engineering Memory
    suppressed_strategies: List[Dict[str, Any]] = Field(default_factory=list)


class Candidate(BaseModel):
    id: str                                         # c1, c2, c3
    strategy: str
    status: str = "pending"                         # pending | generating | evaluating | evaluated | failed | duplicate | cancelled
    model: Dict[str, Any] = Field(default_factory=dict)              # model name, prompt hash, attempts (configuration only)
    changes: Dict[str, str] = Field(default_factory=dict)           # path -> full new content
    diff: str = ""
    patch_hash: Optional[str] = None
    generation_error: Optional[str] = None
    duplicate_of: Optional[str] = None
    checks: List[CheckResult] = Field(default_factory=list)
    correctness: Dict[str, Any] = Field(default_factory=dict)       # Autopilot comparison verdict + failure kind
    security: Dict[str, Any] = Field(default_factory=dict)
    performance: Dict[str, Any] = Field(default_factory=dict)
    resilience: Dict[str, Any] = Field(default_factory=lambda: {"status": "not_evaluated",
                                                               "reason": "no Chaos Engineer scenario applies to this opportunity"})
    maintainability: Dict[str, Any] = Field(default_factory=dict)
    resources: Dict[str, Any] = Field(default_factory=dict)
    constraints: List[Dict[str, Any]] = Field(default_factory=list)  # mandatory checks: {name, passed, detail}
    eligible: bool = False
    score: Optional[float] = None
    score_breakdown: Dict[str, Any] = Field(default_factory=dict)
    rejection_reasons: List[str] = Field(default_factory=list)
    failure_kind: Optional[str] = None              # candidate_defect | infrastructure | flaky | insufficient_evidence
    durations: Dict[str, float] = Field(default_factory=dict)


class Approval(BaseModel):
    candidate_id: str
    approved_by: str
    approved_at: str = Field(default_factory=now_iso)
    source_revision: str
    patch_hash: str
    valid: bool = True
    invalidated_reason: Optional[str] = None


class Promotion(BaseModel):
    status: str = "pending"                         # pending | running | promoted | rejected | rolled_back | failed | stale
    autopilot_plan_id: Optional[str] = None
    execution_id: Optional[str] = None
    gate: Dict[str, Any] = Field(default_factory=dict)
    final_tests: Optional[CheckResult] = None
    rolled_back: bool = False
    rollback_detail: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    error: Optional[str] = None


class Experiment(BaseModel):
    id: str
    project_id: str
    user_id: str
    opportunity: Opportunity
    plan: ExperimentPlan
    status: str = "planned"         # planned | rejected | queued | running | evaluated | approved | promoting | completed | failed | cancelled
    outcome: Optional[str] = None   # one of OUTCOMES once evaluated
    outcome_reasons: List[str] = Field(default_factory=list)
    source_revision: Optional[str] = None
    candidates: List[Candidate] = Field(default_factory=list)
    baseline_checks: List[CheckResult] = Field(default_factory=list)
    baseline_security: Dict[str, Any] = Field(default_factory=dict)
    measurement: Dict[str, Any] = Field(default_factory=dict)        # environment, per-version measurements
    selected: Optional[str] = None
    selection: Dict[str, Any] = Field(default_factory=dict)
    approval: Optional[Approval] = None
    promotion: Optional[Promotion] = None
    audit: List[Dict[str, Any]] = Field(default_factory=list)
    current: str = ""
    cancel_requested: bool = False
    created_at: str = Field(default_factory=now_iso)
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    error: Optional[str] = None


class MemoryRecord(BaseModel):
    """One strategy's measured result in one experiment: what was tried, in which context, what happened."""
    id: str
    experiment_id: str
    project_id: str
    category: str
    context: Dict[str, Any] = Field(default_factory=dict)            # stack facts: framework, data access, endpoint
    strategy: str
    selected: bool = False
    result: str                     # won | eligible | rejected | failed | inconclusive
    reasons: List[str] = Field(default_factory=list)
    failure_kind: Optional[str] = None
    measured: Dict[str, Any] = Field(default_factory=dict)          # median change, repetitions, noise
    evidence_quality: str = "insufficient"                           # strong | moderate | weak | insufficient
    scope: str = ""                 # what the result can and cannot be generalised to
    recorded_at: str = Field(default_factory=now_iso)
    final_outcome: Optional[str] = None             # filled when the experiment is promoted / rolled back
