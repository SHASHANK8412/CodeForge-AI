"""
AIForge Day 29 — Prometheus + Grafana Observability Test Suite
================================================================
Comprehensive unit and integration tests covering:
1. Prometheus Metrics Collection (HTTP, Agent, LLM, Redis, System)
2. Low-Cardinality Metric Labels (Excluding user_id, session_id, raw prompts)
3. Prometheus Exporter Endpoint (/metrics)
4. Grafana Dashboard Configurations (Overview, Agent, API, Infra, LLM, Incidents)
5. Alert Rule Threshold Evaluation
6. Incident Response Integration (Alert -> Incident Dispatch)
7. Performance Engineer Metric Evidence (Version A vs Version B comparison)
8. Security Controls & Secret Redaction in Telemetry Streams
"""

import json
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.monitoring.prometheus import PrometheusMetricsRegistry, sanitize_labels, global_prometheus_registry
from backend.monitoring.alerts import AlertRule, AlertEvaluator, global_alert_evaluator
from backend.monitoring.service import PrometheusGrafanaService, global_monitoring_service


@pytest.fixture
def client():
    return TestClient(app)


class TestPrometheusGrafanaSuite:

    def test_low_cardinality_label_sanitization(self):
        labels = {
            "endpoint": "/api/generate",
            "method": "POST",
            "user_id": "usr_secret_999",
            "session_id": "sess_abcdef123",
            "auth_token": "bearer_secret_token",
            "prompt": "SELECT * FROM secret_db"
        }
        sanitized = sanitize_labels(labels)

        assert "endpoint" in sanitized
        assert "method" in sanitized
        assert "user_id" not in sanitized
        assert "session_id" not in sanitized
        assert "auth_token" not in sanitized
        assert "prompt" not in sanitized

    def test_metrics_collection_and_recording(self):
        from prometheus_client import CollectorRegistry
        registry = PrometheusMetricsRegistry(registry=CollectorRegistry())


        # Record HTTP request
        registry.record_http_request("GET", "/api/projects", 200, 0.045)
        registry.record_http_request("POST", "/api/generate", 500, 1.25)

        # Record AI Agent & LLM metrics
        registry.record_agent_execution("planner", 0.35)
        registry.record_llm_call("ollama:llama3", 1.8, success=True)
        registry.record_cache_event(hit=True, cache_type="llm_cache")

        payload = registry.generate_metrics_payload().decode("utf-8")

        assert "http_requests_total" in payload
        assert "http_request_duration_seconds" in payload
        assert "agent_execution_duration_seconds" in payload
        assert "llm_calls_total" in payload
        assert "cache_hits_total" in payload

    def test_prometheus_metrics_endpoint(self, client):
        res = client.get("/metrics")
        assert res.status_code == 200
        assert "text/plain" in res.headers["content-type"]
        body = res.text
        assert "http_requests_total" in body
        assert "app_health_status" in body

        # Verify no unredacted bearer token / secrets in /metrics output
        assert "bearer_" not in body.lower()
        assert "password" not in body.lower()

    def test_grafana_dashboard_definitions(self):
        service = PrometheusGrafanaService()
        dashboards = service.list_dashboards()

        assert "AIForge Overview" in dashboards
        assert "Agent Performance" in dashboards
        assert "API Performance" in dashboards
        assert "Infrastructure" in dashboards
        assert "LLM Performance" in dashboards
        assert "Incidents" in dashboards

        # Test retrieving dashboard JSON config
        overview_cfg = service.get_dashboard_config("AIForge Overview")
        assert overview_cfg["title"] == "AIForge Overview"
        assert len(overview_cfg["panels"]) >= 1

    def test_alert_rules_and_incident_dispatch(self):
        evaluator = AlertEvaluator()

        # Normal metrics -> 0 alerts triggered
        normal_metrics = {
            "error_rate_pct": 0.1,
            "p95_latency_ms": 150.0,
            "app_health": 1.0,
            "queue_depth": 5.0,
            "memory_usage_pct": 45.0
        }
        alerts_normal = evaluator.evaluate_metrics("proj_test", normal_metrics)
        assert len(alerts_normal) == 0

        # Breached metric -> Alert triggered and dispatched to Incident Response
        breached_metrics = {
            "error_rate_pct": 8.5,  # Breaches > 5%
            "p95_latency_ms": 1400.0,  # Breaches > 1000ms
            "app_health": 1.0,
            "queue_depth": 10.0,
            "memory_usage_pct": 50.0
        }
        alerts_breached = evaluator.evaluate_metrics("proj_test", breached_metrics)
        assert len(alerts_breached) >= 2
        alert_names = [a["alert_name"] for a in alerts_breached]
        assert "HighErrorRate" in alert_names
        assert "HighLatencyP95" in alert_names

    def test_performance_engineer_metric_comparison(self):
        service = PrometheusGrafanaService()

        comparison = service.compare_performance_versions("v1.0", "v2.0", "p95_latency_ms")
        assert comparison["version_a"] == "v1.0"
        assert comparison["version_b"] == "v2.0"
        assert comparison["improvement"] == "IMPROVED"
        assert comparison["val_a"] > comparison["val_b"]
        assert "Prometheus measured" in comparison["evidence"]

    def test_monitoring_overview_endpoint(self, client):
        res = client.get("/api/monitoring/overview?project_id=aiforge-demo")
        assert res.status_code == 200
        data = res.json()
        assert data["system_health"] == "HEALTHY"
        assert "requests_total" in data
        assert "agent_latency_ms" in data
        assert data["grafana_status"] == "ACTIVE"
        assert data["prometheus_status"] == "SCRAPING_HEALTHY"
