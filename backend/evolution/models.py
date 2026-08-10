"""
AIForge Day 24 — Autonomous Software Evolution Engine Pydantic Data Models
=============================================================================
Models for Technical Debt Categories, Debt Severities, Debt Statuses, Technical Debt Items,
Technical Debt Scores, Evolution Recommendations, Roadmaps, Analysis Results, and History Records.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class TechnicalDebtCategory(str, Enum):
    CODE_QUALITY = "CODE_QUALITY"
    ARCHITECTURE = "ARCHITECTURE"
    TESTING = "TESTING"
    SECURITY = "SECURITY"
    MAINTAINABILITY = "MAINTAINABILITY"
    PERFORMANCE = "PERFORMANCE"
    DEPENDENCY = "DEPENDENCY"
    OBSERVABILITY = "OBSERVABILITY"


class DebtSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class DebtStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    ACCEPTED = "ACCEPTED"
    WONT_FIX = "WONT_FIX"


class TechnicalDebtItem(BaseModel):
    id: str
    project_id: str
    category: TechnicalDebtCategory = TechnicalDebtCategory.CODE_QUALITY
    title: str
    description: str
    severity: DebtSeverity = DebtSeverity.MEDIUM
    effort: str = "MEDIUM"  # LOW, MEDIUM, HIGH
    impact: str = "HIGH"    # LOW, MEDIUM, HIGH
    risk: str = "LOW"        # LOW, MEDIUM, HIGH
    affected_files: List[str] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    recommendation: str = ""
    status: DebtStatus = DebtStatus.OPEN
    created_at: str = ""
    updated_at: str = ""


class TechnicalDebtScore(BaseModel):
    code_quality_score: float = 82.0
    architecture_score: float = 76.0
    testing_score: float = 91.0
    security_score: float = 96.0
    maintainability_score: float = 79.0
    overall_score: float = 84.8


class EvolutionRecommendation(BaseModel):
    id: str
    project_id: str
    category: TechnicalDebtCategory = TechnicalDebtCategory.PERFORMANCE
    title: str
    description: str
    impact: str = "HIGH"    # LOW, MEDIUM, HIGH
    effort: str = "MEDIUM"  # LOW, MEDIUM, HIGH
    risk: str = "LOW"        # LOW, MEDIUM, HIGH
    priority_score: float = 85.0
    roadmap_phase: str = "NOW"  # NOW, NEXT, LATER
    affected_files: List[str] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    recommended_action: str = ""
    status: str = "OPEN"  # OPEN, IN_PROGRESS, COMPLETED, REJECTED


class EvolutionRoadmap(BaseModel):
    project_id: str
    health_score: float = 89.0
    debt_level: str = "MEDIUM"
    security_risk: str = "LOW"
    performance_risk: str = "MEDIUM"
    architecture_risk: str = "MEDIUM"
    testing_level: str = "GOOD"
    now: List[EvolutionRecommendation] = Field(default_factory=list)
    next_phase: List[EvolutionRecommendation] = Field(default_factory=list)
    later: List[EvolutionRecommendation] = Field(default_factory=list)


class EvolutionAnalysisResult(BaseModel):
    project_id: str
    debt_score: TechnicalDebtScore
    debt_items: List[TechnicalDebtItem] = Field(default_factory=list)
    roadmap: EvolutionRoadmap
    analyzed_at: str = ""


class EvolutionHistoryRecord(BaseModel):
    id: str
    project_id: str
    timestamp: str
    health_score: float
    debt_score: float
    recommendation_title: str
    before_metrics: Dict[str, Any] = Field(default_factory=dict)
    after_metrics: Dict[str, Any] = Field(default_factory=dict)
    status: str = "COMPLETED"
