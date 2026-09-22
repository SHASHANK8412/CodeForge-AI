"""
AIForge Metrics Collector Module
================================
Tracks HTTP request counts, error rates %, average latency, P95/P99 latency calculations,
and container/process utilization metrics.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

_logger = logging.getLogger("aiforge.observability.metrics")


class ServiceMetrics(BaseModel):
    service_name: str
    request_count: int = 0
    error_count: int = 0
    error_rate_percent: float = 0.0
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    status: str = "HEALTHY"  # HEALTHY, DEGRADED, UNHEALTHY


class MetricsCollector:
    """
    Collects real-time API performance & latency metrics.
    """

    def __init__(self):
        self._latencies: List[float] = []
        self._requests: int = 0
        self._errors: int = 0

    def record_request(self, latency_ms: float, is_error: bool = False):
        self._requests += 1
        if is_error:
            self._errors += 1
        self._latencies.append(latency_ms)
        if len(self._latencies) > 1000:
            self._latencies.pop(0)

    def get_metrics(self, service_name: str = "backend") -> ServiceMetrics:
        if self._requests == 0:
            return ServiceMetrics(service_name=service_name, status="HEALTHY")

        err_rate = round((self._errors / max(1, self._requests)) * 100.0, 2)
        sorted_lats = sorted(self._latencies) if self._latencies else [0.0]

        avg_lat = round(sum(sorted_lats) / max(1, len(sorted_lats)), 2)
        p95_idx = int(len(sorted_lats) * 0.95)
        p99_idx = int(len(sorted_lats) * 0.99)

        p95_lat = sorted_lats[min(p95_idx, len(sorted_lats) - 1)]
        p99_lat = sorted_lats[min(p99_idx, len(sorted_lats) - 1)]

        status = "UNHEALTHY" if err_rate > 10.0 else ("DEGRADED" if err_rate > 2.0 or p95_lat > 500 else "HEALTHY")

        return ServiceMetrics(
            service_name=service_name,
            request_count=self._requests,
            error_count=self._errors,
            error_rate_percent=err_rate,
            avg_latency_ms=avg_lat,
            p95_latency_ms=p95_lat,
            p99_latency_ms=p99_lat,
            status=status
        )


global_metrics_collector = MetricsCollector()
