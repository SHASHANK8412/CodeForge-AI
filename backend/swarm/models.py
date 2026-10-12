"""
AIForge Swarm Intelligence records: missions, task graphs, artifacts with provenance, messages, conflicts,
proposals and decisions, gates and the final report. Agent output is untrusted: artifacts are validated
against their kind's schema before they are accepted, and nothing here is evidence until a check ran.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from backend.evolution.autopilot.models import now_iso

TASK_STATES = ("pending", "ready", "running", "awaiting_review", "blocked", "completed", "failed", "cancelled")
MESSAGE_TYPES = ("request_information", "submit_artifact", "report_finding", "raise_conflict", "request_review",
                 "propose_resolution", "report_failure")


class Endpoint(BaseModel):
    """One operation of the API contract the agents share."""
    method: str
    path: str                                     # FastAPI style: /api/orders/{order_id}
    request_fields: List[str] = Field(default_factory=list)
    response_fields: List[str] = Field(default_factory=list)
    description: str = ""


class Contract(BaseModel):
    name: str = "api"
    endpoints: List[Endpoint] = Field(default_factory=list)


class Task(BaseModel):
    id: str
    objective: str
    kind: str                                    # contract | backend | frontend_client | review | integration | verification
    agent: Optional[str] = None                  # assigned from the capability registry
    capability: str
    inputs: List[str] = Field(default_factory=list)          # artifact kinds it consumes
    outputs: List[str] = Field(default_factory=list)         # artifact kinds it must produce
    depends_on: List[str] = Field(default_factory=list)
    acceptance: List[str] = Field(default_factory=list)
    required_tests: List[str] = Field(default_factory=list)
    owned_paths: List[str] = Field(default_factory=list)     # the only paths this task may write
    status: str = "pending"
    attempts: int = 0
    retry_limit: int = 1
    timeout_seconds: int = 600
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    artifacts: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    feedback: Optional[str] = None               # a repair request from the Integration Agent


class Artifact(BaseModel):
    id: str
    kind: str                                    # contract | source_files | route_inventory | client_calls | review | integration_report | test_report
    creator: str                                 # agent id
    task_id: str
    revision: Optional[str] = None               # the base project's fingerprint it was produced against
    created_at: str = Field(default_factory=now_iso)
    content: Dict[str, Any] = Field(default_factory=dict)
    content_hash: str = ""
    validation: str = "pending"                  # valid | invalid (with reasons)
    validation_errors: List[str] = Field(default_factory=list)
    supersedes: Optional[str] = None             # an earlier artifact of the same task (repairs never overwrite)
    approved: bool = False


class Message(BaseModel):
    id: str
    sender: str
    recipient: str = "swarm"
    task_id: Optional[str] = None
    type: str
    summary: str
    artifact_refs: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    proposed_action: Optional[str] = None
    confidence: Optional[str] = None             # low | medium | high (stated by the sender; not evidence)
    at: str = Field(default_factory=now_iso)


class Proposal(BaseModel):
    id: str
    author: str
    title: str
    action: str                                  # what accepting it does (e.g. "repair:frontend")
    assumptions: List[str] = Field(default_factory=list)
    benefits: List[str] = Field(default_factory=list)
    costs: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)          # measured / checked facts only
    requirements_addressed: List[str] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)
    scores: Dict[str, float] = Field(default_factory=dict)     # criterion -> 0..1 from evidence (see consensus.py)
    violates: List[str] = Field(default_factory=list)          # mandatory constraints it breaks


class Conflict(BaseModel):
    id: str
    kind: str                                    # api_contract | file_ownership | schema | dependency
    severity: str                                # critical | high | medium | low
    components: List[str] = Field(default_factory=list)
    detail: str
    evidence: Dict[str, Any] = Field(default_factory=dict)
    status: str = "open"                         # open | resolving | resolved | escalated | dismissed
    proposals: List[Proposal] = Field(default_factory=list)
    decision: Optional[Dict[str, Any]] = None    # how it was decided (rule, scores, or the person)


class Gate(BaseModel):
    name: str
    mandatory: bool
    status: str = "not_run"                      # passed | failed | not_run | not_applicable | unavailable
    evidence: Dict[str, Any] = Field(default_factory=dict)
    detail: str = ""


class Mission(BaseModel):
    id: str
    project_id: str
    user_id: str
    objective: str
    constraints: List[str] = Field(default_factory=list)
    acceptance: List[str] = Field(default_factory=list)
    contract: Optional[Contract] = None
    settings: Dict[str, Any] = Field(default_factory=dict)     # concurrency, max_messages, timeouts, priorities
    status: str = "planned"      # planned | rejected | running | awaiting_decision | completed | failed | cancelled
    base_revision: Optional[str] = None
    tasks: List[Task] = Field(default_factory=list)
    artifacts: List[Artifact] = Field(default_factory=list)
    messages: List[Message] = Field(default_factory=list)
    conflicts: List[Conflict] = Field(default_factory=list)
    gates: List[Gate] = Field(default_factory=list)
    report: Dict[str, Any] = Field(default_factory=dict)
    plan_errors: List[str] = Field(default_factory=list)
    delivery: Dict[str, Any] = Field(default_factory=dict)     # the Autopilot plan carrying the integrated files
    cancel_requested: bool = False
    created_at: str = Field(default_factory=now_iso)
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    error: Optional[str] = None
