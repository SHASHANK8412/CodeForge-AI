"""
AIForge Day 19 — Autonomous Production Readiness Gate Pydantic Data Models
===========================================================================
Models for Readiness Checks, Reports, Statuses, Severities, CTO Executive Reviews,
Historical Snapshots, and Readiness Version Diffs.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ReadinessStatus(str, Enum):
    READY = "READY"
    READY_WITH_WARNINGS = "READY_WITH_WARNINGS"
    BLOCKED = "BLOCKED"
    INCOMPLETE = "INCOMPLETE"


class CheckSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class CheckStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    NOT_AVAILABLE = "NOT_AVAILABLE"


class ReadinessCheck(BaseModel):
    id: str
    category: str  # Requirements, Security, Testing, Browser Testing, Performance, Architecture, Code Quality, Database, Documentation, Deployment, Observability, Secrets, Dependencies
    name: str
    status: CheckStatus = CheckStatus.PASS
    severity: CheckSeverity = CheckSeverity.LOW
    score: float = 100.0
    evidence: str
    blocking: bool = False
    recommendation: Optional[str] = None
    timestamp: str = ""


class CTOReview(BaseModel):
    recommendation: ReadinessStatus = ReadinessStatus.READY
    executive_summary: str
    major_risks: List[str] = Field(default_factory=list)
    required_actions: List[str] = Field(default_factory=list)


class ReadinessReport(BaseModel):
    report_id: str
    project_id: str
    generation_id: str = "aiforge-demo"
    version: int = 1
    status: ReadinessStatus = ReadinessStatus.READY
    overall_score: float = 96.0
    checks: List[ReadinessCheck] = Field(default_factory=list)
    blocking_issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    cto_review: Optional[CTOReview] = None
    approval_status: str = "PENDING"  # PENDING, APPROVED, REJECTED
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    created_at: str = ""


class ReadinessHistory(BaseModel):
    project_id: str
    snapshots: List[ReadinessReport] = Field(default_factory=list)


class ReadinessDiff(BaseModel):
    old_version: int
    new_version: int
    score_change: float = 0.0
    old_status: ReadinessStatus
    new_status: ReadinessStatus
    resolved_blockers: List[str] = Field(default_factory=list)
    new_warnings: List[str] = Field(default_factory=list)
