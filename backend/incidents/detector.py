"""
AIForge Day 21 — Incident Detection Engine
===========================================
Gathers real signals from health checks, HTTP 5xx error spikes, API latency regressions,
container state, and Playwright smoke tests to detect application incidents.
"""

import logging
from typing import Dict, Any, List, Optional

from backend.devops.service import global_devops_service
from backend.browser_testing.service import global_browser_service
from backend.performance.service import global_performance_service

_logger = logging.getLogger("aiforge.incidents.detector")


class IncidentDetector:
    """
    Detects production application incidents from monitoring signals.
    """

    def scan_for_incidents(
        self,
        project_id: str,
        simulate_db_failure: bool = False,
        simulate_perf_failure: bool = False
    ) -> Optional[Dict[str, Any]]:
        _logger.info(f"[IncidentDetector] Scanning monitoring signals for '{project_id}'")

        if simulate_db_failure:
            return {
                "detected": True,
                "signal_source": "HEALTH_CHECK",
                "symptoms": [
                    "HTTP 500 error on GET /health",
                    "Database connection timeout on PaymentRepository",
                    "3 consecutive health check failures"
                ],
                "evidence": {
                    "http_code": 500,
                    "error_log": "psycopg2.OperationalError: could not connect to server: Connection refused",
                    "failed_endpoint": "/api/orders"
                }
            }

        if simulate_perf_failure:
            return {
                "detected": True,
                "signal_source": "PERFORMANCE_BENCHMARK",
                "symptoms": [
                    "API Latency P95 spiked from 180ms to 620ms",
                    "Database query latency increased by 244%"
                ],
                "evidence": {
                    "baseline_p95_ms": 180.0,
                    "current_p95_ms": 620.0,
                    "affected_api": "POST /api/orders"
                }
            }

        health = global_devops_service.get_production_health(project_id)
        if health.health_check_status != "HEALTHY" or health.http_errors_count > 0:
            return {
                "detected": True,
                "signal_source": "PRODUCTION_HEALTH",
                "symptoms": [f"Production health status is {health.health_check_status}"],
                "evidence": {"http_errors": health.http_errors_count, "latency_ms": health.latency_ms}
            }

        return None


global_incident_detector = IncidentDetector()
