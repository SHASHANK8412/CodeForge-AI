"""
AIForge Day 33 — AI FinOps & Infrastructure Cost Intelligence
=============================================================
Pydantic models for all FinOps data structures.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class CostSourceEnum(str, Enum):
    ESTIMATED = "ESTIMATED"
    ACTUAL = "ACTUAL"
    UNAVAILABLE = "COST DATA UNAVAILABLE"


class ProviderEnum(str, Enum):
    AWS = "AWS"
    AZURE = "AZURE"
    GCP = "GCP"
    LOCAL = "LOCAL"
    UNKNOWN = "UNKNOWN"


class RiskLevelEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class OptimizationPolicyEnum(str, Enum):
    CONSERVATIVE = "CONSERVATIVE"
    BALANCED = "BALANCED"
    AGGRESSIVE = "AGGRESSIVE"


class BudgetStatusEnum(str, Enum):
    OK = "OK"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AnomalySeverityEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


# ─────────────────────────────────────────────
# Core cost record
# ─────────────────────────────────────────────

class InfrastructureCost(BaseModel):
    """Represents a single infrastructure cost record.
    Always distinguishes ESTIMATED from ACTUAL cost.
    """
    id: str = ""
    project_id: str = ""
    provider: ProviderEnum = ProviderEnum.AWS
    environment: str = "production"
    resource_type: str = ""          # e.g. "EC2", "RDS", "Redis"
    resource_name: str = ""
    region: str = "us-east-1"
    quantity: float = 1.0
    unit_cost: float = 0.0           # $/unit/month
    estimated_monthly_cost: float = 0.0
    actual_cost: Optional[float] = None    # None → billing data unavailable
    currency: str = "USD"
    source: CostSourceEnum = CostSourceEnum.ESTIMATED
    assumptions: str = ""
    pricing_timestamp: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ─────────────────────────────────────────────
# Breakdown & summary
# ─────────────────────────────────────────────

class CostBreakdown(BaseModel):
    project_id: str
    provider: ProviderEnum
    environment: str
    compute: float = 0.0
    database: float = 0.0
    redis: float = 0.0
    networking: float = 0.0
    storage: float = 0.0
    monitoring: float = 0.0
    kubernetes: float = 0.0
    other: float = 0.0
    total_monthly_estimate: float = 0.0
    source: CostSourceEnum = CostSourceEnum.ESTIMATED
    line_items: list[InfrastructureCost] = Field(default_factory=list)
    currency: str = "USD"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ─────────────────────────────────────────────
# Budget
# ─────────────────────────────────────────────

class ProjectBudget(BaseModel):
    project_id: str
    environment: str = "production"
    monthly_limit: float = 250.0
    currency: str = "USD"
    alert_threshold: float = 0.80    # 80 % → WARNING
    critical_threshold: float = 1.00 # 100 % → CRITICAL
    current_estimate: float = 0.0
    status: BudgetStatusEnum = BudgetStatusEnum.OK
    percent_used: float = 0.0
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ─────────────────────────────────────────────
# Recommendation
# ─────────────────────────────────────────────

class CostRecommendation(BaseModel):
    id: str
    project_id: str
    title: str
    description: str
    resource_name: str = ""
    resource_type: str = ""
    current_config: str = ""
    suggested_config: str = ""
    potential_saving: str = "ESTIMATE"   # Never fabricate a real dollar value
    risk: RiskLevelEnum = RiskLevelEnum.LOW
    requires_performance_validation: bool = False
    requires_approval: bool = True
    security_safe: bool = True
    reliability_safe: bool = True
    terraform_plan_available: bool = True
    evolution_priority: str = "MEDIUM"
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ─────────────────────────────────────────────
# Waste detection
# ─────────────────────────────────────────────

class WasteItem(BaseModel):
    resource_name: str
    resource_type: str
    allocated: str
    observed_average: str
    waste_label: str = "Potential Waste"   # NEVER "Confirmed Waste" without actual data
    confidence: str = "LOW"
    recommendation: str


# ─────────────────────────────────────────────
# Architecture comparison
# ─────────────────────────────────────────────

class ArchitectureOption(BaseModel):
    name: str
    description: str
    cost_label: str        # LOW / MEDIUM / HIGH
    complexity_label: str
    scalability_label: str
    reliability_label: str
    security_label: str
    estimated_monthly_cost: float = 0.0
    source: CostSourceEnum = CostSourceEnum.ESTIMATED


class ArchitectureCostComparison(BaseModel):
    project_id: str
    question: str
    options: list[ArchitectureOption] = Field(default_factory=list)
    recommended: str = ""
    reasoning: str = ""
    note: str = "Recommendation based on cost, performance, reliability, security, and operational complexity. Not cost alone."
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ─────────────────────────────────────────────
# Anomaly
# ─────────────────────────────────────────────

class CostAnomaly(BaseModel):
    project_id: str
    detected_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    baseline_daily_cost: float = 0.0
    observed_daily_cost: float = 0.0
    multiplier: float = 1.0
    severity: AnomalySeverityEnum = AnomalySeverityEnum.MEDIUM
    possible_causes: list[str] = Field(default_factory=list)
    action: str = "Investigate. Do NOT automatically terminate resources."


# ─────────────────────────────────────────────
# Forecast
# ─────────────────────────────────────────────

class CostForecast(BaseModel):
    project_id: str
    forecast_available: bool = False
    label: str = "FORECAST UNAVAILABLE"
    next_7_days: Optional[float] = None
    next_30_days: Optional[float] = None
    next_90_days: Optional[float] = None
    trend_pct: Optional[float] = None   # e.g. +34 %
    source: CostSourceEnum = CostSourceEnum.ESTIMATED
    note: str = "Forecasts are estimates based on observed resource configurations. Historical billing data is not available."
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ─────────────────────────────────────────────
# K8s justification
# ─────────────────────────────────────────────

class KubernetesJustification(BaseModel):
    project_id: str
    is_justified: bool
    summary: str
    factors: list[str] = Field(default_factory=list)
    recommendation: str
    alternative: Optional[str] = None
