"""
AIForge Day 32 — Infrastructure Data Models
===========================================
Pydantic models for Infrastructure Requirements, Resource Plans, Cost Estimates,
Security Audits, Infrastructure Drift, and Provider Configurations.
"""

from enum import Enum
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class PlanActionEnum(str, Enum):
    CREATE = "CREATE"
    MODIFY = "MODIFY"
    DESTROY = "DESTROY"


class InfraRequirement(BaseModel):
    project_id: str = "aiforge-demo"
    environment: str = "production"  # development, staging, production
    provider: str = "AWS"  # AWS, Azure, GCP, Local
    frontend_hosting: bool = True
    backend_compute: bool = True
    database_required: bool = True
    redis_required: bool = True
    ingress_required: bool = True


class ResourcePlanItem(BaseModel):
    resource_type: str
    resource_name: str
    action: PlanActionEnum = PlanActionEnum.CREATE
    is_destructive: bool = False
    reason: str = "Provisioning required architecture component"
    dependencies: List[str] = Field(default_factory=list)


class TerraformPlan(BaseModel):
    project_id: str = "aiforge-demo"
    environment: str = "production"
    provider: str = "AWS"
    to_create_count: int = 8
    to_modify_count: int = 2
    to_destroy_count: int = 0
    is_destructive: bool = False
    destructive_resources: List[str] = Field(default_factory=list)
    items: List[ResourcePlanItem] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class CostEstimate(BaseModel):
    monthly_compute_usd: float = 48.0
    monthly_database_usd: float = 35.0
    monthly_redis_usd: float = 15.0
    monthly_total_usd: float = 98.0
    is_estimate: bool = True
    label: str = "ESTIMATE AVAILABLE"


class SecurityAuditResult(BaseModel):
    passed: bool = True
    violations: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class DriftResult(BaseModel):
    has_drift: bool = False
    resource_name: str = "aws_ecs_task_definition.backend"
    expected: str = "3 replicas"
    actual: str = "5 replicas"
    potential_cause: str = "Manual scaling action applied directly on cloud console."


class CloudProviderConfig(BaseModel):
    provider_name: str = "AWS"
    is_configured: bool = True
    region: str = "us-east-1"
    account_id: str = "123456789012"
    status_message: str = "Provider credentials active and verified."
