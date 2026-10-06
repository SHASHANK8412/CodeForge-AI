"""
AIForge Day 26 — Centralized OpenTelemetryService
=================================================
Manages OpenTelemetry trace collection, metrics calculation, performance regression detection,
Flight Recorder correlation, and REST API data querying.
"""

import time
import secrets
from collections import deque
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from backend.observability.models import (
    DistributedTrace, TraceSpan, SpanKind, ObservabilityMetrics,
    PerformanceRegressionAlert, ObservabilityReadinessStatus
)
from backend.observability.tracer import global_opentelemetry_tracer
from backend.observability.database_telemetry import global_database_telemetry_instrumentor
from backend.observability.dna_mapper import global_dna_trace_mapper
from backend.observability.integration import global_telemetry_multi_system_bridge

_logger = logging.getLogger("aiforge.observability.service")


def _sanitize_headers(headers: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not headers:
        return {}
    sensitive_keys = {"authorization", "cookie", "x-api-key", "secret", "password", "token"}
    sanitized = {}
    for k, v in headers.items():
        if k.lower() in sensitive_keys or any(s in k.lower() for s in sensitive_keys):
            sanitized[k] = "[REDACTED]"
        else:
            sanitized[k] = str(v)
    return sanitized


PLATFORM_PROJECT = "platform"
_MAX_TRACES = 1000


def _percentile(values: List[float], pct: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(pct / 100 * (len(ordered) - 1))))
    return round(ordered[index], 2)


class OpenTelemetryService:
    """
    Request traces as they actually happened: method, route, status and measured duration, one
    server span each, kept in a bounded in-memory buffer per project. AIForge's own API requests
    are recorded under the "platform" id; generated projects are not instrumented, so they have
    no traces rather than invented ones.
    """

    def __init__(self):
        self._traces: Dict[str, deque] = {}
        self._totals: Dict[str, Dict[str, int]] = {}
        self._regressions: Dict[str, List[PerformanceRegressionAlert]] = {}

    def record_trace(
        self,
        project_id: str = PLATFORM_PROJECT,
        http_method: str = "GET",
        route: str = "/",
        status_code: int = 200,
        headers: Dict[str, Any] = None,
        duration_ms: Optional[float] = None,
    ) -> DistributedTrace:
        trace_id = f"trace_{secrets.token_urlsafe(6)}"
        duration = round(float(duration_ms or 0.0), 2)
        span = global_opentelemetry_tracer.create_span(
            trace_id=trace_id,
            name=f"{http_method} {route}",
            kind=SpanKind.SERVER,
            duration_ms=duration,
            status_code=status_code,
            attributes={"http.method": http_method, "http.route": route, "headers": _sanitize_headers(headers)},
        )
        trace = DistributedTrace(
            trace_id=trace_id,
            project_id=project_id,
            root_http_method=http_method,
            root_route=route,
            total_duration_ms=duration,
            status_code=status_code,
            spans=[span],
            created_at=datetime.now().isoformat(),
        )
        self._traces.setdefault(project_id, deque(maxlen=_MAX_TRACES)).append(trace)
        totals = self._totals.setdefault(project_id, {"requests": 0, "errors": 0})
        totals["requests"] += 1
        totals["errors"] += 1 if status_code >= 500 else 0
        return trace

    def get_metrics(self, project_id: str) -> ObservabilityMetrics:
        traces = list(self._traces.get(project_id, ()))
        totals = self._totals.get(project_id, {"requests": 0, "errors": 0})
        if not traces:
            return ObservabilityMetrics(project_id=project_id, total_requests=0, error_rate_pct=0.0,
                                        p95_duration_ms=0.0, active_incidents_count=0,
                                        observability_status="NOT_AVAILABLE")
        return ObservabilityMetrics(
            project_id=project_id,
            total_requests=totals["requests"],
            error_rate_pct=round(totals["errors"] / totals["requests"] * 100, 2),
            p95_duration_ms=_percentile([t.total_duration_ms for t in traces], 95),
            active_incidents_count=0,
            observability_status="PASS",
        )

    def get_traces(self, project_id: str) -> List[DistributedTrace]:
        return list(reversed(self._traces.get(project_id, ())))

    def get_trace_details(self, project_id: str, trace_id: str) -> Optional[DistributedTrace]:
        return next((t for t in self._traces.get(project_id, ()) if t.trace_id == trace_id), None)

    def detect_performance_regression(self, project_id: str) -> Optional[PerformanceRegressionAlert]:
        """
        Compare each route's p95 between the older and newer half of its recorded requests; report
        the worst slowdown of at least 1.5x (needs 20+ requests on that route), otherwise None.
        """
        by_route: Dict[str, List[DistributedTrace]] = {}
        for t in self._traces.get(project_id, ()):
            by_route.setdefault(f"{t.root_http_method} {t.root_route}", []).append(t)
        worst = None
        for endpoint, traces in by_route.items():
            if len(traces) < 20:
                continue
            half = len(traces) // 2
            before = _percentile([t.total_duration_ms for t in traces[:half]], 95)
            after_traces = traces[half:]
            after = _percentile([t.total_duration_ms for t in after_traces], 95)
            ratio = after / before if before else 0
            if ratio >= 1.5 and (worst is None or ratio > worst.regression_ratio):
                slowest = max(after_traces, key=lambda t: t.total_duration_ms)
                worst = PerformanceRegressionAlert(
                    project_id=project_id, endpoint=endpoint,
                    previous_v13_p95_ms=before, current_v14_p95_ms=after, regression_ratio=round(ratio, 2),
                    slowest_span_name=slowest.spans[0].name if slowest.spans else endpoint,
                    slowest_span_duration_ms=slowest.total_duration_ms, trace_id=slowest.trace_id,
                    detected_at=datetime.now().isoformat(),
                )
        if worst:
            self._regressions.setdefault(project_id, []).append(worst)
        return worst


global_opentelemetry_service = OpenTelemetryService()
