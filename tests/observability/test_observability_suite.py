import os
import sys
import pytest
import asyncio
from pathlib import Path

# Ensure PYTHONPATH
sys.path.insert(0, os.path.abspath("."))

from backend.observability.log_manager import global_log_manager
from backend.observability.metrics_collector import global_metrics_collector
from backend.observability.error_analyzer import global_error_analyzer
from backend.incidents.incident_detector import global_incident_detector
from backend.incidents.incident_diagnostic_agent import global_incident_diagnostic_agent
from backend.incidents.observability_engine import global_observability_engine


class TestObservabilityIncidentEngine:

    def test_log_manager_secret_redaction(self):
        raw_msg = "Failed login for admin with password='secret_admin_pass_123' and Authorization: Bearer eyJhbGciOiJIUzI1Ni..."
        entry = global_log_manager.log("backend", "ERROR", raw_msg)

        assert "secret_admin_pass_123" not in entry.message
        assert "eyJhbGci" not in entry.message
        assert "********" in entry.message

    def test_metrics_collector_p95_calculation(self):
        for i in range(100):
            global_metrics_collector.record_request(latency_ms=float(i * 10), is_error=(i >= 95))

        metrics = global_metrics_collector.get_metrics("backend")
        assert metrics.request_count == 100
        assert metrics.error_count == 5
        assert metrics.error_rate_percent == 5.0
        assert metrics.p95_latency_ms >= 900.0

    def test_error_analyzer_clustering(self):
        global_error_analyzer.record_error("psycopg2.OperationalError: could not connect to server", "/api/db")
        global_error_analyzer.record_error("Database connection refused", "/api/todos")

        clusters = global_error_analyzer.get_clusters()
        assert len(clusters) > 0
        db_cluster = next((c for c in clusters if c.category == "DatabaseConnectionError"), None)
        assert db_cluster is not None
        assert db_cluster.occurrences >= 2

    def test_incident_detector_and_diagnostic(self, tmp_path):
        inc = global_incident_detector.raise_incident(
            project_id="ObsApp",
            service="backend",
            symptom="HTTP 500 Internal Server Error",
            error_msg="JWT Token validation failed in auth.py"
        )
        assert inc.incident_id.startswith("inc_")
        assert inc.status == "DETECTED"

        diag_inc = global_incident_diagnostic_agent.diagnose_incident(inc, tmp_path)
        assert diag_inc.status == "DIAGNOSED"
        assert diag_inc.requirement_id == "FR-002"
        assert diag_inc.root_cause is not None

    def test_observability_engine_remediation(self, tmp_path):
        async def _run():
            proj_dir = tmp_path / "ObsEngineTestApp"
            proj_dir.mkdir(parents=True, exist_ok=True)

            inc = global_incident_detector.raise_incident("ObsEngineTestApp", "backend", "Container Stopped", "Process exited with code 1")
            diag = global_incident_diagnostic_agent.diagnose_incident(inc, proj_dir)

            res_inc = await global_observability_engine.trigger_autonomous_remediation(diag.incident_id, proj_dir)
            assert res_inc.status in ["RESOLVED", "ROLLED_BACK"]
            assert (proj_dir / "INCIDENT_REPORT.md").exists()

        asyncio.run(_run())
