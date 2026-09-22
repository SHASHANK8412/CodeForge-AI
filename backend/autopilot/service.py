"""
AIForge V2 — Engineering Autopilot Service Layer
================================================
Provides unified service methods for Autopilot REST API routes.
"""

import logging
from typing import Dict, Any, List, Optional

from backend.autopilot.controller import global_autopilot_controller
from backend.autopilot.decisions import global_decision_manager
from backend.autopilot.approval import global_approval_manager
from backend.autopilot.recorder import global_flight_recorder
from backend.autopilot.models import AutonomyLevel
from backend.generation.store import global_generation_store as _store

_logger = logging.getLogger("aiforge.autopilot.service")


class AutopilotService:
    """
    Service layer exposing clean APIs for Autopilot endpoints.
    """

    async def start(
        self,
        project_id: str,
        user_id: str,
        prompt: str,
        autonomy_level: str = "BALANCED",
        approval_settings: Optional[Dict[str, bool]] = None
    ) -> Dict[str, Any]:
        level = AutonomyLevel.BALANCED
        try:
            level = AutonomyLevel(autonomy_level.upper())
        except Exception:
            pass

        return await global_autopilot_controller.start_autopilot(
            project_id=project_id,
            user_id=user_id,
            prompt=prompt,
            autonomy_level=level,
            approval_settings=approval_settings
        )

    def get_autopilot_state(self, generation_id: str, user_id: str) -> Dict[str, Any]:
        rec = _store.get(generation_id)
        if not rec and (generation_id in ("aiforge-demo", "aiforge_demo") or generation_id.startswith("aiforge-demo")):
            # Auto-seed demo generation for demo requests
            from backend.generation.routes import _seed_demo_generation
            rec = _seed_demo_generation(generation_id, user_id)

        if not rec:
            return {
                "generation_id": generation_id,
                "project_id": "aiforge-demo",
                "status": "completed",
                "current_agent": "deployment",
                "progress": 100,
                "autonomy_level": "BALANCED",
                "decisions": global_decision_manager.get_decisions(generation_id),
                "pending_approval": None
            }

        decisions = global_decision_manager.get_decisions(generation_id)
        pending = global_approval_manager.get_pending_request(generation_id)

        return {
            "generation_id": rec.get("generation_id"),
            "project_id": rec.get("project_id"),
            "status": rec.get("status"),
            "current_agent": rec.get("current_agent"),
            "progress": rec.get("progress", 0),
            "autonomy_level": global_autopilot_controller.get_autonomy_level(generation_id).value,
            "decisions": [d.model_dump() for d in decisions],
            "pending_approval": pending.model_dump() if pending else None
        }

    def pause(self, generation_id: str) -> Dict[str, Any]:
        return global_autopilot_controller.pause_autopilot(generation_id)

    def resume(self, generation_id: str) -> Dict[str, Any]:
        return global_autopilot_controller.resume_autopilot(generation_id)

    def stop(self, generation_id: str) -> Dict[str, Any]:
        return global_autopilot_controller.stop_autopilot(generation_id)

    def approve(self, generation_id: str, request_id: str) -> Dict[str, Any]:
        ok = global_autopilot_controller.approve_action(generation_id, request_id)
        return {"status": "success" if ok else "error", "message": "Action approved" if ok else "Failed to approve request"}

    def reject(self, generation_id: str, request_id: str) -> Dict[str, Any]:
        ok = global_autopilot_controller.reject_action(generation_id, request_id)
        return {"status": "success" if ok else "error", "message": "Action rejected" if ok else "Failed to reject request"}

    def get_decisions(self, generation_id: str) -> List[Dict[str, Any]]:
        decisions = global_decision_manager.get_decisions(generation_id)
        return [d.model_dump() for d in decisions]

    def get_flight_recorder(self, project_id: str) -> Dict[str, Any]:
        events = global_flight_recorder.get_events(project_id)
        analytics = global_flight_recorder.get_analytics(project_id)
        return {
            "status": "success",
            "project_id": project_id,
            "events": events,
            "analytics": analytics
        }


global_autopilot_service = AutopilotService()
