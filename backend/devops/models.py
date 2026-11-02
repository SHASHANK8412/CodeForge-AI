"""
AIForge Day 20 — Autonomous DevOps Pydantic Data Models
========================================================
Models for Deployment Statuses, Deployment Plans, Resource Limits,
Environment Configurations, Health Checks, Smoke Tests, History, and Diffs.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class DeploymentState(str, Enum):
    QUEUED = "QUEUED"
    VALIDATING = "VALIDATING"
    BUILDING = "BUILDING"
    DEPLOYING = "DEPLOYING"
    HEALTH_CHECK = "HEALTH_CHECK"
    SMOKE_TEST = "SMOKE_TEST"
    LIVE = "LIVE"
    FAILED = "FAILED"
    ROLLING_BACK = "ROLLING_BACK"
    ROLLED_BACK = "ROLLED_BACK"


class ResourceLimits(BaseModel):
    max_memory_mb: int = 512
    max_cpu: float = 1.0
    storage_mb: int = 2048
    execution_timeout_seconds: int = 300


class DeploymentPlan(BaseModel):
    plan_id: str
    project_id: str
    version: int = 1
    application_type: str = "react_fastapi"
    frontend_type: str = "static_nginx"
    backend_type: str = "fastapi"
    containerization: bool = True
    provider: str = "Docker"
    environment: str = "production"
    health_endpoint: str = "/health"
    required_environment_vars: List[str] = Field(default_factory=list)
    resource_limits: ResourceLimits = Field(default_factory=ResourceLimits)
    port: int = 8080
    dockerfile_content: str = ""


class HealthCheckResult(BaseModel):
    status: str = "HEALTHY"  # HEALTHY, DEGRADED, UNHEALTHY
    http_code: int = 200
    latency_ms: float = 45.0
    details: Dict[str, Any] = Field(default_factory=dict)
    checked_at: str = ""


class SmokeTestResult(BaseModel):
    status: str = "PASS"  # PASS, FAIL
    total_scenarios: int = 4
    passed_scenarios: int = 4
    failed_scenarios: int = 0
    scenarios_summary: List[Dict[str, Any]] = Field(default_factory=list)
    executed_at: str = ""


class DeploymentStatus(BaseModel):
    id: str
    project_id: str
    version: int = 1
    environment: str = "production"
    provider: str = "Docker"
    status: DeploymentState = DeploymentState.QUEUED
    image: str = ""
    url: str = "http://localhost:8080"
    started_at: str = ""
    completed_at: Optional[str] = None
    health_status: HealthCheckResult = Field(default_factory=HealthCheckResult)
    smoke_test_status: SmokeTestResult = Field(default_factory=SmokeTestResult)
    error: Optional[str] = None
    rollback_status: Optional[str] = None
    sanitized_logs: List[str] = Field(default_factory=list)


class DeploymentHistory(BaseModel):
    project_id: str
    deployments: List[DeploymentStatus] = Field(default_factory=list)


class DeploymentComparison(BaseModel):
    old_version: int
    new_version: int
    readiness_change: float = 0.0
    latency_change_ms: float = 0.0
    status_change: str = "Failed -> Live"


class ProductionHealth(BaseModel):
    project_id: str
    status: str = "LIVE"
    uptime_percent: float = 99.9
    health_check_status: str = "HEALTHY"
    http_errors_count: int = 0
    latency_ms: float = 42.0
    active_version: int = 1
    container_status: str = "Running"
    last_deployment_time: str = ""
