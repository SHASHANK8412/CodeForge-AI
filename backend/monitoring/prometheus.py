"""
AIForge Day 29 — Prometheus Metrics Registry
=============================================
Manages Prometheus counters, gauges, and histograms with strict low-cardinality label enforcement.
Integration layer for OpenTelemetry metrics export.
"""

import time
import logging
from typing import Dict, Any, Optional
from prometheus_client import (
    CollectorRegistry, Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST, REGISTRY
)

_logger = logging.getLogger("aiforge.monitoring.prometheus")

# High-cardinality label scrubbers
FORBIDDEN_LABEL_KEYS = {"user_id", "session_id", "prompt", "query_string", "auth_token"}


def sanitize_labels(labels: Dict[str, str]) -> Dict[str, str]:
    """Sanitizes labels to prevent high-cardinality or sensitive data leaks."""
    safe = {}
    for k, v in labels.items():
        if k.lower() in FORBIDDEN_LABEL_KEYS:
            continue
        safe_val = str(v)
        if len(safe_val) > 64:
            safe_val = safe_val[:64] + "..."
        safe[k] = safe_val
    return safe


class PrometheusMetricsRegistry:
    """
    Centralized Prometheus Metrics Registry.
    """

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or REGISTRY

        # HTTP Metrics
        self.http_requests_total = Counter(
            "http_requests_total",
            "Total HTTP requests handled by AIForge API",
            ["method", "endpoint", "status_code"],
            registry=self.registry
        )
        self.http_request_duration_seconds = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "endpoint"],
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
            registry=self.registry
        )
        self.http_errors_total = Counter(
            "http_errors_total",
            "Total HTTP error responses (4xx and 5xx)",
            ["method", "endpoint", "error_type"],
            registry=self.registry
        )
        self.http_active_requests = Gauge(
            "http_active_requests",
            "Number of active HTTP requests currently in-flight",
            ["endpoint"],
            registry=self.registry
        )

        # AI Agent Metrics
        self.agent_execution_duration_seconds = Histogram(
            "agent_execution_duration_seconds",
            "Execution duration for AI Agents (Planner, Architect, Frontend, Backend, Testing)",
            ["agent_type"],
            buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
            registry=self.registry
        )
        self.llm_calls_total = Counter(
            "llm_calls_total",
            "Total LLM calls executed",
            ["model", "status"],
            registry=self.registry
        )
        self.llm_execution_duration_seconds = Histogram(
            "llm_execution_duration_seconds",
            "LLM generation duration in seconds",
            ["model"],
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
            registry=self.registry
        )

        # Redis & Cache Metrics
        self.cache_hits_total = Counter(
            "cache_hits_total",
            "Total cache hits",
            ["cache_type"],
            registry=self.registry
        )
        self.cache_misses_total = Counter(
            "cache_misses_total",
            "Total cache misses",
            ["cache_type"],
            registry=self.registry
        )
        self.queue_depth = Gauge(
            "queue_depth",
            "Current depth of background job queue",
            ["queue_type"],
            registry=self.registry
        )
        self.job_duration_seconds = Histogram(
            "job_duration_seconds",
            "Background job completion duration in seconds",
            ["job_type"],
            buckets=(0.5, 2.0, 5.0, 15.0, 30.0, 60.0, 180.0),
            registry=self.registry
        )

        # System Infrastructure Metrics
        self.app_health_status = Gauge(
            "app_health_status",
            "System health status (1 = healthy, 0 = degraded/down)",
            ["component"],
            registry=self.registry
        )
        self.process_cpu_usage_ratio = Gauge(
            "process_cpu_usage_ratio",
            "Process CPU usage ratio",
            registry=self.registry
        )
        self.process_memory_bytes = Gauge(
            "process_memory_bytes",
            "Process memory footprint in bytes",
            registry=self.registry
        )

        # Initialize health gauges
        self.app_health_status.labels(component="fastapi_backend").set(1.0)
        self.app_health_status.labels(component="postgresql_database").set(1.0)
        self.app_health_status.labels(component="redis_cache").set(1.0)

    def record_http_request(self, method: str, endpoint: str, status_code: int, duration_s: float):
        method_str = method.upper()
        ep_str = endpoint.split("?")[0]  # Strip query string for low cardinality
        sc_str = str(status_code)

        self.http_requests_total.labels(method=method_str, endpoint=ep_str, status_code=sc_str).inc()
        self.http_request_duration_seconds.labels(method=method_str, endpoint=ep_str).observe(duration_s)

        if status_code >= 400:
            err_type = "CLIENT_ERROR" if status_code < 500 else "SERVER_ERROR"
            self.http_errors_total.labels(method=method_str, endpoint=ep_str, error_type=err_type).inc()

    def record_agent_execution(self, agent_type: str, duration_s: float):
        self.agent_execution_duration_seconds.labels(agent_type=agent_type).observe(duration_s)

    def record_llm_call(self, model: str, duration_s: float, success: bool = True):
        status = "SUCCESS" if success else "FAILURE"
        self.llm_calls_total.labels(model=model, status=status).inc()
        self.llm_execution_duration_seconds.labels(model=model).observe(duration_s)

    def record_cache_event(self, hit: bool, cache_type: str = "llm_cache"):
        if hit:
            self.cache_hits_total.labels(cache_type=cache_type).inc()
        else:
            self.cache_misses_total.labels(cache_type=cache_type).inc()

    def generate_metrics_payload(self) -> bytes:
        return generate_latest(self.registry)


global_prometheus_registry = PrometheusMetricsRegistry()
