"""
AIForge Observability & Autonomous Incident Response Engine
===========================================================
Orchestrates logging, metrics, health probing, incident detection, root cause diagnosis,
autonomous remediation (restart, repair, rollback), and INCIDENT_REPORT.md generation.
"""

import time
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from backend.observability.log_manager import global_log_manager, LogEntry
from backend.observability.metrics_collector import global_metrics_collector, ServiceMetrics
from backend.observability.error_analyzer import global_error_analyzer
from backend.incidents.incident_detector import global_incident_detector, IncidentRecord
from backend.incidents.incident_diagnostic_agent import global_incident_diagnostic_agent
from backend.deployment.rollback_manager import global_rollback_manager
from backend.execution.health_checker import global_health_checker

_logger = logging.getLogger("aiforge.incidents.observability_engine")


class ObservabilityEngine:
    """
    Unified Observability & Autonomous Incident Response Engine.
    """

    async def check_system_health(self, project_id: str, frontend_url: str, backend_url: str) -> Dict[str, Any]:
        be_res = await global_health_checker.check_health_async("backend", f"{backend_url}/health")
        fe_res = await global_health_checker.check_health_async("frontend", frontend_url)

        global_metrics_collector.record_request(be_res.response_time_ms, is_error=not be_res.is_healthy)
        metrics = global_metrics_collector.get_metrics("backend")

        if not be_res.is_healthy:
            global_log_manager.log("backend", "ERROR", f"Backend Health Failed: {be_res.error_message}")
            global_error_analyzer.record_error(be_res.error_message or "Health Failure", "/health")

            # Raise incident if not already detected
            inc = global_incident_detector.raise_incident(
                project_id=project_id,
                service="backend",
                symptom="Backend HTTP Health Probe Failed",
                error_msg=be_res.error_message or "Connection refused"
            )
            # Diagnosed by diagnostic agent
            global_incident_diagnostic_agent.diagnose_incident(inc)

        return {
            "project_id": project_id,
            "frontend_status": "HEALTHY" if fe_res.is_healthy else "UNHEALTHY",
            "backend_status": "HEALTHY" if be_res.is_healthy else "UNHEALTHY",
            "metrics": metrics.model_dump(),
            "active_incidents": [i.model_dump() for i in global_incident_detector.get_incidents(project_id)]
        }

    async def trigger_autonomous_remediation(self, incident_id: str, project_path: Optional[Path] = None) -> IncidentRecord:
        incidents = global_incident_detector.get_incidents()
        inc = next((i for i in incidents if i.incident_id == incident_id), None)

        if not inc:
            raise ValueError(f"Incident '{incident_id}' not found.")

        inc.status = "REPAIRING"
        _logger.info(f"ObservabilityEngine: Executing autonomous remediation for incident '{incident_id}'...")

        # If infrastructure / health probe, attempt rollback or restart
        try:
            rb_res = global_rollback_manager.trigger_rollback(
                reason=f"Autonomous Remediation for Incident {incident_id}",
                project_path=project_path
            )
            inc.status = "RESOLVED"
            _logger.info(f"ObservabilityEngine: Incident '{incident_id}' RESOLVED via rollback to '{rb_res['restored_version']}'")
        except Exception as e:
            inc.status = "FAILED"
            _logger.error(f"ObservabilityEngine: Remediation failed for '{incident_id}': {e}")

        if project_path and project_path.exists():
            self._write_incident_report(project_path, inc)

        return inc

    def _write_incident_report(self, project_path: Path, inc: IncidentRecord):
        content = (
            f"# AIForge Incident & Autonomous Response Report\n\n"
            f"**Incident ID**: `{inc.incident_id}`\n"
            f"**Severity**: `{inc.severity}`\n"
            f"**Status**: `{inc.status}`\n"
            f"**Service**: `{inc.service}`\n"
            f"**Git Commit**: `{inc.git_commit}`\n"
            f"**Requirement Correlated**: `{inc.requirement_id or 'N/A'}`\n\n"
            f"## Root Cause Analysis\n"
            f"{inc.root_cause or 'Under investigation'}\n\n"
            f"## Symptoms & Errors\n"
            f"- **Symptoms**: {', '.join(inc.symptoms)}\n"
            f"- **Errors**: {', '.join(inc.errors)}\n"
        )
        try:
            (project_path / "INCIDENT_REPORT.md").write_text(content, encoding="utf-8")
        except Exception:
            pass


global_observability_engine = ObservabilityEngine()
