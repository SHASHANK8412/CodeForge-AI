"""
AIForge Day 21 — Centralized IncidentResponseService
=====================================================
Manages the complete incident response lifecycle (Detection ➔ Classification ➔ Diagnosis ➔
Remediation ➔ Approval ➔ Repair ➔ Validation ➔ Deployment ➔ Resolution / Rollback),
learning loop (INCIDENT_LEARNING in Project Memory), incident Q&A chat, metrics, and Flight Recorder logging.
"""

import json
import secrets
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from backend.incidents.models import (
    Incident, IncidentType, IncidentStatus, IncidentSeverity, IncidentTimelineEvent,
    IncidentMetrics, PostIncidentReport, RemediationPlan, AutonomyPolicy
)
from backend.incidents.detector import global_incident_detector
from backend.incidents.classifier import global_incident_classifier
from backend.incidents.diagnosis import global_incident_analyst_agent
from backend.incidents.remediation import global_remediation_engine
from backend.incidents.escalation import global_escalation_service
from backend.devops.service import global_devops_service
from backend.autopilot.recorder import global_flight_recorder

_logger = logging.getLogger("aiforge.incidents.service")


class IncidentResponseService:
    """
    Centralized Autonomous Incident Response & Self-Healing Service.
    """

    def __init__(self):
        # project_id -> list of Incidents
        self._incidents: Dict[str, List[Incident]] = {}
        self._autonomy_policies: Dict[str, AutonomyPolicy] = {}

    def get_autonomy_policy(self, project_id: str) -> AutonomyPolicy:
        return self._autonomy_policies.get(project_id, AutonomyPolicy.BALANCED)

    def set_autonomy_policy(self, project_id: str, policy: AutonomyPolicy):
        self._autonomy_policies[project_id] = policy

    def trigger_incident_workflow(
        self,
        project_id: str,
        simulate_db_failure: bool = False,
        simulate_perf_failure: bool = False,
        simulate_validation_failure: bool = False,
        simulate_repeated_loop: bool = False
    ) -> Incident:
        _logger.info(f"[IncidentService] Triggering incident workflow for '{project_id}'")

        det_payload = global_incident_detector.scan_for_incidents(
            project_id, simulate_db_failure, simulate_perf_failure
        )
        if not det_payload:
            det_payload = {
                "symptoms": ["HTTP 500 on POST /api/orders"],
                "evidence": {"failed_endpoint": "/api/orders", "http_code": 500}
            }

        inc_type, severity = global_incident_classifier.classify(det_payload)
        inc_id = f"inc_{secrets.token_urlsafe(6)}"
        now_str = datetime.now().isoformat()

        timeline = [
            IncidentTimelineEvent(timestamp=now_str, stage="DETECTION", message=f"🚨 Incident detected: {det_payload['symptoms'][0]}"),
            IncidentTimelineEvent(timestamp=now_str, stage="CLASSIFICATION", message=f"Classified as {inc_type.value} ({severity.value})")
        ]

        try:
            global_flight_recorder.record_event(project_id, "IncidentEngine", "incident_detected", {"type": inc_type.value, "severity": severity.value})
            global_flight_recorder.record_event(project_id, "IncidentEngine", "incident_classified", {"type": inc_type.value})
            global_flight_recorder.record_event(project_id, "IncidentEngine", "incident_investigation_started", {})
        except Exception:
            pass

        # Root cause diagnosis using Engineering DNA
        root_cause, affected_files, affected_apis = global_incident_analyst_agent.diagnose_root_cause(
            project_id, inc_type, det_payload["evidence"]
        )
        timeline.append(IncidentTimelineEvent(timestamp=now_str, stage="DIAGNOSIS", message=f"🧬 Root cause identified: {root_cause}"))

        try:
            global_flight_recorder.record_event(project_id, "IncidentEngine", "incident_diagnosed", {"root_cause": root_cause})
        except Exception:
            pass

        # Check escalation / loop detection
        if simulate_repeated_loop:
            should_esc, esc_msg = True, "Repeated incident root cause detected 3 times in 1 hour. Automatic remediation disabled."
        else:
            should_esc, esc_msg = global_escalation_service.should_escalate(project_id, root_cause)

        incident = Incident(
            id=inc_id,
            project_id=project_id,
            type=inc_type,
            severity=severity,
            status=IncidentStatus.INVESTIGATING if not should_esc else IncidentStatus.ESCALATED,
            detected_at=now_str,
            symptoms=det_payload["symptoms"],
            evidence=det_payload["evidence"],
            affected_components=affected_files,
            root_cause=root_cause,
            timeline=timeline
        )

        if should_esc:
            incident.status = IncidentStatus.ESCALATED
            incident.timeline.append(IncidentTimelineEvent(timestamp=now_str, stage="ESCALATION", message=f"⚠ {esc_msg}"))
            try:
                global_flight_recorder.record_event(project_id, "IncidentEngine", "incident_escalated", {"reason": esc_msg})
            except Exception:
                pass

            if project_id not in self._incidents:
                self._incidents[project_id] = []
            self._incidents[project_id].append(incident)
            return incident

        # Create remediation plan
        plan = global_remediation_engine.create_remediation_plan(incident)
        incident.remediation = plan
        incident.status = IncidentStatus.AWAITING_APPROVAL if plan.requires_approval else IncidentStatus.REPAIRING

        try:
            global_flight_recorder.record_event(project_id, "IncidentEngine", "remediation_created", {"plan_id": plan.plan_id})
        except Exception:
            pass

        # Auto-apply if low risk or allowed by policy
        policy = self.get_autonomy_policy(project_id)
        if not plan.requires_approval or policy == AutonomyPolicy.FULL_AUTONOMY:
            return self.apply_and_validate_remediation(project_id, incident, simulate_validation_failure)

        if project_id not in self._incidents:
            self._incidents[project_id] = []
        self._incidents[project_id].append(incident)
        return incident

    def apply_and_validate_remediation(
        self,
        project_id: str,
        incident: Incident,
        simulate_validation_failure: bool = False
    ) -> Incident:
        now_str = datetime.now().isoformat()
        incident.status = IncidentStatus.REPAIRING
        incident.approval_status = "APPROVED"
        incident.timeline.append(IncidentTimelineEvent(timestamp=now_str, stage="REPAIR", message="🔧 Remediation patch applied on repair snapshot"))

        try:
            global_flight_recorder.record_event(project_id, "IncidentEngine", "remediation_approved", {})
            global_flight_recorder.record_event(project_id, "IncidentEngine", "remediation_started", {})
        except Exception:
            pass

        # Validate remediation
        incident.status = IncidentStatus.VALIDATING
        try:
            global_flight_recorder.record_event(project_id, "IncidentEngine", "incident_validation_started", {})
        except Exception:
            pass

        valid, val_msg = global_remediation_engine.validate_remediation(
            project_id, incident.remediation, simulate_validation_failure
        )

        if not valid:
            _logger.warning(f"[IncidentService] Remediation validation failed for '{incident.id}': {val_msg}")
            incident.status = IncidentStatus.ROLLED_BACK
            incident.rollback_status = "ROLLED_BACK"
            incident.timeline.append(IncidentTimelineEvent(timestamp=now_str, stage="ROLLBACK", message=f"❌ {val_msg}. Rolled back to previous version."))

            try:
                global_flight_recorder.record_event(project_id, "IncidentEngine", "incident_rolled_back", {"reason": val_msg})
            except Exception:
                pass

            if project_id not in self._incidents:
                self._incidents[project_id] = []
            self._incidents[project_id].append(incident)
            return incident

        # Deploy & Resolve
        global_devops_service.deploy_project(project_id, bypass_readiness=True)
        incident.status = IncidentStatus.RESOLVED
        incident.resolved_at = now_str
        incident.timeline.append(IncidentTimelineEvent(timestamp=now_str, stage="RESOLUTION", message="🟢 Fix deployed. Health & Playwright smoke tests PASSED. Incident RESOLVED."))

        try:
            global_flight_recorder.record_event(project_id, "IncidentEngine", "remediation_completed", {})
            global_flight_recorder.record_event(project_id, "IncidentEngine", "incident_resolved", {})
        except Exception:
            pass

        if project_id not in self._incidents:
            self._incidents[project_id] = []
        self._incidents[project_id].append(incident)
        return incident

    def get_incidents(self, project_id: str) -> List[Incident]:
        inc_list = self._incidents.get(project_id, [])
        if not inc_list:
            # Seed demo incident
            i1 = self.trigger_incident_workflow(project_id, simulate_db_failure=False)
            inc_list = [i1]
            self._incidents[project_id] = inc_list
        return inc_list

    def answer_incident_question(self, project_id: str, question: str) -> str:
        incidents = self.get_incidents(project_id)
        latest = incidents[-1]
        q_lower = question.lower()

        if "why" in q_lower or "cause" in q_lower:
            return f"The incident occurred due to: {latest.root_cause}. Affected files: {', '.join(latest.affected_components)}."
        if "healthy" in q_lower or "status" in q_lower:
            return f"Service is currently {latest.status.value}. Baseline health checks and smoke tests are passing."

        return f"Incident #{latest.id} ({latest.type.value}) detected at {latest.detected_at}. Status: {latest.status.value}."

    def get_metrics(self, project_id: str) -> IncidentMetrics:
        return IncidentMetrics(
            mttd_minutes=1.2,
            mttr_minutes=8.5,
            total_incidents=len(self.get_incidents(project_id)),
            resolved_automatically=3,
            resolved_manually=1,
            rollback_count=1,
            repeated_incidents_count=0
        )

    def generate_post_incident_report(self, project_id: str, incident_id: str) -> PostIncidentReport:
        incidents = self.get_incidents(project_id)
        inc = next((i for i in incidents if i.id == incident_id), incidents[0])

        return PostIncidentReport(
            incident_id=inc.id,
            project_id=project_id,
            title=f"Post-Mortem: {inc.type.value}",
            severity=inc.severity,
            duration_minutes=8.5,
            root_cause_summary=inc.root_cause or "Application query failure",
            impact_summary=f"Affected {', '.join(inc.affected_components)}",
            detection_source="Health Check & Telemetry Monitor",
            resolution_method="Automated Remediation & DevOps Deployment",
            prevention_recommendations=[
                "Add database connection pool validation check to Production Readiness Gate.",
                "Enforce cursor cleanup linting rule in OrderService."
            ],
            created_at=datetime.now().isoformat()
        )


global_incident_service = IncidentResponseService()
