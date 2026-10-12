"""
AIForge Day 19 — Centralized ProductionReadinessService
=======================================================
Manages readiness runs (evidence only, see checks.py), human approval, the history of real runs,
version diffs, and Flight Recorder logging. Readiness never repairs anything itself: fixes go through
the Security Guardian / Autopilot, and readiness is evaluated again afterwards.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List

from backend.readiness.models import (
    ReadinessReport, ReadinessHistory, ReadinessDiff, ReadinessStatus
)
from backend.readiness.gate import global_readiness_gate
from backend.autopilot.recorder import global_flight_recorder

_logger = logging.getLogger("aiforge.readiness.service")

MAX_READINESS_REPAIR_ATTEMPTS = 3


class ProductionReadinessService:
    """
    Centralized service for Autonomous Production Readiness Gate.
    """

    def __init__(self):
        # project_id -> list of ReadinessReports
        self._history: Dict[str, List[ReadinessReport]] = {}

    def run_readiness_check(
        self,
        project_id: str,
        generation_id: str = "",
        project=None,
    ) -> ReadinessReport:
        _logger.info(f"[ReadinessService] Running readiness check for project '{project_id}'")

        try:
            global_flight_recorder.record_event(project_id, "ReadinessGate", "readiness_started", {})
        except Exception:
            pass

        version = len(self._history.get(project_id, [])) + 1
        report = global_readiness_gate.evaluate_project(project_id, generation_id or project_id, version, project)

        if project_id not in self._history:
            self._history[project_id] = []
        self._history[project_id].append(report)

        for c in report.checks:
            try:
                global_flight_recorder.record_event(
                    project_id, "ReadinessGate", "readiness_check_completed",
                    {"category": c.category, "name": c.name, "status": c.status.value}
                )
            except Exception:
                pass

        if report.status == ReadinessStatus.BLOCKED:
            try:
                global_flight_recorder.record_event(project_id, "ReadinessGate", "readiness_blocked", {"blockers": report.blocking_issues})
            except Exception:
                pass
        else:
            try:
                global_flight_recorder.record_event(project_id, "ReadinessGate", "readiness_ready", {"score": report.overall_score})
            except Exception:
                pass

        return report

    def get_latest_report(self, project_id: str) -> ReadinessReport:
        reports = self._history.get(project_id, [])
        if reports:
            return reports[-1]
        return self.run_readiness_check(project_id)

    def approve_deployment(self, project_id: str, approver: str = "Chief Architect") -> bool:
        """Records a person's approval of the latest evaluation; refused when it is BLOCKED or INCOMPLETE.
        Approval does not deploy anything."""
        report = self.get_latest_report(project_id)
        if report.status in (ReadinessStatus.BLOCKED, ReadinessStatus.INCOMPLETE):
            _logger.warning("[ReadinessService] Cannot approve '%s': readiness is %s.", project_id, report.status.value)
            return False

        report.approval_status = "APPROVED"
        report.approved_by = approver
        report.approved_at = datetime.now().isoformat()

        try:
            global_flight_recorder.record_event(project_id, "HumanApprover", "approval_granted", {"approver": approver})
        except Exception:
            pass

        return True

    def reject_deployment(self, project_id: str, approver: str = "Chief Architect") -> bool:
        report = self.get_latest_report(project_id)
        report.approval_status = "REJECTED"

        try:
            global_flight_recorder.record_event(project_id, "HumanApprover", "approval_rejected", {"approver": approver})
        except Exception:
            pass

        return True

    def get_history(self, project_id: str) -> ReadinessHistory:
        return ReadinessHistory(project_id=project_id, snapshots=list(self._history.get(project_id, [])))

    def get_diff(self, project_id: str, v1: int = 1, v2: int = 2) -> ReadinessDiff:
        """Raises KeyError when either version was never evaluated."""
        history = self.get_history(project_id)
        r1 = next((r for r in history.snapshots if r.version == v1), None)
        r2 = next((r for r in history.snapshots if r.version == v2), None)
        if r1 is None or r2 is None:
            raise KeyError(f"readiness version {v1 if r1 is None else v2} was not evaluated")

        return ReadinessDiff(
            old_version=v1,
            new_version=v2,
            score_change=round(r2.overall_score - r1.overall_score, 1),
            old_status=r1.status,
            new_status=r2.status,
            resolved_blockers=r1.blocking_issues,
            new_warnings=r2.warnings
        )

    def export_report_json(self, project_id: str) -> str:
        report = self.get_latest_report(project_id)
        return json.dumps(report.model_dump(), indent=2)


global_readiness_service = ProductionReadinessService()
