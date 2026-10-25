"""
AIForge Day 21 — Autonomous Incident Response & Self-Healing Pydantic Data Models
===================================================================================
Models for Incidents, Incident Types, Statuses, Severities, Remediation Plans,
Autonomy Policies, Timelines, Metrics, and Post-Incident Reports.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class IncidentType(str, Enum):
    APPLICATION_ERROR = "APPLICATION_ERROR"
    API_FAILURE = "API_FAILURE"
    DATABASE_FAILURE = "DATABASE_FAILURE"
    PERFORMANCE_REGRESSION = "PERFORMANCE_REGRESSION"
    FRONTEND_FAILURE = "FRONTEND_FAILURE"
    AUTHENTICATION_FAILURE = "AUTHENTICATION_FAILURE"
    DEPLOYMENT_FAILURE = "DEPLOYMENT_FAILURE"
    HEALTH_CHECK_FAILURE = "HEALTH_CHECK_FAILURE"
    DEPENDENCY_FAILURE = "DEPENDENCY_FAILURE"
    RESOURCE_EXHAUSTION = "RESOURCE_EXHAUSTION"


class IncidentStatus(str, Enum):
    DETECTED = "DETECTED"
    INVESTIGATING = "INVESTIGATING"
    DIAGNOSED = "DIAGNOSED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    REPAIRING = "REPAIRING"
    VALIDATING = "VALIDATING"
    RESOLVED = "RESOLVED"
    ROLLED_BACK = "ROLLED_BACK"
    ESCALATED = "ESCALATED"
    CLOSED = "CLOSED"


class IncidentSeverity(str, Enum):
    P0 = "P0"  # Complete service outage or critical security issue
    P1 = "P1"  # Major feature unavailable
    P2 = "P2"  # Limited functionality degradation
    P3 = "P3"  # Minor issue


class AutonomyPolicy(str, Enum):
    MANUAL = "MANUAL"
    ASSISTED = "ASSISTED"
    BALANCED = "BALANCED"
    FULL_AUTONOMY = "FULL_AUTONOMY"


class IncidentTimelineEvent(BaseModel):
    timestamp: str
    stage: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class RemediationPlan(BaseModel):
    plan_id: str
    incident_id: str
    title: str
    description: str
    affected_files: List[str] = Field(default_factory=list)
    proposed_code_changes: Dict[str, str] = Field(default_factory=dict)
    risk_level: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    requires_approval: bool = True
    validation_steps: List[str] = Field(default_factory=list)


class Incident(BaseModel):
    id: str
    project_id: str
    deployment_id: str = "dep_live"
    version: int = 1
    type: IncidentType = IncidentType.API_FAILURE
    severity: IncidentSeverity = IncidentSeverity.P1
    status: IncidentStatus = IncidentStatus.DETECTED
    detected_at: str = ""
    resolved_at: Optional[str] = None
    symptoms: List[str] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    affected_components: List[str] = Field(default_factory=list)
    root_cause: Optional[str] = None
    remediation: Optional[RemediationPlan] = None
    approval_status: str = "PENDING"  # PENDING, APPROVED, REJECTED
    rollback_status: Optional[str] = None
    timeline: List[IncidentTimelineEvent] = Field(default_factory=list)


class IncidentMetrics(BaseModel):
    mttd_minutes: float = 1.2
    mttr_minutes: float = 8.5
    total_incidents: int = 4
    resolved_automatically: int = 3
    resolved_manually: int = 1
    rollback_count: int = 1
    repeated_incidents_count: int = 0


class PostIncidentReport(BaseModel):
    incident_id: str
    project_id: str
    title: str
    severity: IncidentSeverity
    duration_minutes: float
    root_cause_summary: str
    impact_summary: str
    detection_source: str
    resolution_method: str
    prevention_recommendations: List[str] = Field(default_factory=list)
    created_at: str = ""
