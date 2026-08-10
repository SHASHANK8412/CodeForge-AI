"""
AIForge Day 21 — Deterministic Incident Classifier
===================================================
Maps detected symptoms and evidence to IncidentType and IncidentSeverity.
"""

import logging
from typing import Dict, Any, Tuple

from backend.incidents.models import IncidentType, IncidentSeverity

_logger = logging.getLogger("aiforge.incidents.classifier")


class IncidentClassifier:
    """
    Classifies incidents using deterministic rules.
    """

    def classify(self, detection_payload: Dict[str, Any]) -> Tuple[IncidentType, IncidentSeverity]:
        symptoms = [s.lower() for s in detection_payload.get("symptoms", [])]
        ev_str = str(detection_payload.get("evidence", "")).lower()

        if any("database" in s or "psycopg2" in ev_str for s in symptoms):
            return IncidentType.DATABASE_FAILURE, IncidentSeverity.P1

        if any("p95" in s or "latency" in s for s in symptoms):
            return IncidentType.PERFORMANCE_REGRESSION, IncidentSeverity.P2

        if any("auth" in s or "jwt" in ev_str for s in symptoms):
            return IncidentType.AUTHENTICATION_FAILURE, IncidentSeverity.P0

        if any("500" in s or "api" in s for s in symptoms):
            return IncidentType.API_FAILURE, IncidentSeverity.P1

        return IncidentType.APPLICATION_ERROR, IncidentSeverity.P2


global_incident_classifier = IncidentClassifier()
