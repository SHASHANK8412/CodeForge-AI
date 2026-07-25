"""
AIForge V2 – Enterprise Database Schema & ORM Models (PostgreSQL / SQLAlchemy)
================================================================================
Models for:
- Projects, Tasks, Agents, Messages
- Logs, Events, Deployments
- Knowledge, Embeddings, Users, Sessions, Metrics
"""

import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pydantic import BaseModel, Field


class ProjectRecord(BaseModel):
    id: str
    name: str
    client_prompt: str
    complexity_score: float
    status: str = "active"
    created_at: float = Field(default_factory=time.time)


class TaskRecord(BaseModel):
    id: str
    project_id: str
    assigned_agent: str
    title: str
    status: str = "pending"
    created_at: float = Field(default_factory=time.time)


class AgentRecord(BaseModel):
    id: str
    role: str
    status: str = "idle"
    tasks_completed: int = 0
    created_at: float = Field(default_factory=time.time)


class MessageRecord(BaseModel):
    id: str
    sender: str
    recipient: str
    payload: Dict[str, Any]
    timestamp: float = Field(default_factory=time.time)


class LogRecord(BaseModel):
    id: str
    agent_name: str
    execution_time_ms: float
    tokens_used: int
    errors: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)


class EventRecord(BaseModel):
    id: str
    topic: str
    sender: str
    payload: Dict[str, Any]
    timestamp: float = Field(default_factory=time.time)


class DeploymentRecord(BaseModel):
    id: str
    project_id: str
    target_platform: str = "docker"
    status: str = "deployed"
    timestamp: float = Field(default_factory=time.time)


class KnowledgeRecord(BaseModel):
    id: str
    category: str
    problem: str
    solution: str
    times_used: int = 1
    timestamp: float = Field(default_factory=time.time)


class EmbeddingRecord(BaseModel):
    id: str
    text_content: str
    vector_dims: int = 384
    timestamp: float = Field(default_factory=time.time)


class UserRecord(BaseModel):
    id: str
    username: str
    role: str = "admin"
    created_at: float = Field(default_factory=time.time)


class SessionRecord(BaseModel):
    id: str
    user_id: str
    token: str
    created_at: float = Field(default_factory=time.time)


class MetricRecord(BaseModel):
    id: str
    metric_name: str
    value: float
    timestamp: float = Field(default_factory=time.time)


class RequirementRecord(BaseModel):
    id: str
    project_id: str
    type: str  # functional, non_functional
    description: str
    priority: str = "high"
    created_at: float = Field(default_factory=time.time)


class UserStoryRecord(BaseModel):
    id: str
    project_id: str
    persona: str
    story: str
    status: str = "backlog"
    created_at: float = Field(default_factory=time.time)


class SprintRecord(BaseModel):
    id: str
    project_id: str
    name: str
    duration_weeks: int = 2
    status: str = "planned"
    created_at: float = Field(default_factory=time.time)


class RiskRecord(BaseModel):
    id: str
    project_id: str
    risk: str
    severity: str = "high"
    mitigation: str
    created_at: float = Field(default_factory=time.time)


class APIDefinitionRecord(BaseModel):
    id: str
    project_id: str
    endpoint: str
    method: str = "GET"
    request_schema: Dict[str, Any] = Field(default_factory=dict)
    response_schema: Dict[str, Any] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)


class ArchitectureRecord(BaseModel):
    id: str
    project_id: str
    type: str = "microservices"
    description: str
    created_at: float = Field(default_factory=time.time)


class DeploymentV2Record(BaseModel):
    id: str
    project_id: str
    provider: str = "Docker Compose"
    status: str = "ready"
    created_at: float = Field(default_factory=time.time)


class FrontendComponentRecord(BaseModel):
    id: str
    project_id: str
    component_name: str
    path: str
    status: str = "generated"
    created_at: float = Field(default_factory=time.time)


class FrontendPageRecord(BaseModel):
    id: str
    project_id: str
    page_name: str
    route: str
    status: str = "generated"
    created_at: float = Field(default_factory=time.time)


class FrontendRouteRecord(BaseModel):
    id: str
    project_id: str
    path: str
    layout: str = "DashboardLayout"
    protected: bool = True
    created_at: float = Field(default_factory=time.time)


class BackendServiceRecord(BaseModel):
    id: str
    project_id: str
    service_name: str
    status: str = "generated"
    created_at: float = Field(default_factory=time.time)


class APIRouteRecord(BaseModel):
    id: str
    project_id: str
    method: str = "POST"
    path: str
    protected: bool = True
    created_at: float = Field(default_factory=time.time)


class AuthRoleRecord(BaseModel):
    id: str
    role: str
    permissions: List[str] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)


class DatabaseModelRecord(BaseModel):
    id: str
    project_id: str
    model_name: str
    status: str = "generated"
    created_at: float = Field(default_factory=time.time)


class MigrationRecord(BaseModel):
    id: str
    project_id: str
    version: str
    status: str = "applied"
    created_at: float = Field(default_factory=time.time)


class IndexRecord(BaseModel):
    id: str
    project_id: str
    index_name: str
    table_name: str
    created_at: float = Field(default_factory=time.time)


class BackupRecord(BaseModel):
    id: str
    project_id: str
    backup_type: str = "daily"
    status: str = "success"
    created_at: float = Field(default_factory=time.time)


class ReviewReportRecord(BaseModel):
    id: str
    project_id: str
    overall_score: float = 95.5
    created_at: float = Field(default_factory=time.time)


class ReviewIssueRecord(BaseModel):
    id: str
    project_id: str
    category: str
    severity: str = "Medium"
    description: str
    resolved: bool = False
    created_at: float = Field(default_factory=time.time)


class RefactorSuggestionRecord(BaseModel):
    id: str
    project_id: str
    file: str
    description: str
    priority: str = "Low"
    created_at: float = Field(default_factory=time.time)


class TestSuiteRecord(BaseModel):
    id: str
    project_id: str
    suite_name: str
    status: str = "PASSED"
    coverage: float = 94.5
    created_at: float = Field(default_factory=time.time)


class TestResultRecord(BaseModel):
    id: str
    project_id: str
    test_name: str
    status: str = "passed"
    duration: float = 15.0
    error_message: Optional[str] = None
    created_at: float = Field(default_factory=time.time)


class CoverageReportRecord(BaseModel):
    id: str
    project_id: str
    line_coverage: float = 95.0
    branch_coverage: float = 92.0
    function_coverage: float = 96.0
    overall_coverage: float = 94.5
    created_at: float = Field(default_factory=time.time)







