"""
AIForge Swarm Intelligence records: missions, task graphs, artifacts with provenance, messages, conflicts,
proposals and decisions, gates and the final report. Agent output is untrusted: artifacts are validated
against their kind's schema before they are accepted, and nothing here is evidence until a check ran.
"""

import hashlib
import json
import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from backend.evolution.autopilot.models import now_iso

TASK_STATES = ("pending", "ready", "running", "awaiting_review", "blocked", "completed", "failed", "cancelled")
PHASES = ("PLANNING", "CONTRACT_READY", "PARALLEL_GENERATION", "STATIC_VALIDATION", "INTEGRATION_TESTING",
          "FAILURE_CLASSIFICATION", "REPAIR_REQUIRED", "REVALIDATION", "SECURITY_VERIFICATION", "AUTOPILOT_REVIEW")
OUTCOMES = ("SUCCEEDED", "FAILED", "BLOCKED", "NEEDS_HUMAN_REVIEW")
FINDING_CATEGORIES = ("request_contract_mismatch", "response_schema_mismatch", "http_status_mismatch",
                      "frontend_integration_error", "backend_runtime_error", "auth_mismatch", "security_violation",
                      "test_infrastructure_failure", "insufficient_evidence")
MESSAGE_TYPES = ("request_information", "submit_artifact", "report_finding", "raise_conflict", "request_review",
                 "propose_resolution", "report_failure")


class Endpoint(BaseModel):
    """One operation of the API contract the agents share (v2: JSON Schema subset, see schemas.py).

    A v1 endpoint (only request_fields / response_fields) is upgraded on load: its fields become required
    properties of unknown type, with a 200 JSON response (and 422 for a body). The field-name lists are kept in
    step with the schemas so v1 checks keep working."""
    method: str
    path: str                                     # FastAPI style: /api/orders/{order_id}
    description: str = ""
    path_params: Dict[str, Dict[str, Any]] = Field(default_factory=dict)      # name -> JSON Schema
    query_params: Dict[str, Dict[str, Any]] = Field(default_factory=dict)     # name -> {"schema", "required"}
    headers: Dict[str, Dict[str, Any]] = Field(default_factory=dict)          # name -> {"required"}
    auth: str = "none"                            # none | bearer
    request_content_type: Optional[str] = None    # application/json when there is a body
    request_schema: Optional[Dict[str, Any]] = None
    responses: Dict[str, Dict[str, Any]] = Field(default_factory=dict)        # status -> {"content_type", "schema"}
    errors: Dict[str, Dict[str, Any]] = Field(default_factory=dict)           # documented errors: status -> {...}
    request_fields: List[str] = Field(default_factory=list)                   # v1 (derived from request_schema)
    response_fields: List[str] = Field(default_factory=list)                  # v1 (derived from the success schema)

    @model_validator(mode="before")
    @classmethod
    def _upgrade(cls, data):
        from backend.swarm.schemas import upgrade
        if isinstance(data, dict):
            data = upgrade(data)
            if data.get("request_schema") and not data.get("request_content_type"):
                data["request_content_type"] = "application/json"
            if data.get("request_schema") and not data.get("request_fields"):
                data["request_fields"] = sorted((data["request_schema"].get("properties") or {}))
            ok = next((v for k, v in sorted((data.get("responses") or {}).items()) if str(k).startswith("2")), None)
            if ok and not data.get("response_fields"):
                data["response_fields"] = sorted(((ok.get("schema") or {}).get("properties") or {}))
            params = dict(data.get("path_params") or {})
            for name in re.findall(r"\{(\w+)\}", str(data.get("path", ""))):
                params.setdefault(name, {})                       # type left open unless the contract says
            data["path_params"] = params
        return data

    @field_validator("auth")
    @classmethod
    def _auth(cls, v):
        if v not in ("none", "bearer"):
            raise ValueError("auth must be 'none' or 'bearer'")
        return v

    def key(self) -> str:
        return f"{self.method.upper()} {self.path}"


class Contract(BaseModel):
    name: str = "api"
    version: int = 2                              # schema format; v1 contracts are upgraded on load
    endpoints: List[Endpoint] = Field(default_factory=list)

    def revision(self) -> str:
        """Content hash of the contract: the 'contract version' a mission's results refer to."""
        return hashlib.sha256(json.dumps(self.model_dump(), sort_keys=True).encode()).hexdigest()[:16]


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
    status: str = "not_run"                      # passed | failed | not_run | not_applicable | unavailable | flaky
    evidence: Dict[str, Any] = Field(default_factory=dict)
    detail: str = ""


