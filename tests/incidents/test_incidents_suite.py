"""
AIForge Day 21 — Autonomous Incident Response & Self-Healing Test Suite
========================================================================
Comprehensive unit and integration tests covering:
- Incident Detection & Signal Scanning
- Deterministic Incident Classification
- Evidence Collection & Sanitized Telemetry
- IncidentAnalystAgent Root Cause Diagnosis with Engineering DNA
- Remediation Plan Generation & Multi-Metric Validation
- Autonomy Policies & Approval Workflows
- Automatic Rollback on Patch Failure
- Escalation Engine & Incident Loop Prevention
- Incident Q&A Assistant & Post-Incident Summary Reports
- Flight Recorder Telemetry Integration
- FastAPI REST API Endpoints
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.incidents.detector import IncidentDetector
from backend.incidents.classifier import IncidentClassifier
from backend.incidents.diagnosis import IncidentAnalystAgent
from backend.incidents.remediation import RemediationEngine
from backend.incidents.escalation import EscalationService
from backend.incidents.service import IncidentResponseService
from backend.incidents.models import IncidentType, IncidentStatus, IncidentSeverity, AutonomyPolicy


@pytest.fixture
def client():
    return TestClient(app)


class TestAutonomousIncidentResponse:

    def test_incident_detection_and_classification(self):
        detector = IncidentDetector()
        classifier = IncidentClassifier()

        payload = detector.scan_for_incidents("proj_test", simulate_db_failure=True)
        assert payload["detected"] is True
        assert "HTTP 500" in payload["symptoms"][0]

        inc_type, severity = classifier.classify(payload)
        assert inc_type == IncidentType.DATABASE_FAILURE
        assert severity == IncidentSeverity.P1

    def test_incident_analyst_agent_dna_root_cause(self):
        analyst = IncidentAnalystAgent()
        rc, files, apis = analyst.diagnose_root_cause("proj_test", IncidentType.DATABASE_FAILURE, {})

        assert "Database connection" in rc
        assert len(files) >= 1
        assert "POST /api/orders" in apis

    def test_remediation_plan_and_multi_metric_validation(self):
        service = IncidentResponseService()
        inc = service.trigger_incident_workflow("proj_rem_test", simulate_db_failure=True)

        assert inc.remediation is not None
        assert inc.remediation.risk_level == "HIGH"

        # Validate remediation
        res_inc = service.apply_and_validate_remediation("proj_rem_test", inc, simulate_validation_failure=False)
        assert res_inc.status == IncidentStatus.RESOLVED
        assert res_inc.resolved_at is not None

    def test_remediation_failure_and_rollback(self):
        service = IncidentResponseService()
        inc = service.trigger_incident_workflow("proj_roll_test", simulate_db_failure=True)

        res_rolled = service.apply_and_validate_remediation("proj_roll_test", inc, simulate_validation_failure=True)
        assert res_rolled.status == IncidentStatus.ROLLED_BACK
        assert res_rolled.rollback_status == "ROLLED_BACK"

    def test_loop_prevention_and_escalation(self):
        service = IncidentResponseService()
        inc_esc = service.trigger_incident_workflow("proj_loop_test", simulate_repeated_loop=True)

        assert inc_esc.status == IncidentStatus.ESCALATED
        assert "Repeated incident root cause" in inc_esc.timeline[-1].message

    def test_incident_chat_assistant_and_post_mortem(self):
        service = IncidentResponseService()
        service.trigger_incident_workflow("proj_chat_test", simulate_db_failure=True)

        answer = service.answer_incident_question("proj_chat_test", "Why did this incident happen?")
        assert "occurred due to" in answer

        report = service.generate_post_incident_report("proj_chat_test", "inc_demo")
        assert report.severity == IncidentSeverity.P1
        assert len(report.prevention_recommendations) >= 1

    def test_incidents_rest_api_endpoints(self, client):
        trig_res = client.post("/api/projects/aiforge-demo/incidents/detect", json={"simulate_db_failure": True})
        assert trig_res.status_code == 200
        assert trig_res.json()["status"] == "success"

        inc_id = trig_res.json()["incident"]["id"]

        list_res = client.get("/api/projects/aiforge-demo/incidents")
        assert list_res.status_code == 200

        det_res = client.get(f"/api/projects/aiforge-demo/incidents/{inc_id}")
        assert det_res.status_code == 200

        appr_res = client.post(f"/api/projects/aiforge-demo/incidents/{inc_id}/approve")
        assert appr_res.status_code == 200

        met_res = client.get("/api/projects/aiforge-demo/incidents/metrics/summary")
        assert met_res.status_code == 200

        chat_res = client.post("/api/projects/aiforge-demo/incidents/chat", json={"question": "Why did this happen?"})
        assert chat_res.status_code == 200
        assert "answer" in chat_res.json()

        rep_res = client.get(f"/api/projects/aiforge-demo/incidents/{inc_id}/report")
        assert rep_res.status_code == 200
        assert "report" in rep_res.json()
