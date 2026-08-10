"""
AIForge Day 23 — AI Codebase Copilot & Natural-Language Software Control Pydantic Data Models
=============================================================================================
Models for Copilot Intents, Action Categories, Requests, Contexts, Plans, Action Results, Sessions,
Progress Steps, and Feedback.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class CopilotIntent(str, Enum):
    QUESTION = "QUESTION"
    EXPLANATION = "EXPLANATION"
    ANALYSIS = "ANALYSIS"
    MODIFICATION = "MODIFICATION"
    DEBUGGING = "DEBUGGING"
    TESTING = "TESTING"
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"
    DEPLOYMENT = "DEPLOYMENT"
    INCIDENT = "INCIDENT"
    ARCHITECTURE = "ARCHITECTURE"
    SEARCH = "SEARCH"
    WHAT_IF = "WHAT_IF"


class ActionCategory(str, Enum):
    READ_ONLY = "READ_ONLY"
    SAFE_ACTION = "SAFE_ACTION"
    MUTATING_ACTION = "MUTATING_ACTION"
    HIGH_RISK_ACTION = "HIGH_RISK_ACTION"


class CopilotProgressStep(BaseModel):
    step: str
    status: str = "IN_PROGRESS"  # IN_PROGRESS, COMPLETED, FAILED
    details: str = ""


class CopilotContext(BaseModel):
    project_id: str
    files: List[str] = Field(default_factory=list)
    dna_nodes: List[str] = Field(default_factory=list)
    memories: List[str] = Field(default_factory=list)
    rag_docs: List[str] = Field(default_factory=list)
    recent_git_commits: List[str] = Field(default_factory=list)
    test_results: Dict[str, Any] = Field(default_factory=dict)
    security_findings: Dict[str, Any] = Field(default_factory=dict)
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)
    active_incidents: List[str] = Field(default_factory=list)
    readiness_score: float = 92.0
    deployment_status: str = "READY"


class CopilotPlan(BaseModel):
    plan_id: str
    request: str
    intent: CopilotIntent
    action_category: ActionCategory
    summary: str
    affected_files: List[str] = Field(default_factory=list)
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL
    requires_approval: bool = False
    validation_pipeline: List[str] = Field(default_factory=list)
    proposed_changes: Dict[str, str] = Field(default_factory=dict)


class CopilotActionResult(BaseModel):
    action_id: str
    plan_id: str
    status: str  # COMPLETED, BLOCKED, ROLLED_BACK, FAILED
    message: str
    execution_time_ms: float = 0.0
    validation_evidence: Dict[str, Any] = Field(default_factory=dict)
    artifacts: List[str] = Field(default_factory=list)


class CopilotMessage(BaseModel):
    id: str
    sender: str  # USER, COPILOT, SYSTEM
    text: str
    timestamp: str = ""
    intent: Optional[CopilotIntent] = None
    action_category: Optional[ActionCategory] = None
    plan: Optional[CopilotPlan] = None
    result: Optional[CopilotActionResult] = None
    action_buttons: List[Dict[str, str]] = Field(default_factory=list)
    context_used: Optional[CopilotContext] = None


class CopilotSession(BaseModel):
    session_id: str
    project_id: str
    created_at: str = ""
    messages: List[CopilotMessage] = Field(default_factory=list)


class CopilotFeedback(BaseModel):
    session_id: str
    message_id: str
    rating: str  # USEFUL, NOT_USEFUL, INCORRECT
    comment: Optional[str] = None
