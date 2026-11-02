"""
AIForge V2 — Security Foundation Pydantic Data Models
=====================================================
Models for Security Findings, Secret Detection, Prompt Injection Guards,
Dependency Vulnerability Audits, Docker Sandbox Execution, and Security Audit Logs.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class FindingStatus(str, Enum):
    OPEN = "OPEN"
    FIXED = "FIXED"
    ACCEPTED = "ACCEPTED"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class SecretFinding(BaseModel):
    type: str  # e.g., API_KEY, DATABASE_URL, PRIVATE_KEY, JWT_SECRET, AWS_CREDENTIAL
    file: str
    line: Optional[int] = None
    severity: Severity = Severity.CRITICAL
    message: str
    redacted_sample: str


class PromptGuardResult(BaseModel):
    risk: str = Field(..., description="HIGH, MEDIUM, LOW")
    source: str
    reason: str
    flagged_terms: List[str] = Field(default_factory=list)


class DependencyVulnerability(BaseModel):
    package_name: str
    installed_version: str
    vulnerability_id: str
    severity: Severity
    summary: str


class DependencyScanResult(BaseModel):
    total: int = 0
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    vulnerabilities: List[DependencyVulnerability] = Field(default_factory=list)
    status_message: str = "Dependency scan complete"


class SandboxResult(BaseModel):
    execution_id: str
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    memory_used_mb: float
    cpu_percent: float
    timed_out: bool = False


class SecurityFinding(BaseModel):
    id: str
    severity: Severity
    category: str  # AUTH, INJECTION, SECRET, XSS, PATH_TRAVERSAL, DESERIALIZATION, CORS
    title: str
    file: str
    line: Optional[int] = None
    message: str
    evidence: str
    recommendation: str
    blocking: bool = True
    status: FindingStatus = FindingStatus.OPEN
    false_positive_reason: Optional[str] = None
    marked_by: Optional[str] = None
    timestamp: str = ""


class SecurityReport(BaseModel):
    project_id: str
    security_score: float = 100.0  # Derived 0-100 score
    decision: str = "PASS"  # PASS, WARN, BLOCK
    total_findings: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    findings: List[SecurityFinding] = Field(default_factory=list)
    secrets: List[SecretFinding] = Field(default_factory=list)
    dependency_summary: Optional[DependencyScanResult] = None
    scanned_at: str = ""


class SecurityAuditEvent(BaseModel):
    id: str
    event_type: str  # security_scan_started, secret_detected, vulnerability_detected, deployment_blocked, etc.
    project_id: str
    user_id: str
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str
