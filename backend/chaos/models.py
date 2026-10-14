"""
Records of the AIForge Chaos Engineer.

A failure is *reproduced* only when an experiment showed it; static analysis yields *suspicions*.
Scores come only from evaluated criteria; a criterion that could not be evaluated is "not evaluated"
and never counts as passed.
"""

import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from backend.evolution.autopilot.models import now_iso

_ALIAS = re.compile(r"^[a-z][a-z0-9-]{1,30}$")
_ENV = re.compile(r"^[A-Z_][A-Z0-9_]{0,60}$")
RESERVED_ENV = {"PATH", "PYTHONPATH", "HOME", "PYTHONDONTWRITEBYTECODE", "PYTHONUNBUFFERED", "LD_PRELOAD"}


class DependencySpec(BaseModel):
    """A disposable stub dependency, reachable from the app at http://<name>:8080 via env var <env_var>."""
    name: str
    env_var: str
    routes: Dict[str, Any] = Field(default_factory=dict)       # path -> JSON body the stub returns

    @field_validator("name")
    @classmethod
    def _name(cls, v):
        if not _ALIAS.match(v) or v in ("app", "probe"):
            raise ValueError("dependency name: lowercase letters, digits and '-', 2-31 chars, not 'app'/'probe'")
        return v

    @field_validator("env_var")
    @classmethod
    def _env(cls, v):
        if not _ENV.match(v) or v in RESERVED_ENV:
            raise ValueError("env_var must be an UPPER_CASE name and not a reserved variable")
        return v

    @field_validator("routes")
    @classmethod
    def _routes(cls, v):
        if len(v) > 20 or any(not str(k).startswith("/") or ".." in str(k) for k in v):
            raise ValueError("routes: up to 20 paths starting with '/'")
        if len(str(v)) > 64_000:
            raise ValueError("routes are too large")
        return v


class Target(BaseModel):
    method: str = "GET"
    path: str

    @field_validator("path")
    @classmethod
    def _path(cls, v):
        if not v.startswith("/") or ".." in v.split("/") or "://" in v or "\\" in v or len(v) > 200:
            raise ValueError("endpoint paths are relative ('/...') without '..' or URLs")
        return v

    @field_validator("method")
    @classmethod
    def _method(cls, v):
        v = v.upper()
        if v not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
            raise ValueError("unsupported method")
        return v


class Limits(BaseModel):
    memory_mb: int = Field(512, ge=128, le=1024)
    cpus: float = Field(1.0, ge=0.25, le=1.0)
    max_scenario_seconds: int = Field(120, ge=20, le=300)
    max_burst_requests: int = Field(300, ge=10, le=1000)
    max_concurrency: int = Field(16, ge=1, le=32)
    timeout_budget_ms: int = Field(3000, ge=200, le=30000)      # a request slower than this did not fail fast
    recovery_budget_s: int = Field(30, ge=5, le=120)


class AssessmentConfig(BaseModel):
    environment: str = "sandbox"                 # only "sandbox" (an isolated Docker network) is supported
    scenarios: List[str]
    dependencies: List[DependencySpec] = Field(default_factory=list, max_length=3)
    endpoints: List[Target] = Field(default_factory=list, max_length=8)   # empty: from the app's /openapi.json
    health_path: Optional[str] = None
    limits: Limits = Field(default_factory=Limits)


class Check(BaseModel):
    check: str
    passed: bool
    detail: str = ""


class Observation(BaseModel):
    """One phase of a scenario: what the probe saw."""
    phase: str                                   # baseline | failure | recovery | after
    at: str = Field(default_factory=now_iso)
    seconds_from_start: Optional[float] = None
    per_endpoint: Dict[str, Dict[str, Any]] = Field(default_factory=dict)   # ep -> {ok, total, success_rate, p50_ms, max_ms, codes}
    health: Optional[str] = None
    leaks: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


class Criterion(BaseModel):
    id: str
    category: str                                # containment | timeout | recovery | error_handling | degradation | data_integrity | post_recovery
    description: str
    status: str                                  # passed | failed | not_evaluated
    evidence: str


class ScenarioResult(BaseModel):
    scenario: str
    status: str = "pending"                      # pending | running | recovering | evaluating | passed | failed | inconclusive | not_evaluated | aborted
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    procedure: List[str] = Field(default_factory=list)       # what was done, in order (audit trail)
    observations: List[Observation] = Field(default_factory=list)
    criteria: List[Criterion] = Field(default_factory=list)
    detect_seconds: Optional[float] = None       # injection -> first degraded answer
    recovery_seconds: Optional[float] = None     # restore -> every endpoint answering successfully again
    affected_endpoints: List[str] = Field(default_factory=list)   # observed, not inferred
    unaffected_endpoints: List[str] = Field(default_factory=list)
    app_logs_tail: str = ""
    error: Optional[str] = None


class ChaosFinding(BaseModel):
    id: str
    project_id: str
    category: str
    component: str
    severity: str                                # critical | high | medium | low
    kind: str                                    # reproduced | static_suspicion
    title: str
    evidence: str
    reproduction: str = ""
    expected: str = ""
    observed: str = ""
    confidence: str = "medium"
    root_cause: str = ""
    root_cause_level: str = "unconfirmed_hypothesis"   # confirmed | probable | unconfirmed_hypothesis
    file: Optional[str] = None
    line: Optional[int] = None
    remediation: str = ""
    scenario: Optional[str] = None
    criterion: Optional[str] = None
    status: str = "open"                         # open | planned | verified | not_improved | dismissed


class Assessment(BaseModel):
    id: str
    project_id: str
    user_id: str
    status: str = "queued"     # queued | preflight | awaiting_approval | running | recovering | evaluating | completed | failed | aborted | inconclusive | refused
    created_at: str = Field(default_factory=now_iso)
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    config: AssessmentConfig
    preflight: List[Check] = Field(default_factory=list)
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    current: Optional[str] = None                # scenario now running
    results: List[ScenarioResult] = Field(default_factory=list)
    score: Dict[str, Any] = Field(default_factory=dict)
    finding_ids: List[str] = Field(default_factory=list)
    impact: Dict[str, Any] = Field(default_factory=dict)      # Digital Twin view: potential vs observed
    audit: List[Dict[str, Any]] = Field(default_factory=list)  # every action with a timestamp
    abort_requested: bool = False
    error: Optional[str] = None
    purpose: str = "assessment"                  # assessment | repair_gate
