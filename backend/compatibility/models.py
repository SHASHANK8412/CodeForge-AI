"""
AICE records. The shared contract extends the Swarm contract (backend/swarm/models.py: Endpoint / Contract, the API part
in a JSON Schema subset) with the data model, conventions and environment the components share, and is versioned per
project: a new version is only created by an explicit registration with an author and a reason, and every version
change is recorded as a ContractChange (what changed, whether it breaks consumers, which components it affects).

Nothing in a contract is invented: what the source (architect output, a person, an API call) did not state is listed in
`unspecified` and is reported as not checked, never as compatible.
"""

import hashlib
import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from backend.evolution.autopilot.models import now_iso
from backend.swarm.models import Contract

FIELD_TYPES = ("string", "integer", "number", "boolean", "object", "array", "unknown")
FIELD_FORMATS = (None, "date-time", "date", "uuid", "email")
RUN_STATES = ("queued", "running", "COMPATIBLE", "COMPATIBLE_WITH_WARNINGS", "INCOMPATIBLE", "BLOCKED", "CANCELLED")
FINAL_STATES = ("COMPATIBLE", "COMPATIBLE_WITH_WARNINGS", "INCOMPATIBLE", "BLOCKED", "CANCELLED")
FINDING_STATES = ("open", "repaired", "unresolved", "needs_contract_decision", "info", "blocked")
AGENTS = ("frontend", "backend", "database", "architect")


class EntityField(BaseModel):
    name: str
    type: str = "unknown"                      # FIELD_TYPES
    format: Optional[str] = None               # FIELD_FORMATS (date-time / date / uuid / email)
    required: bool = True                      # present on every record
    nullable: bool = False
    primary_key: bool = False
    references: Optional[str] = None           # "entity.field" (a relationship)


class Entity(BaseModel):
    name: str                                  # as the requirements / architecture name it ("Task")
    table: Optional[str] = None                # persisted name when stated ("tasks")
    fields: List[EntityField] = Field(default_factory=list)


class EnvVar(BaseModel):
    name: str
    component: str = "backend"                 # backend | frontend | database
    required: bool = True
    description: str = ""


class SharedContract(BaseModel):
    """One version of a project's integration contract."""
    id: str = ""                               # "v<version>" (store key)
    project_id: str
    version: int = 1
    revision: str = ""                         # content hash of the contract body
    api: Contract = Field(default_factory=Contract)
    entities: List[Entity] = Field(default_factory=list)
    auth: Dict[str, Any] = Field(default_factory=lambda: {"scheme": "unspecified"})   # bearer | none | unspecified
    error_format: Optional[Dict[str, Any]] = None       # JSON Schema of every error body (FastAPI: {"detail": ...})
    pagination: Optional[Dict[str, Any]] = None         # {"style": "envelope", "items_field", "total_field"} | {"style": "array"}
    datetime_format: Optional[str] = None               # "iso8601" | "epoch_seconds" | "epoch_millis"
    environment: List[EnvVar] = Field(default_factory=list)
    dependencies: Dict[str, List[str]] = Field(default_factory=dict)   # component -> components it calls
    requirements: List[str] = Field(default_factory=list)              # what the contract was derived from
    unspecified: Dict[str, List[str]] = Field(default_factory=dict)    # "GET /x" | "contract" -> aspects not stated
    conventions: Dict[str, str] = Field(default_factory=dict)          # aspect -> where a default came from
    source: str = "api"                        # architect | user | api
    author: str = ""
    reason: str = ""
    parent_version: Optional[int] = None
    created_at: str = Field(default_factory=now_iso)

    def body(self) -> Dict[str, Any]:
        """What the revision hashes: everything that defines behaviour (not who registered it or when)."""
        return self.model_dump(mode="json", include={"api", "entities", "auth", "error_format", "pagination", "datetime_format",
                                                     "environment", "dependencies", "unspecified"})

    def compute_revision(self) -> str:
        return hashlib.sha256(json.dumps(self.body(), sort_keys=True).encode()).hexdigest()[:16]


class ChangeItem(BaseModel):
    kind: str                                  # endpoint_added | request_field_removed | entity_field_type | auth_changed | ...
    target: str                                # "POST /api/tasks request.title", "entity Task.title"
    before: Any = None
    after: Any = None
    breaking: bool = False
    why: str = ""                              # why it is (not) backward compatible
    affected_components: List[str] = Field(default_factory=list)
    affected_code: List[str] = Field(default_factory=list)              # "frontend/src/api.js:12" from the last analysis


