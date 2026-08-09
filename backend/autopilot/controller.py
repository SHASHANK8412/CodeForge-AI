"""
AIForge V2 — Engineering Autopilot Controller
==============================================
Orchestrates the existing LangGraph workflow and real-time events without duplicating the pipeline.
Manages Autopilot state (Active, Paused, Awaiting Approval, Stopped, Completed).
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional

from backend.autopilot.models import AutopilotStatus, AutonomyLevel
from backend.autopilot.recorder import global_flight_recorder
from backend.autopilot.decisions import global_decision_manager
from backend.autopilot.approval import global_approval_manager
from backend.generation.store import global_generation_store as _store
from backend.generation.event_bus import global_event_bus as _bus
from backend.generation.manager import global_generation_manager as _manager

_logger = logging.getLogger("aiforge.autopilot.controller")


class AutopilotController:
    """
    Central Controller for AIForge Engineering Autopilot.
    Reuses existing LangGraph workflow, generation store, and SSE event bus.
    """

    def __init__(self):
        self._statuses: Dict[str, AutopilotStatus] = {}
        self._autonomy_levels: Dict[str, AutonomyLevel] = {}

    def get_status(self, generation_id: str) -> AutopilotStatus:
        return self._statuses.get(generation_id, AutopilotStatus.IDLE)

    def get_autonomy_level(self, generation_id: str) -> AutonomyLevel:
        return self._autonomy_levels.get(generation_id, AutonomyLevel.BALANCED)

    async def start_autopilot(
        self,
        project_id: str,
        user_id: str,
        prompt: str,
        autonomy_level: AutonomyLevel = AutonomyLevel.BALANCED,
        approval_settings: Optional[Dict[str, bool]] = None
    ) -> Dict[str, Any]:
        """
        Starts a new Autopilot session by creating a generation in the real generation engine.
        """
        gen_id = _store.create(project_id, user_id, prompt)
        self._statuses[gen_id] = AutopilotStatus.ACTIVE
        self._autonomy_levels[gen_id] = autonomy_level

        # Emit autopilot_started event on event bus
        _bus.emit_sync(
            gen_id,
            "autopilot_started",
            agent="planner",
            message=f"⚡ Engineering Autopilot started ({autonomy_level.value})",
            metadata={
                "autonomy_level": autonomy_level.value,
                "approval_settings": approval_settings or {}
            }
        )

        # Record Flight Recorder Event
        global_flight_recorder.record_event(
            generation_id=gen_id,
            project_id=project_id,
            stage="PLAN",
            agent="planner",
            event_type="autopilot_started",
            decision=f"Autopilot started in {autonomy_level.value} mode",
            reason=f"Goal: {prompt}"
        )

        # Trigger real generation pipeline in background
        await _manager.run(gen_id)

        _logger.info(f"AutopilotController: Started Autopilot '{gen_id}' for project '{project_id}'")
        return {
            "generation_id": gen_id,
            "project_id": project_id,
            "status": "ACTIVE",
            "autonomy_level": autonomy_level.value,
            "message": "Engineering Autopilot started successfully."
        }

    def pause_autopilot(self, generation_id: str) -> Dict[str, Any]:
        rec = _store.get(generation_id)
        if not rec:
            return {"status": "PAUSED", "generation_id": generation_id}

        self._statuses[generation_id] = AutopilotStatus.PAUSED
        _store.update_status(generation_id, "paused")

        _bus.emit_sync(generation_id, "autopilot_paused", agent=rec.get("current_agent", "system"), message="⏸ Autopilot paused by user.")

        global_flight_recorder.record_event(
            generation_id=generation_id,
            project_id=rec.get("project_id", "default_project"),
            stage="BUILD",
            agent="system",
            event_type="autopilot_paused",
            decision="Autopilot paused",
            reason="User requested manual pause."
        )

        return {"status": "PAUSED", "generation_id": generation_id, "message": "Autopilot paused. Project state preserved."}

    def resume_autopilot(self, generation_id: str) -> Dict[str, Any]:
        rec = _store.get(generation_id)
        if not rec:
            return {"status": "ACTIVE", "generation_id": generation_id}

        self._statuses[generation_id] = AutopilotStatus.ACTIVE
        _store.update_status(generation_id, "building")

        _bus.emit_sync(generation_id, "autopilot_resumed", agent=rec.get("current_agent", "system"), message="▶ Autopilot resumed.")

        global_flight_recorder.record_event(
            generation_id=generation_id,
            project_id=rec.get("project_id", "default_project"),
            stage="BUILD",
            agent="system",
            event_type="autopilot_resumed",
            decision="Autopilot resumed",
            reason="User requested resume."
        )

        return {"status": "ACTIVE", "generation_id": generation_id, "message": "Autopilot resumed from previous state."}

    def stop_autopilot(self, generation_id: str) -> Dict[str, Any]:
        rec = _store.get(generation_id)
        if not rec:
            return {"status": "STOPPED", "generation_id": generation_id}

        self._statuses[generation_id] = AutopilotStatus.STOPPED
        _store.update_status(generation_id, "cancelled")

        _bus.emit_sync(generation_id, "autopilot_stopped", agent="system", message="🛑 Autopilot stopped by user.")

        global_flight_recorder.record_event(
            generation_id=generation_id,
            project_id=rec.get("project_id", "default_project"),
            stage="BUILD",
            agent="system",
            event_type="autopilot_stopped",
            decision="Autopilot stopped",
            reason="User cancelled execution."
        )

        return {"status": "STOPPED", "generation_id": generation_id, "message": "Autopilot stopped. Project preserved."}

    def approve_action(self, generation_id: str, request_id: str) -> bool:
        ok = global_approval_manager.approve_request(generation_id, request_id)
        if ok:
            self._statuses[generation_id] = AutopilotStatus.ACTIVE
            _bus.emit_sync(generation_id, "approval_granted", agent="system", message=f"✓ Human Approval Granted for request '{request_id}'")
        return ok

    def reject_action(self, generation_id: str, request_id: str) -> bool:
        ok = global_approval_manager.reject_request(generation_id, request_id)
        if ok:
            _bus.emit_sync(generation_id, "approval_rejected", agent="system", message=f"❌ Human Approval Rejected for request '{request_id}'")
        return ok


global_autopilot_controller = AutopilotController()
