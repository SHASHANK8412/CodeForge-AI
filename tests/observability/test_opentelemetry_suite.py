"""
AIForge Day 26 — OpenTelemetry Observability Test Suite
=========================================================
Comprehensive unit and integration tests covering:
- FastAPI Request Instrumentation & Trace ID Generation
- Distributed Trace Span Breakdown (FastAPI -> Service -> Database -> Response)
- Database Telemetry Instrumentation without Secret Leakage
- Automatic Security Redaction of Passwords, JWTs, and API Keys
- Performance Engineer Telemetry Feeding
- Incident Response Trace Evidence Integration
- Engineering DNA Source File Mapping
- Flight Recorder Trace ID Correlation
- Performance Regression Detection
- Production Readiness Observability Gate
- FastAPI REST API Endpoints
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.observability.tracer import OpenTelemetryTracer
from backend.observability.database_telemetry import DatabaseTelemetryInstrumentor
from backend.observability.dna_mapper import EngineeringDNATraceMapper
from backend.observability.integration import TelemetryMultiSystemBridge
from backend.observability.service import OpenTelemetryService
from backend.observability.models import SpanKind


@pytest.fixture
def client():
    return TestClient(app)


class TestOpenTelemetryObservability:

    def test_security_redaction_engine(self):
        tracer = OpenTelemetryTracer()

        raw_attrs = {
            "Authorization": "Bearer secret_jwt_token_12345",
            "db.connection": "postgres://admin:super_secret_pass@localhost:5432/db",
            "http.route": "/api/orders",
            "api_key": "sk-test-12345"
        }

        redacted = tracer.redact_attributes(raw_attrs)
        assert redacted["Authorization"] == "[REDACTED_HEADER]"
        assert "super_secret_pass" not in redacted["db.connection"]
        assert redacted["http.route"] == "/api/orders"
        assert redacted["api_key"] == "[REDACTED_HEADER]"

    def test_database_telemetry_span_creation(self):
        inst = DatabaseTelemetryInstrumentor()
        span = inst.record_db_span(
            trace_id="trace_db_test",
            operation_type="SELECT",
            table_name="orders",
            duration_ms=287.0,
            statement="SELECT * FROM orders WHERE password='secret_password_123'"
        )

        assert span.kind == SpanKind.DATABASE
        assert span.duration_ms == 287.0
        assert span.attributes["db.operation"] == "SELECT"
        assert "secret_password_123" not in span.attributes["db.statement"]

    def test_distributed_trace_and_dna_mapping(self):
        service = OpenTelemetryService()
        trace = service.record_trace("proj_test")

        assert len(trace.spans) == 5
        assert trace.spans[0].kind == SpanKind.SERVER
        assert trace.spans[3].kind == SpanKind.CLIENT  # External API

        dna_mapper = EngineeringDNATraceMapper()
        mapped = dna_mapper.map_trace_to_dna(trace)

        assert mapped["trace_id"] == trace.trace_id
        assert len(mapped["mapped_spans"]) == 5
        assert mapped["mapped_spans"][1]["dna_file_path"] == "backend/services/orders.py"

    def test_multi_system_telemetry_integration(self):
        bridge = TelemetryMultiSystemBridge()
        service = OpenTelemetryService()
        trace = service.record_trace("proj_test")

        perf_feed = bridge.feed_performance_engineer(trace)
        assert perf_feed["trace_id"] == trace.trace_id
        assert "duration:" in perf_feed["evidence"]

        inc_feed = bridge.feed_incident_response("proj_test", trace)
        assert inc_feed["incident_trigger"] == "LATENCY_SPIKE"
        assert "largest measured contributor" in inc_feed["analysis"]
        assert "Do not claim root cause solely from latency correlation" in inc_feed["analysis"]

        readiness = bridge.evaluate_observability_readiness("proj_test")
        assert readiness.status == "PASS"

    def test_performance_regression_alert(self):
        service = OpenTelemetryService()
        alert = service.detect_performance_regression("proj_test")

        assert alert.regression_ratio > 2.0
        assert alert.slowest_span_duration_ms == 350.0

    def test_readiness_gate_collector_integration(self):
        from backend.readiness.checks import global_readiness_check_collector
        checks = global_readiness_check_collector.collect_all_checks("proj_test")
        otel_chk = next((c for c in checks if c.category == "Observability"), None)
        assert otel_chk is not None
        assert otel_chk.status.value == "PASS"
        assert not otel_chk.blocking

    def test_fastapi_middleware_trace_header(self, client):
        res = client.get("/health")
        assert res.status_code == 200
        assert "X-Trace-ID" in res.headers

    def test_observability_rest_api_endpoints(self, client):
        met_res = client.get("/api/projects/aiforge-demo/observability/metrics")
        assert met_res.status_code == 200
        assert met_res.json()["status"] == "success"

        tra_res = client.get("/api/projects/aiforge-demo/observability/traces")
        assert tra_res.status_code == 200

        trace_id = tra_res.json()["traces"][0]["trace_id"]
        det_res = client.get(f"/api/projects/aiforge-demo/observability/traces/{trace_id}")
        assert det_res.status_code == 200
        assert det_res.json()["trace"]["trace_id"] == trace_id

        reg_res = client.get("/api/projects/aiforge-demo/observability/regression")
        assert reg_res.status_code == 200

        red_res = client.get("/api/projects/aiforge-demo/observability/readiness")
        assert red_res.status_code == 200

