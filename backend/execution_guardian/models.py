"""
Execution Guardian records.

  Check         one validation check: status PENDING | RUNNING | PASSED | FAILED | BLOCKED | SKIPPED
                (BLOCKED = the check could not run, e.g. no isolated environment; SKIPPED = not applicable or not
                present - never counted as passed)
  Failure       one classified failure, with the log excerpt it rests on and the agent it is routed to
  RepairAttempt one bounded repair: the agent, the strategy, files changed / rejected, checks before and after
  Verification  the run: VERIFIED only when every required check actually passed; VERIFIED_WITH_WARNINGS when
                they passed but something applicable was skipped or optional checks reported issues; FAILED;
                BLOCKED when a required check could not run and none failed
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from backend.evolution.autopilot.models import now_iso

CHECK_STATUSES = ("PENDING", "RUNNING", "PASSED", "FAILED", "BLOCKED", "SKIPPED")
FINAL_STATUSES = ("VERIFIED", "VERIFIED_WITH_WARNINGS", "FAILED", "BLOCKED")
CATEGORIES = ("syntax_error", "compilation_error", "dependency_install_error", "frontend_build_error",
              "backend_startup_error", "database_connection_error", "api_contract_mismatch", "unit_test_failure",
              "integration_test_failure", "configuration_error", "runtime_exception", "infrastructure_error")


class Check(BaseModel):
    name: str                                    # python_syntax | quality_gate | security_static | python_dependencies
                                                 # | python_tests | backend_startup | frontend_dependencies
                                                 # | frontend_build | frontend_tests | api_contract
    label: str
    required: bool = True
    status: str = "PENDING"
    profile: str = ""                            # the controlled execution profile used (never a command from the project)
    environment: str = ""
    started_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    exit_code: Optional[int] = None
    timed_out: bool = False
    counts: Dict[str, int] = Field(default_factory=dict)
    error_summary: str = ""
    log_excerpt: str = ""                        # real output (redacted), never invented
    reason: str = ""                             # why it was skipped or blocked
    provenance: str = ""                         # what produced the result (this run, or the workflow's testing node)


class Failure(BaseModel):
    id: str
    check: str
    category: str                                # CATEGORIES
    severity: str                                # critical | high | medium
    summary: str
    log_excerpt: str = ""
    files: List[str] = Field(default_factory=list)
    failing_tests: List[str] = Field(default_factory=list)
    responsible_agent: Optional[str] = None      # frontend | backend | database | debug | architect | dependency_resolver
    classified_by: str = "rule"                  # rule (with its name) | model (labelled) | fallback
    next_action: str = ""
    signature: str = ""                          # category + check + normalised message, to detect repeats
    repairable: bool = True
    attempt: int = 0                             # the verification round that observed it


class RepairAttempt(BaseModel):
    attempt: int
    failure_ids: List[str]
    agent: str
    strategy: str                                # deterministic strategy name | model:<agent>
    started_at: str = Field(default_factory=now_iso)
    finished_at: Optional[str] = None
    files_changed: List[str] = Field(default_factory=list)
    rejected_paths: List[Dict[str, str]] = Field(default_factory=list)
    before: Dict[str, str] = Field(default_factory=dict)       # check -> status before the repair
    after: Dict[str, str] = Field(default_factory=dict)        # check -> status after
    resolved: List[str] = Field(default_factory=list)          # failure signatures that disappeared
    new_failures: List[str] = Field(default_factory=list)      # failures the repair introduced
    rolled_back: bool = False
    outcome: str = "pending"                     # improved | resolved | no_change | regressed | no_fix | rejected
    note: str = ""


class Verification(BaseModel):
    id: str
    project_id: str
    user_id: str
    source: str = "api"                          # api (isolated working copy) | workflow (the generation graph)
    status: str = "RUNNING"                      # RUNNING | VERIFIED | VERIFIED_WITH_WARNINGS | FAILED | BLOCKED | CANCELLED
    current_operation: str = "queued"
    stack: Dict[str, Any] = Field(default_factory=dict)
    settings: Dict[str, Any] = Field(default_factory=dict)
    checks: List[Check] = Field(default_factory=list)
    original_checks: List[Check] = Field(default_factory=list)  # the first round, preserved
    failures: List[Failure] = Field(default_factory=list)       # current (latest round)
    original_failures: List[Failure] = Field(default_factory=list)
    repairs: List[RepairAttempt] = Field(default_factory=list)
    activity: List[Dict[str, Any]] = Field(default_factory=list)
    report: Dict[str, Any] = Field(default_factory=dict)
    delivery: Dict[str, Any] = Field(default_factory=dict)
    started_at: str = Field(default_factory=now_iso)
    finished_at: Optional[str] = None
    cancel_requested: bool = False
    error: Optional[str] = None
