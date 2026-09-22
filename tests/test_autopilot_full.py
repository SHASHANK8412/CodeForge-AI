"""
tests/test_autopilot_full.py
==============================
Comprehensive unit & integration tests for AIForge Engineering Autopilot & Flight Recorder.
"""

import asyncio
import pytest
from fastapi.testclient import TestClient

from backend.autopilot.models import AutonomyLevel, AutopilotStatus, DecisionType
from backend.autopilot.controller import global_autopilot_controller
from backend.autopilot.decisions import global_decision_manager
from backend.autopilot.approval import global_approval_manager
from backend.autopilot.recorder import global_flight_recorder
from backend.autopilot.service import global_autopilot_service


@pytest.fixture()
def app_client():
    from backend.main import app
    return TestClient(app, raise_server_exceptions=True)


class TestEngineeringAutopilot:

    def test_autopilot_start(self):
        res = asyncio.run(global_autopilot_service.start(
            project_id="proj_auto_001",
            user_id="user_test_01",
            prompt="Build a task management platform with FastAPI and React",
            autonomy_level="BALANCED"
        ))
        assert res["status"] == "ACTIVE"
        assert "generation_id" in res

    def test_autopilot_pause(self):
        gen_res = asyncio.run(global_autopilot_service.start("proj_auto_002", "user_test_01", "Build e-commerce app"))
        gen_id = gen_res["generation_id"]

        pause_res = global_autopilot_service.pause(gen_id)
        assert pause_res["status"] == "PAUSED"
        assert global_autopilot_controller.get_status(gen_id) == AutopilotStatus.PAUSED

    def test_autopilot_resume(self):
        gen_res = asyncio.run(global_autopilot_service.start("proj_auto_003", "user_test_01", "Build analytics dashboard"))
        gen_id = gen_res["generation_id"]

        global_autopilot_service.pause(gen_id)
        resume_res = global_autopilot_service.resume(gen_id)
        assert resume_res["status"] == "ACTIVE"
        assert global_autopilot_controller.get_status(gen_id) == AutopilotStatus.ACTIVE

    def test_autopilot_stop(self):
        gen_res = asyncio.run(global_autopilot_service.start("proj_auto_004", "user_test_01", "Build CRM tool"))
        gen_id = gen_res["generation_id"]

        stop_res = global_autopilot_service.stop(gen_id)
        assert stop_res["status"] == "STOPPED"

    def test_approval_gate(self):
        gen_id = "gen_approval_test"
        req = global_approval_manager.create_request(gen_id, "Modify database schema", "Required for order entity FK")
        assert req.status == "PENDING"

        pending = global_approval_manager.get_pending_request(gen_id)
        assert pending.id == req.id

        approved = global_approval_manager.approve_request(gen_id, req.id)
        assert approved is True
        assert global_approval_manager.get_pending_request(gen_id) is None

    def test_decision_recording(self):
        gen_id = "gen_decision_test"
        card = global_decision_manager.record_decision(
            generation_id=gen_id,
            type=DecisionType.ARCHITECTURE,
            title="PostgreSQL Selected",
            summary="Selected PostgreSQL database",
            reason="Relational order and user entities",
            evidence=["User model", "Order FK"],
            impact="Architecture: +8",
            confidence=0.92,
            sources=["[S1] architecture.json"]
        )
        assert card.title == "PostgreSQL Selected"
        assert card.confidence == 0.92

        decisions = global_decision_manager.get_decisions(gen_id)
        assert len(decisions) == 1
        assert decisions[0].id == card.id

    def test_flight_recorder(self):
        evt = global_flight_recorder.record_event(
            generation_id="gen_fre_001",
            project_id="proj_fre_001",
            stage="BUILD",
            agent="backend",
            event_type="stage_completed",
            decision="FastAPI REST API generated",
            files_changed=["backend/main.py"]
        )
        assert evt.agent == "backend"

        events = global_flight_recorder.get_events("proj_fre_001")
        assert len(events) >= 1

        analytics = global_flight_recorder.get_analytics("proj_fre_001")
        assert "automatic_repairs" in analytics

    def test_autopilot_ownership_and_api(self, app_client):
        res = app_client.get("/api/autopilot/aiforge-demo")
        assert res.status_code == 200
        body = res.json()
        assert body["status"] in ("success", "completed")
        assert "decisions" in body

    def test_autopilot_recovery(self):
        state = global_autopilot_service.get_autopilot_state("aiforge-demo", "user_test_01")
        assert state["status"] in ("completed", "ACTIVE", "PAUSED")
        assert len(state["decisions"]) >= 1

    def test_autopilot_completion(self):
        gen_res = asyncio.run(global_autopilot_service.start("proj_comp", "user_test_01", "Build SaaS app"))
        gen_id = gen_res["generation_id"]

        state = global_autopilot_service.get_autopilot_state(gen_id, "user_test_01")
        assert state["generation_id"] == gen_id

    def test_autopilot_failure(self):
        gen_res = asyncio.run(global_autopilot_service.start("proj_fail", "user_test_01", "Build broken app"))
        gen_id = gen_res["generation_id"]

        stop_res = global_autopilot_service.stop(gen_id)
        assert stop_res["status"] == "STOPPED"
