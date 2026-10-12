"""
AIForge Reality Simulator records. Three kinds of number are kept apart everywhere:
  assumption   supplied by the person (arrival rate, traffic mix, prices, dependency latency)
  measured     produced by a run against an isolated copy of the app (with the run's id)
  predicted    produced by the analytical model from measured inputs + assumptions (with formulas)
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from backend.evolution.autopilot.models import now_iso

MAX_RPS = 200.0
MAX_DURATION = 120
MAX_REQUESTS = 20000


class Resources(BaseModel):
    workers: int = Field(1, ge=1, le=4)            # uvicorn worker processes
    cpus: float = Field(1.0, ge=0.25, le=2.0)      # container CPU limit
    memory_mb: int = Field(1024, ge=128, le=2048)


class Alternative(BaseModel):
    id: str = Field(..., pattern=r"^[a-z0-9_]{1,30}$")
    title: str
    resources: Resources = Field(default_factory=Resources)
    dependency_latency_ms: Optional[float] = Field(None, ge=0, le=5000)   # an assumption about an external service


class Traffic(BaseModel):
    pattern: str = Field("constant", pattern="^(constant|ramp|burst)$")
    rps: float = Field(10, gt=0, le=MAX_RPS)                              # constant rate, or the ramp's end / burst peak
    start_rps: float = Field(1, gt=0, le=MAX_RPS)                         # ramp start / burst base rate
    burst_seconds: float = Field(5, gt=0, le=60)
    duration_seconds: int = Field(30, ge=5, le=MAX_DURATION)
    mix: Dict[str, float] = Field(default_factory=dict)                  # "GET /path" -> weight

    @field_validator("mix")
    @classmethod
    def weights(cls, v):
        if any(w < 0 for w in v.values()) or (v and sum(v.values()) <= 0):
            raise ValueError("traffic weights must be non-negative and not all zero")
        for k in v:
            method, _, path = k.partition(" ")
            if method != "GET" or not path.startswith("/") or "{" in path:
                raise ValueError(f"only GET endpoints without path parameters can be driven: {k}")
        return v

    @model_validator(mode="after")
    def bounded(self):
        peak = max(self.rps, self.start_rps)
        if peak * self.duration_seconds > MAX_REQUESTS:
            raise ValueError(f"the scenario would send up to {int(peak * self.duration_seconds)} requests; the limit is {MAX_REQUESTS}")
        return self


class Prices(BaseModel):
    """User-supplied unit prices (no pricing data is built in). Costs are estimates from these inputs."""
    vcpu_hour: float = Field(..., ge=0)
    gb_hour: float = Field(0.0, ge=0)
    currency: str = Field("USD", max_length=8)


class Scenario(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    traffic: Traffic
    alternatives: List[Alternative] = Field(..., min_length=1, max_length=4)
    dependency: Optional[Dict[str, Any]] = None   # Chaos stub: {"name", "env_var", "routes"} for latency alternatives
    dependent_endpoints: List[str] = Field(default_factory=list)          # endpoints that call the dependency
    prices: Optional[Prices] = None
    target_utilization: float = Field(0.7, gt=0.1, le=0.95)
    assumptions: List[str] = Field(default_factory=list)                 # free-text assumptions the person states

    @model_validator(mode="after")
    def consistent(self):
        ids = [a.id for a in self.alternatives]
        if len(set(ids)) != len(ids):
            raise ValueError("alternative ids must be unique")
        if any(a.dependency_latency_ms is not None for a in self.alternatives) and not self.dependent_endpoints:
            raise ValueError("a dependency-latency alternative needs the endpoints that call the dependency")
        return self


class Simulation(BaseModel):
    id: str
    project_id: str
    user_id: str
    scenario: Scenario
    run_load: bool = False                       # execute the workload (approved) or predict only
    status: str = "queued"                       # queued | running | completed | failed | cancelled
    created_at: str = Field(default_factory=now_iso)
    finished_at: Optional[str] = None
    revision: Optional[str] = None
    application: Dict[str, Any] = Field(default_factory=dict)        # Digital Twin facts with their evidence
    baseline: Dict[str, Any] = Field(default_factory=dict)           # measured service times (low load)
    predictions: Dict[str, Any] = Field(default_factory=dict)        # alternative id -> analytical prediction
    measurements: Dict[str, Any] = Field(default_factory=dict)       # alternative id -> load-run results
    comparisons: Dict[str, Any] = Field(default_factory=dict)        # alternative id -> predicted vs observed
    bottlenecks: List[Dict[str, Any]] = Field(default_factory=list)
    costs: Dict[str, Any] = Field(default_factory=dict)
    recommendation: Dict[str, Any] = Field(default_factory=dict)
    stages: List[Dict[str, Any]] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    cancel_requested: bool = False
    error: Optional[str] = None


class CalibrationRecord(BaseModel):
    id: str
    project_id: str
    simulation_id: str
    alternative: str
    method: str
    metric: str                                  # throughput_rps | mean_ms | p95_ms
    revision: Optional[str] = None
    inputs: Dict[str, Any] = Field(default_factory=dict)
    predicted: float
    low: Optional[float] = None
    high: Optional[float] = None
    observed: float
    error_pct: float
    within_bounds: bool
    comparable_key: str                          # only records with the same key are aggregated
    recorded_at: str = Field(default_factory=now_iso)