class Finding(BaseModel):
    """One integration failure, with the evidence it rests on. 'verified' needs runtime evidence (a check that ran
    in the isolated environment); a static-only finding stays 'unverified'; a finding whose responsible component
    cannot be established is 'unresolved' (never guessed)."""
    id: str
    mission_id: str
    key: str                                      # identity of the mismatch across rounds (category|endpoint|check)
    endpoint: str                                 # "POST /api/orders", or the component when no endpoint applies
    component: str                                # where it was observed: backend | frontend | integration | infrastructure
    category: str                                 # FINDING_CATEGORIES
    severity: str                                 # critical | high | medium | low
    expected: str
    observed: str
    evidence: Dict[str, Any] = Field(default_factory=dict)       # check ids, artifact ids, request/response excerpts
    basis: str = "static"                         # static (AST) | declared (OpenAPI) | runtime (executed check)
    responsible: Optional[str] = None             # backend | frontend, only when established by the evidence
    confidence: str = "medium"                    # from the kind of evidence, never from an agent's statement
    recommended_correction: str = ""
    status: str = "unverified"   # verified | unverified | unresolved | repaired | repair_failed | needs_human_review | blocked
    round: int = 0                                # the integration round that observed it
    repair_attempt: Optional[str] = None
    created_at: str = Field(default_factory=now_iso)


class RepairAttempt(BaseModel):
    """One bounded repair of one component (automatic, or directed by a person)."""
    id: str
    component: str                                # backend | frontend
    task_id: str
    finding_keys: List[str]
    finding_ids: List[str]
    requested_by: str                             # integration_agent | user <id>
    author: Optional[str] = None                  # the agent that produced the new version
    requested_at: str = Field(default_factory=now_iso)
    completed_at: Optional[str] = None
    request: str = ""                             # the evidence and expected behaviour sent to the agent
    artifact_before: Optional[str] = None
    artifact_after: Optional[str] = None
    changed_files: List[str] = Field(default_factory=list)
    validation: Dict[str, Any] = Field(default_factory=dict)    # re-extraction, runtime checks, gates after the repair
    outcome: str = "pending"                      # pending | succeeded | failed


class Mission(BaseModel):
    id: str
    project_id: str
    user_id: str
    objective: str
    constraints: List[str] = Field(default_factory=list)
    acceptance: List[str] = Field(default_factory=list)
    contract: Optional[Contract] = None
    settings: Dict[str, Any] = Field(default_factory=dict)     # concurrency, max_messages, timeouts, priorities
    status: str = "planned"      # planned | rejected | running | awaiting_decision | completed | failed | blocked | cancelled
    phase: str = "PLANNING"      # lifecycle phase (PHASES)
    outcome: Optional[str] = None                # SUCCEEDED | FAILED | BLOCKED | NEEDS_HUMAN_REVIEW
    phase_history: List[Dict[str, Any]] = Field(default_factory=list)
    base_revision: Optional[str] = None
    tasks: List[Task] = Field(default_factory=list)
    artifacts: List[Artifact] = Field(default_factory=list)
    messages: List[Message] = Field(default_factory=list)
    conflicts: List[Conflict] = Field(default_factory=list)
    gates: List[Gate] = Field(default_factory=list)
    findings: List[Finding] = Field(default_factory=list)
    repairs: List[RepairAttempt] = Field(default_factory=list)
    runtime: List[Dict[str, Any]] = Field(default_factory=list)  # each integration-testing run (checks, environment, cleanup)
    properties: Dict[str, Any] = Field(default_factory=dict)     # per endpoint: static / declared / verified values
    autopilot_review: Dict[str, Any] = Field(default_factory=dict)
    report: Dict[str, Any] = Field(default_factory=dict)
    plan_errors: List[str] = Field(default_factory=list)
    delivery: Dict[str, Any] = Field(default_factory=dict)     # the Autopilot plan carrying the integrated files
    cancel_requested: bool = False
    created_at: str = Field(default_factory=now_iso)
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    error: Optional[str] = None
