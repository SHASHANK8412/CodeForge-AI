"""
AIForge V2 – Planner Agent Data Models
======================================
Data structures for Requirements, User Personas, User Stories, Acceptance Criteria,
MVP Definitions, Sprint Plans, Risk Analysis, and Technical Recommendations.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class RequirementPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RiskSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BusinessAnalysis(BaseModel):
    project_name: str
    business_goal: str
    target_users: List[str]
    core_features: List[str]
    expected_scale: str = "Standard Scalable Multi-Tenant Tier"
    platforms: List[str] = Field(default_factory=lambda: ["Web SPA (React)", "REST API (FastAPI)"])


class FunctionalRequirement(BaseModel):
    id: str
    title: str
    description: str
    priority: RequirementPriority = RequirementPriority.HIGH


class NonFunctionalRequirement(BaseModel):
    category: str  # Performance, Security, Scalability, Availability
    description: str
    target_metric: str


class UserPersona(BaseModel):
    name: str
    role: str
    goals: List[str]
    pain_points: List[str]
    needs: List[str]


class AcceptanceCriteria(BaseModel):
    given: str
    when_event: str
    then_outcome: str


class UserStory(BaseModel):
    id: str
    persona: str
    i_want_to: str
    so_that: str
    priority: RequirementPriority = RequirementPriority.HIGH
    acceptance_criteria: List[AcceptanceCriteria] = Field(default_factory=list)


class PrioritizedFeature(BaseModel):
    feature_name: str
    priority: RequirementPriority
    mvp_version: str = "V1 (Must Have)"


class MVPDefinition(BaseModel):
    v1_must_have: List[str]
    v2_should_have: List[str]
    v3_nice_to_have: List[str]


class SprintPlan(BaseModel):
    sprint_number: int
    sprint_name: str
    duration_weeks: int = 2
    focus_area: str
    deliverables: List[str]


class RiskItem(BaseModel):
    risk_type: str  # Technical, Business, Security, Performance
    description: str
    severity: RiskSeverity
    mitigation: str


class TechRecommendation(BaseModel):
    layer: str  # Frontend, Backend, Database, Cache, LLM, Infra
    technology: str
    justification: str


class PlannerReport(BaseModel):
    project_id: str
    project_name: str
    business_analysis: BusinessAnalysis
    functional_requirements: List[FunctionalRequirement]
    non_functional_requirements: List[NonFunctionalRequirement]
    user_personas: List[UserPersona]
    user_stories: List[UserStory]
    prioritized_features: List[PrioritizedFeature]
    mvp_definition: MVPDefinition
    sprint_plan: List[SprintPlan]
    risk_analysis: List[RiskItem]
    tech_recommendations: List[TechRecommendation]
    architecture_recommendation: str = "Decoupled REST API + Micro-Frontend Architecture"
