"""
AIForge Deployment Monitor & Incident Response Engine
=====================================================
Monitors running deployments, tracks latency, 5xx errors, and container health,
raising structured INCIDENT reports when outages or failures occur.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

_logger = logging.getLogger("aiforge.deployment.monitor")


class IncidentRecord(BaseModel):
    incident_id: str
    project_id: str
    severity: str  # CRITICAL, HIGH, MEDIUM
    issue: str
    failed_url: str
    timestamp: float
    status: str = "OPEN"  # OPEN, REPAIRED, ROLLED_BACK


class DeploymentMonitor:
    """
    Background monitoring engine for deployed application instances.
    """

    def __init__(self):
        self._incidents: List[IncidentRecord] = []

    def record_incident(self, project_id: str, issue: str, url: str, severity: str = "HIGH") -> IncidentRecord:
        inc_id = f"inc_{int(time.time() * 1000)}"
        inc = IncidentRecord(
            incident_id=inc_id,
            project_id=project_id,
            severity=severity,
            issue=issue,
            failed_url=url,
            timestamp=time.time()
        )
        self._incidents.insert(0, inc)
        _logger.error(f"DeploymentMonitor: Raised INCIDENT '{inc_id}' for '{project_id}': {issue}")
        return inc

    def get_active_incidents(self, project_id: Optional[str] = None) -> List[IncidentRecord]:
        if project_id:
            return [inc for inc in self._incidents if inc.project_id == project_id and inc.status == "OPEN"]
        return [inc for inc in self._incidents if inc.status == "OPEN"]


global_deployment_monitor = DeploymentMonitor()
