"""
AIForge Day 26 — OpenTelemetry Observability Pydantic Data Models
===================================================================
Models for Trace Spans, Distributed Traces, Observability Metrics,
Performance Regression Alerts, and Observability Readiness Statuses.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class SpanKind(str, Enum):
    SERVER = "SERVER"
    CLIENT = "CLIENT"
    INTERNAL = "INTERNAL"
    DATABASE = "DATABASE"


class TraceSpan(BaseModel):
    span_id: str
    trace_id: str
    name: str
    kind: SpanKind = SpanKind.SERVER
    duration_ms: float
    status_code: int = 200
    attributes: Dict[str, Any] = Field(default_factory=dict)
    dna_file_path: Optional[str] = None
    start_time: str = ""
    end_time: str = ""


class DistributedTrace(BaseModel):
    trace_id: str
    project_id: str
    root_http_method: str = "POST"
    root_route: str = "/api/orders"
    total_duration_ms: float = 342.0
    status_code: int = 200
    spans: List[TraceSpan] = Field(default_factory=list)
    flight_recorder_events: List[str] = Field(default_factory=list)
    created_at: str = ""


class ObservabilityMetrics(BaseModel):
    project_id: str
    total_requests: int = 12842
    error_rate_pct: float = 0.14
    p95_duration_ms: float = 182.0
    active_incidents_count: int = 0
    observability_status: str = "PASS"  # PASS, WARN, NOT_AVAILABLE


class PerformanceRegressionAlert(BaseModel):
    project_id: str
    endpoint: str = "POST /api/orders"
    previous_v13_p95_ms: float = 180.0
    current_v14_p95_ms: float = 420.0
    regression_ratio: float = 2.33
    slowest_span_name: str = "PostgreSQL"
    slowest_span_duration_ms: float = 350.0
    trace_id: str = "trace_reg_99"
    detected_at: str = ""


class ObservabilityReadinessStatus(BaseModel):
    project_id: str
    status: str = "PASS"  # PASS, WARN, NOT_AVAILABLE
    tracing_enabled: bool = True
    fastapi_instrumented: bool = True
    db_instrumented: bool = True
    redaction_active: bool = True
    details: str = "OpenTelemetry tracing active with complete span coverage and security redaction."
