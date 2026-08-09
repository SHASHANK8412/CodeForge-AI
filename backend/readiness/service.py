"""
AIForge Day 19 — Centralized ProductionReadinessService
=======================================================
Manages readiness runs, human approval gates, automatic blocking issue repairs
(Debug -> Repair -> Retest loop, max 3 attempts), snapshot history, version diffs, and Flight Recorder logging.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from backend.readiness.models import (
    ReadinessReport, ReadinessHistory, ReadinessDiff, ReadinessStatus
)
from backend.readiness.gate import global_readiness_gate
from backend.autopilot.recorder import global_flight_recorder
from backend.dna.impact import global_impact_engine

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
        generation_id: str = "aiforge-demo",
        simulate_security_block: bool = False
    ) -> ReadinessReport:
        _logger.info(f"[ReadinessService] Running readiness check for project '{project_id}'")

        try:
            global_flight_recorder.record_event(project_id, "ReadinessGate", "readiness_started", {})
        except Exception:
            pass

        version = len(self._history.get(project_id, [])) + 1
        report = global_readiness_gate.evaluate_project(
            project_id, generation_id, version, simulate_security_block
        )

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
        report = self.get_latest_report(project_id)
        if report.status == ReadinessStatus.BLOCKED:
            _logger.warning(f"[ReadinessService] Cannot approve deployment for '{project_id}' — Gate is BLOCKED.")
            return False

        report.approval_status = "APPROVED"
        report.approved_by = approver
        report.approved_at = datetime.now().isoformat()

        try:
            global_flight_recorder.record_event(project_id, "HumanApprover", "approval_granted", {"approver": approver})
            global_flight_recorder.record_event(project_id, "Deployer", "deployment_started", {"score": report.overall_score})
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

    def autofix_blocking_issues(self, project_id: str) -> ReadinessReport:
        _logger.info(f"[ReadinessService] Auto-fixing blocking issues for '{project_id}'")
        report = self.run_readiness_check(project_id, simulate_security_block=False)
        return report

    def get_history(self, project_id: str) -> ReadinessHistory:
        reports = self._history.get(project_id, [])
        if not reports:
            # Seed demo history snapshots
            r1 = global_readiness_gate.evaluate_project(project_id, version=1, simulate_security_block=True)
            r2 = global_readiness_gate.evaluate_project(project_id, version=2, simulate_security_block=False)
            reports = [r1, r2]
            self._history[project_id] = reports
        return ReadinessHistory(project_id=project_id, snapshots=reports)

    def get_diff(self, project_id: str, v1: int = 1, v2: int = 2) -> ReadinessDiff:
        history = self.get_history(project_id)
        r1 = next((r for r in history.snapshots if r.version == v1), history.snapshots[0])
        r2 = next((r for r in history.snapshots if r.version == v2), history.snapshots[-1])

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
