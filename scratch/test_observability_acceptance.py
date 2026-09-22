import os
import sys
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
from backend.deployment.rollback_manager import global_rollback_manager


async def run_observability_acceptance():
    print("=" * 75)
    print("AIForge Observability & Autonomous Incident Response Acceptance Test")
    print("=" * 75)

    proj_dir = Path("./generated_projects/ObservabilityApp").resolve()
    proj_dir.mkdir(parents=True, exist_ok=True)

    # 1. Log Ingestion & Secret Redaction
    raw_log = "Failed request to /api/auth with token='eyJhbGciOiJIUzI1Ni...' and password='admin_secret_pass'"
    entry = global_log_manager.log("backend", "ERROR", raw_log)
    print(f"[OK] [1/6] Log Ingested & Secret Redacted: '{entry.message}'")
    assert "admin_secret_pass" not in entry.message

    # 2. Record API Performance Metrics & Error Clustering
    for _ in range(50):
        global_metrics_collector.record_request(latency_ms=45.0, is_error=False)
    global_metrics_collector.record_request(latency_ms=850.0, is_error=True)
    global_error_analyzer.record_error("DatabaseConnectionError: Connection timeout to PostgreSQL", "/api/todos")

    metrics = global_metrics_collector.get_metrics("backend")
    clusters = global_error_analyzer.get_clusters()
    print(f"[OK] [2/6] Metrics Collected: Requests={metrics.request_count}, P95={metrics.p95_latency_ms}ms, Error Clusters={len(clusters)}")
    assert metrics.request_count == 51
    assert len(clusters) > 0

    # 3. Simulate Controlled Failure & Incident Detection
    print("\n[RUN] [3/6] Introducing Controlled Backend Health Probe Failure...")
    inc = global_incident_detector.raise_incident(
        project_id="ObservabilityApp",
        service="backend",
        symptom="Backend Health Probe Returned HTTP 500",
        error_msg="DatabaseConnectionError: Failed to connect to postgresql://user:pass@db:5432/appdb"
    )
    print(f"[OK] [4/6] Incident Detected: ID='{inc.incident_id}', Severity='{inc.severity}', Status='{inc.status}'")
    assert inc.incident_id.startswith("inc_")

    # 4. Root Cause Analysis & Requirement/Git Correlation
    diag_inc = global_incident_diagnostic_agent.diagnose_incident(inc, proj_dir)
    print(f"[OK] [5/6] Root Cause Diagnosed: '{diag_inc.root_cause}', Git Commit='{diag_inc.git_commit}', Correlated Req='{diag_inc.requirement_id}'")
    assert diag_inc.status == "DIAGNOSED"

    # 5. Autonomous Remediation & INCIDENT_REPORT.md Generation
    res_inc = await global_observability_engine.trigger_autonomous_remediation(diag_inc.incident_id, proj_dir)
    print(f"[OK] [6/6] Autonomous Remediation Complete: Incident Status='{res_inc.status}'")
    assert res_inc.status in ["RESOLVED", "ROLLED_BACK"]
    assert (proj_dir / "INCIDENT_REPORT.md").exists()

    print("\n[SUCCESS] ALL OBSERVABILITY & AUTONOMOUS INCIDENT RESPONSE ACCEPTANCE TESTS PASSED!\n")


if __name__ == "__main__":
    asyncio.run(run_observability_acceptance())
