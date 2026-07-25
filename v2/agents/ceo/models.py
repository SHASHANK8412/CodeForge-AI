"""
AIForge V2 – CEO Agent Data Models
===================================
Models for project classification, complexity estimation, resource allocation, and team selection.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ComplexityTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    ENTERPRISE = "enterprise"


class ProjectPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CEOProjectEvaluation(BaseModel):
    project_name: str
    client_prompt: str
    complexity_tier: ComplexityTier
    complexity_score: float = Field(..., ge=1.0, le=10.0)
    priority: ProjectPriority = ProjectPriority.HIGH
    estimated_duration_days: float
    frontend_tech: str = "React"
    backend_tech: str = "FastAPI"
    database_tech: str = "PostgreSQL"
    ai_tech: Optional[str] = "Ollama / Qwen2.5-Coder"
    deployment_tech: str = "Docker"
    required_teams: List[str]
    risks: List[str] = Field(default_factory=list)
    suggested_architecture: str = "Decoupled FastAPI backend & React frontend with PostgreSQL DB"
