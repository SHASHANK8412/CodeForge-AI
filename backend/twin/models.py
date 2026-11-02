"""
Records of the AIForge Digital Twin: the dependency graph of a project, impact reports for
proposed changes, and the comparison of a report's predictions with what a change actually did.

Every edge says how it is known: "established" (read directly from the code: an import that
resolves to a project file, a decorator, a JSX element of an imported component) or "inferred"
(a match that is likely but not provable statically: a URL string matched to a route, a test
file named after a module). Predictions built on inferred edges are marked as such.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from backend.evolution.autopilot.models import now_iso

NODE_TYPES = ("file", "function", "class", "route", "model", "component", "test", "config", "package")
EDGE_TYPES = (
    "imports",        # file -> file           (module import that resolves to a project file)
    "uses",           # file -> function/class/model/component (imported symbol)
    "defines",        # file -> function/class/model/component/route
    "handled_by",     # route -> function
    "renders",        # file -> component      (JSX element of an imported component)
    "calls_api",      # file -> route          (URL string in a fetch/axios call matched to a route)
    "tests",          # test -> file           (test imports the module, or is named after it)
    "depends_on",     # file -> package        (third-party import)
)


class Node(BaseModel):
    id: str
    type: str
    path: Optional[str] = None
    symbol: Optional[str] = None
    language: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class Edge(BaseModel):
    source: str
    target: str
    type: str
    certainty: str = "established"      # established | inferred
    evidence: str = ""


class GraphAnalysis(BaseModel):
    id: str
    project_id: str
    user_id: str
    status: str = "queued"               # queued | running | completed | failed
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    fingerprint: str = ""                # sizes and mtimes of the scanned files, to detect a stale graph
    stats: Dict[str, Any] = Field(default_factory=dict)
    nodes: List[Node] = Field(default_factory=list)
    edges: List[Edge] = Field(default_factory=list)
    unresolved: List[Dict[str, Any]] = Field(default_factory=list)
    cycles: List[List[str]] = Field(default_factory=list)
    limits: List[str] = Field(default_factory=list)   # what the scan could not cover
    error: Optional[str] = None


class RiskFactor(BaseModel):
    factor: str
    points: int
    reason: str


class SelectedTest(BaseModel):
    path: str
    reasons: List[str]
    certainty: str = "established"
    kind: str = "unit"                   # unit | integration | regression


class Prediction(BaseModel):
    """The impact of one change option, computed from the graph."""
    label: str
    request: str
    seeds: List[Dict[str, Any]] = Field(default_factory=list)          # {path, source, reason}
    change_kinds: List[str] = Field(default_factory=list)
    modify_scope: List[str] = Field(default_factory=list)              # files expected to change
    create_scope: List[str] = Field(default_factory=list)              # folders where new files may appear
    direct: List[Dict[str, Any]] = Field(default_factory=list)         # {path, via, certainty}
    transitive: List[Dict[str, Any]] = Field(default_factory=list)     # {path, depth, chain, certainty}
    apis: List[Dict[str, Any]] = Field(default_factory=list)
    models: List[Dict[str, Any]] = Field(default_factory=list)
    components: List[Dict[str, Any]] = Field(default_factory=list)
    configs: List[Dict[str, Any]] = Field(default_factory=list)
    interfaces_at_risk: List[Dict[str, Any]] = Field(default_factory=list)
    risk: str = "low"                                                   # low | medium | high | critical
    risk_points: int = 0
    risk_factors: List[RiskFactor] = Field(default_factory=list)
    security_review: bool = False
    tests: List[SelectedTest] = Field(default_factory=list)
    untested: List[str] = Field(default_factory=list)
    validation_steps: List[str] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)


class Outcome(BaseModel):
    """Prediction versus reality, recorded after the linked Autopilot execution ended."""
    execution_id: str
    execution_status: str
    recorded_at: str = Field(default_factory=now_iso)
    predicted_files: List[str] = Field(default_factory=list)
    predicted_affected: List[str] = Field(default_factory=list)
    actual_files: List[str] = Field(default_factory=list)
    out_of_scope_files: List[str] = Field(default_factory=list)
    unexpected_files: List[str] = Field(default_factory=list)
    predicted_not_changed: List[str] = Field(default_factory=list)
    validation_failures: List[str] = Field(default_factory=list)
    precision: Optional[float] = None
    recall: Optional[float] = None
    limitations: List[str] = Field(default_factory=list)


class ImpactReport(BaseModel):
    id: str
    project_id: str
    user_id: str
    request: str
    status: str = "queued"               # queued | running | completed | failed
    created_at: str = Field(default_factory=now_iso)
    finished_at: Optional[str] = None
    graph_id: Optional[str] = None
    graph_stale: bool = False
    planner: Dict[str, Any] = Field(default_factory=dict)   # how the change proposal was produced
    options: List[Prediction] = Field(default_factory=list)  # [0] = the request; more = alternatives
    assumptions: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    files_written: int = 0               # always 0: a simulation is read-only (checked, see simulate.py)
    plan_id: Optional[str] = None        # Autopilot plan created from this report
    outcome: Optional[Outcome] = None
    error: Optional[str] = None
