"""
AIForge V2 — Day 15 Engineering Autopilot Models
=================================================
Data models for Autonomy Levels, Decision Cards, Approval Requests, and Flight Recorder.
"""

import time
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class AutonomyLevel(str, Enum):
    ASSISTED = "ASSISTED"
    BALANCED = "BALANCED"
    FULL_AUTONOMY = "FULL_AUTONOMY"


class AutopilotStatus(str, Enum):
    IDLE = "IDLE"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    STOPPED = "STOPPED"


class DecisionType(str, Enum):
    PLANNING = "PLANNING"
    ARCHITECTURE = "ARCHITECTURE"
    REVIEW = "REVIEW"
    REPAIR = "REPAIR"
    TESTING = "TESTING"
    QUALITY = "QUALITY"
    SECURITY = "SECURITY"
    DEPLOYMENT = "DEPLOYMENT"


class DecisionCardData(BaseModel):
    id: str
    generation_id: str
    type: DecisionType
    title: str
    summary: str
    reason: str
    evidence: List[str] = Field(default_factory=list)
    impact: str = ""
    confidence: Optional[float] = Field(default=None, description="Confidence score 0.0-1.0 or None if unavailable")
    timestamp: str = Field(default_factory=lambda: time.strftime("%H:%M:%S"))
    sources: List[str] = Field(default_factory=list, description="RAG and Memory citations")


class ApprovalRequest(BaseModel):
    id: str
    generation_id: str
    action: str
    reason: str
    status: str = Field(default="PENDING", description="PENDING, APPROVED, REJECTED")
    created_at: str = Field(default_factory=lambda: time.strftime("%H:%M:%S"))


class FlightRecorderEvent(BaseModel):
    id: str
    generation_id: str
    project_id: str
    stage: str  # PLAN, ARCHITECT, BUILD, REVIEW, TEST, REPAIR, OPTIMIZE, DEPLOY
    agent: str
    event_type: str
    decision: Optional[str] = None
    reason: Optional[str] = None
    files_changed: List[str] = Field(default_factory=list)
    quality_before: Optional[float] = None
    quality_after: Optional[float] = None
    test_before: Optional[int] = None
    test_after: Optional[int] = None
    timestamp: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
