"""
Records of the AIForge Security Guardian.

Verification states keep detection, proof and repair apart:
  detected                  a rule or scanner matched (static evidence only)
  requires_review           a pattern that needs a person to judge (context the analysis cannot see)
  verification_in_progress  a safe verification is running in the sandbox
  verified                  a bounded, benign test against a disposable copy showed the issue
  not_reproduced            the verification ran and did not show the issue
  verification_unavailable  no safe automated verification exists for this finding (or it could not run)
  fixed                     an approved change addressing it was applied (not yet re-verified)
  fix_verified              after the change, the same verification no longer shows the issue
  accepted_risk             a person accepted the risk
A rule match never makes a finding "verified"; a generated patch never makes it "fixed".
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from backend.evolution.autopilot.models import now_iso

STATES = ("detected", "requires_review", "verification_in_progress", "verified", "not_reproduced", "fixed",
          "fix_verified", "accepted_risk", "verification_unavailable")
CATEGORIES = ("injection", "auth", "secrets", "web", "dependencies", "configuration", "crypto")


class Evidence(BaseModel):
    source: str                                  # rule id / scanner name / verification
    detail: str
    file: Optional[str] = None
    line: Optional[int] = None


class Verification(BaseModel):
    method: str                                  # what was sent and what counts as proof
    preconditions: List[str] = Field(default_factory=list)
    status: str = "pending"                      # pending | running | verified | not_reproduced | unavailable | error | aborted
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    requests: List[Dict[str, Any]] = Field(default_factory=list)   # benign requests and the (redacted) answers
    conclusion: str = ""
    limitations: List[str] = Field(default_factory=list)


class Finding(BaseModel):
    id: str
    project_id: str
    rule_id: str
    category: str
    title: str
    description: str
    severity: str                                # critical | high | medium | low | info
    confidence: str                              # high | medium | low
    file: Optional[str] = None
    line: Optional[int] = None
    route: Optional[str] = None                  # "METHOD /path" when the code belongs to a route handler
    component: Optional[str] = None
    evidence: List[Evidence] = Field(default_factory=list)
    detection: List[str] = Field(default_factory=list)       # independent sources that reported it
    state: str = "detected"
    impact: str = ""
    remediation: str = ""
    dependencies: List[str] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)     # CWE / advisory ids
    verifiable: Optional[str] = None             # verification kind, if a safe automated one exists
    verification: Optional[Verification] = None
    priority: str = "P4"
    priority_reasons: List[str] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)    # Twin: exposure, auth boundary, dependents
    first_seen: str = Field(default_factory=now_iso)
    last_seen: str = Field(default_factory=now_iso)
    last_verified: Optional[str] = None
    accepted_by: Optional[str] = None
    accepted_note: str = ""


class ToolRun(BaseModel):
    tool: str
    status: str                                  # ran | partial | unavailable | error | skipped
    detail: str = ""
    version: Optional[str] = None
    retrieved_at: Optional[str] = None           # advisory data retrieval time


class Assessment(BaseModel):
    id: str
    project_id: str
    user_id: str
    status: str = "queued"     # queued | analyzing | verifying | awaiting_approval | completed | failed | aborted | inconclusive
    created_at: str = Field(default_factory=now_iso)
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    tools: List[ToolRun] = Field(default_factory=list)
    finding_ids: List[str] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)
    coverage: Dict[str, Any] = Field(default_factory=dict)  # what was and was not analyzed
    verification_requested: bool = False
    verification_ids: List[str] = Field(default_factory=list)
    audit: List[Dict[str, Any]] = Field(default_factory=list)
    abort_requested: bool = False
    error: Optional[str] = None


class Gate(BaseModel):
    """A remediation's security re-check: the same verification on the original and the changed copy."""
    id: str                                      # the Autopilot execution
    project_id: str
    finding_id: str
    created_at: str = Field(default_factory=now_iso)
    decision: str = "not_measured"               # improved | regressed | inconclusive | not_measured
    reasons: List[str] = Field(default_factory=list)
    original: Optional[Verification] = None
    changed: Optional[Verification] = None
