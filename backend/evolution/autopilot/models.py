"""
Records of AIForge Autopilot: analyses, findings, improvement plans, executions and checks.

The states are kept apart on purpose: a finding is *detected*, a plan *proposes*, an execution
*applies* changes, checks *run*, and a fix is *verified* only when the checks support it.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Confidence(str, Enum):
    CONFIRMED = "confirmed"   # a tool reported it (parser, linter, test run, scanner)
    LIKELY = "likely"         # a deterministic pattern that is usually a real problem
    SUSPECTED = "suspected"   # a heuristic that needs a person or a measurement to confirm


class Category(str, Enum):
    SYNTAX = "syntax"
    QUALITY = "quality"
    TESTS = "tests"
    DEPENDENCIES = "dependencies"
    SECURITY = "security"
    MAINTAINABILITY = "maintainability"
    PERFORMANCE = "performance"


class FindingStatus(str, Enum):
    OPEN = "open"
    PLANNED = "planned"
    FIXED_VERIFIED = "fixed_verified"   # no longer detected after a change that passed its checks
    FIX_FAILED = "fix_failed"
    DISMISSED = "dismissed"
    RESOLVED = "resolved"               # no longer detected by a later analysis


class Finding(BaseModel):
    id: str
    project_id: str
    rule_id: str
    analyzer: str
    category: Category
    title: str
    description: str
    severity: Severity
    confidence: Confidence
    file: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    evidence: str = ""
    remediation: str = ""
    validation: str = ""
    fix_strategy: str = "manual"        # ruff_fix | add_requirements | import_repair | model | manual
    detected_at: str = Field(default_factory=now_iso)
    first_seen: str = Field(default_factory=now_iso)
    last_seen: str = Field(default_factory=now_iso)
    status: FindingStatus = FindingStatus.OPEN
    priority: str = "P4"
    priority_reasons: List[str] = Field(default_factory=list)


class ToolRun(BaseModel):
    tool: str
    status: str          # ran | unavailable | blocked | error | skipped
    detail: str = ""


class Analysis(BaseModel):
    id: str
    project_id: str
    user_id: str
    status: str = "queued"               # queued | running | completed | failed
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    project_map: Dict[str, Any] = Field(default_factory=dict)
    tools: List[ToolRun] = Field(default_factory=list)
    finding_ids: List[str] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class PlanStatus(str, Enum):
    DRAFT = "draft"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PlanTask(BaseModel):
    id: str
    title: str
    finding_ids: List[str]
    files: List[str]
    modification: str
    strategy: str
    agent: str
    depends_on: List[str] = Field(default_factory=list)
    request: str = ""                    # a change request (Digital Twin plans) instead of findings to fix
    context_files: List[str] = Field(default_factory=list)   # read-only context shown to the model


class Decision(BaseModel):
    decision: str            # approved | rejected | cancelled | scope_approved
    user_id: str
    at: str = Field(default_factory=now_iso)
    note: str = ""


class Plan(BaseModel):
    id: str
    project_id: str
    user_id: str
    objective: str
    finding_ids: List[str]
    tasks: List[PlanTask]
    expected_files: List[str]
    agents: List[str]
    checks: List[str]
    risks: List[str]
    assumptions: List[str]
    approval_required: List[str]
    completion_criteria: List[str]
    status: PlanStatus = PlanStatus.AWAITING_APPROVAL
    decisions: List[Decision] = Field(default_factory=list)
    created_at: str = Field(default_factory=now_iso)
    origin: str = "findings"             # findings | digital_twin
    origin_ref: Optional[str] = None     # the Digital Twin impact report it came from
    security_review_required: bool = False   # approval must acknowledge a security review


class CheckResult(BaseModel):
    check_id: str
    label: str
    environment: str
    started_at: str
    finished_at: str
    status: str               # passed | failed | blocked | error | not_run
    exit_code: Optional[int] = None
    counts: Dict[str, int] = Field(default_factory=dict)
    output: str = ""


class Stage(BaseModel):
    name: str
    status: str = "pending"   # pending | running | done | failed | skipped
    at: Optional[str] = None
    detail: str = ""


class TaskResult(BaseModel):
    task_id: str
    status: str               # applied | no_changes | out_of_scope | failed | skipped
    files: List[str] = Field(default_factory=list)
    outside: List[str] = Field(default_factory=list)   # out_of_scope: the files the plan did not list
    detail: str = ""
    attempts: int = 0


class Execution(BaseModel):
    id: str
    plan_id: str
    project_id: str
    user_id: str
    status: str = "queued"    # queued | running | completed | rejected | failed | cancelled | needs_approval
    stages: List[Stage] = Field(default_factory=list)
    baseline: List[CheckResult] = Field(default_factory=list)
    after: List[CheckResult] = Field(default_factory=list)
    task_results: List[TaskResult] = Field(default_factory=list)
    changed_files: List[str] = Field(default_factory=list)
    diff: str = ""
    verdict: Dict[str, Any] = Field(default_factory=dict)
    verified_findings: List[str] = Field(default_factory=list)
    unresolved_findings: List[str] = Field(default_factory=list)
    applied_to_project: bool = False
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    error: Optional[str] = None
    cancel_requested: bool = False