class ContractChange(BaseModel):
    id: str
    project_id: str
    from_version: Optional[int] = None
    to_version: int
    from_revision: Optional[str] = None
    to_revision: str
    author: str
    reason: str
    source: str = "api"
    items: List[ChangeItem] = Field(default_factory=list)
    breaking: bool = False
    affected_components: List[str] = Field(default_factory=list)
    at: str = Field(default_factory=now_iso)


class CompatFinding(BaseModel):
    """One compatibility problem, with the evidence it rests on.

    basis: static (read from the code by a deterministic rule) | static_heuristic (a pattern match that can miss or
    misread, e.g. which response fields the frontend reads) | runtime (a generated test that ran) | model (a language
    model's reading of an ambiguous case - advisory only, never the reason anything passes)."""
    id: str
    key: str                                   # rule|target (identity across analyses and repairs)
    rule: str
    severity: str                              # critical | high | medium | low
    target: str
    components: List[str] = Field(default_factory=list)
    expected: str = ""                         # what the contract says
    actual: str = ""                           # what the implementation does
    evidence: Dict[str, Any] = Field(default_factory=dict)
    recommended_fix: str = ""
    responsible_agent: Optional[str] = None    # AGENTS; None when the evidence does not establish it
    basis: str = "static"
    status: str = "open"                       # FINDING_STATES
    breaking: Optional[bool] = None            # drift / contract changes
    repairable: bool = False
    detected_at: str = Field(default_factory=now_iso)


class GeneratedTest(BaseModel):
    id: str                                    # pytest function name
    kind: str                                  # endpoint_exists | valid_request | missing_required_field | unauthenticated |
                                               # frontend_request | db_schema | db_roundtrip
    target: str
    description: str
    status: str = "not_run"                    # not_run | passed | failed | skipped | error
    detail: str = ""


class RepairRecord(BaseModel):
    attempt: int
    agent: str
    strategy: str = ""                         # deterministic rule names, or model:<agent>
    finding_keys: List[str] = Field(default_factory=list)
    files_changed: List[str] = Field(default_factory=list)
    rejected_paths: List[Dict[str, str]] = Field(default_factory=list)
    resolved: List[str] = Field(default_factory=list)
    new_findings: List[str] = Field(default_factory=list)
    tests_before: Dict[str, int] = Field(default_factory=dict)
    tests_after: Dict[str, int] = Field(default_factory=dict)
    outcome: str = "pending"                   # resolved | improved | no_change | regressed | no_fix | rejected | deferred
    rolled_back: bool = False
    note: str = ""
    started_at: str = Field(default_factory=now_iso)
    finished_at: Optional[str] = None


class IntegrationRun(BaseModel):
    id: str
    project_id: str
    user_id: str
    kind: str = "analyze"                      # analyze (static only) | verify (+ generated tests, bounded repairs)
    source: str = "api"                        # api | workflow
    status: str = "queued"                     # RUN_STATES
    contract_version: Optional[int] = None
    contract_revision: Optional[str] = None
    settings: Dict[str, Any] = Field(default_factory=dict)
    components: Dict[str, Any] = Field(default_factory=dict)          # what was analyzed (counts, files)
    coverage: List[Dict[str, str]] = Field(default_factory=list)      # each check: checked | not_checked | blocked |
                                                                       # not_applicable, and why
    findings: List[CompatFinding] = Field(default_factory=list)
    original_findings: List[CompatFinding] = Field(default_factory=list)
    tests: List[GeneratedTest] = Field(default_factory=list)
    test_execution: Dict[str, Any] = Field(default_factory=dict)      # status, environment, counts, log excerpt
    repairs: List[RepairRecord] = Field(default_factory=list)
    implementation: Dict[str, Any] = Field(default_factory=dict)      # the snapshot drift detection compares against
    report: Dict[str, Any] = Field(default_factory=dict)
    delivery: Dict[str, Any] = Field(default_factory=dict)
    activity: List[Dict[str, Any]] = Field(default_factory=list)
    current_operation: str = ""
    cancel_requested: bool = False
    error: Optional[str] = None
    started_at: str = Field(default_factory=now_iso)
    finished_at: Optional[str] = None
