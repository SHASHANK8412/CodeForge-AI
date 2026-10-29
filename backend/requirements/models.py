"""
AIForge Product Intelligence & Requirements Schema
==================================================
Canonical Pydantic models for software requirements, user stories, acceptance criteria,
traceability matrices, change impact analysis, and project specifications.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class Requirement(BaseModel):
    id: str  # FR-001, NFR-001, SEC-001, DATA-001, BR-001
    category: str  # FUNCTIONAL, NON_FUNCTIONAL, SECURITY, DATA, BUSINESS_RULE, INTEGRATION
    title: str
    description: str
    priority: str = "HIGH"  # CRITICAL, HIGH, MEDIUM, LOW
    is_implemented: bool = False
    is_tested: bool = False
    is_verified: bool = False


class UserStory(BaseModel):
    id: str  # US-001
    as_a: str
    i_want: str
    so_that: str
    requirement_ids: List[str] = Field(default_factory=list)


class AcceptanceCriteria(BaseModel):
    id: str  # AC-001
    user_story_id: str
    given: str
    when: str
    then: str
    requirement_ids: List[str] = Field(default_factory=list)
    passed: bool = False


class TraceabilityItem(BaseModel):
    requirement_id: str
    user_story_ids: List[str] = Field(default_factory=list)
    acceptance_criteria_ids: List[str] = Field(default_factory=list)
    implementation_files: List[str] = Field(default_factory=list)
    test_files: List[str] = Field(default_factory=list)
    status: str = "NOT_IMPLEMENTED"  # NOT_IMPLEMENTED, IMPLEMENTED, TESTED, VERIFIED


class AmbiguityQuestion(BaseModel):
    id: str
    category: str
    question: str
    options: List[str] = Field(default_factory=list)
    importance: str = "HIGH"  # CRITICAL, HIGH, MEDIUM, LOW
    default_choice: str = ""


class ProjectSpecification(BaseModel):
    project_name: str
    project_type: str = "Full-Stack Web Application"
    version: str = "1.0"
    target_users: List[str] = Field(default_factory=list)
    functional_requirements: List[Requirement] = Field(default_factory=list)
    non_functional_requirements: List[Requirement] = Field(default_factory=list)
    security_requirements: List[Requirement] = Field(default_factory=list)
    data_requirements: List[Requirement] = Field(default_factory=list)
    business_rules: List[Requirement] = Field(default_factory=list)
    user_stories: List[UserStory] = Field(default_factory=list)
    acceptance_criteria: List[AcceptanceCriteria] = Field(default_factory=list)
    traceability_matrix: List[TraceabilityItem] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    open_questions: List[AmbiguityQuestion] = Field(default_factory=list)
    coverage_score: float = 0.0


class ChangeImpact(BaseModel):
    new_requirements: List[Requirement] = Field(default_factory=list)
    affected_files: List[str] = Field(default_factory=list)
    affected_agents: List[str] = Field(default_factory=list)
    affected_tests: List[str] = Field(default_factory=list)
    requires_full_regeneration: bool = False
    estimated_files_count: int = 0
