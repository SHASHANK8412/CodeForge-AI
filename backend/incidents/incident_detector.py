"""
AIForge Incident Detector Module
================================
Monitors health checks, error rates, container status, and E2E regressions,
creating structured IncidentRecord models when threshold conditions are violated.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

_logger = logging.getLogger("aiforge.incidents.detector")


class IncidentRecord(BaseModel):
    incident_id: str
    project_id: str
    deployment_id: Optional[str] = None
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    service: str  # frontend, backend, database
    started_at: float = Field(default_factory=time.time)
    symptoms: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    status: str = "DETECTED"  # DETECTED, INVESTIGATING, DIAGNOSED, REPAIRING, VERIFYING, RESOLVED, ROLLED_BACK, FAILED
    git_commit: Optional[str] = None
    requirement_id: Optional[str] = None
    root_cause: Optional[str] = None


class IncidentDetector:
    """
    Automated incident detection engine.
    """

    def __init__(self):
        self._incidents: List[IncidentRecord] = []

    def raise_incident(
        self,
        project_id: str,
        service: str,
        symptom: str,
        error_msg: str,
        severity: str = "HIGH",
        deployment_id: Optional[str] = None
    ) -> IncidentRecord:
        inc_id = f"inc_{int(time.time() * 1000)}"
        inc = IncidentRecord(
            incident_id=inc_id,
            project_id=project_id,
            deployment_id=deployment_id,
            severity=severity,
            service=service,
            symptoms=[symptom],
            errors=[error_msg],
            status="DETECTED"
        )
        self._incidents.insert(0, inc)
        _logger.error(f"IncidentDetector: Raised {severity} incident '{inc_id}' on {service}: {symptom}")
        return inc

    def get_incidents(self, project_id: Optional[str] = None) -> List[IncidentRecord]:
        if project_id:
            return [i for i in self._incidents if i.project_id == project_id]
        return list(self._incidents)


global_incident_detector = IncidentDetector()
