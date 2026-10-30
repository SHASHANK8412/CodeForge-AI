"""
AIForge Production Readiness (CTO) Gate
=======================================
Six dimensions (Security, Architecture, Testing, Performance, Database, Documentation), each computed from recorded
evidence (backend/quality/evidence.py: the Execution Guardian's latest verification, the Integration Engine's latest
run, the project's files). A dimension no recorded check covers is NOT_EVALUATED and has no score.

APPROVED only when every required dimension was evaluated and none failed. An override is a recorded human decision
(who, why, when): it changes the decision to APPROVED_BY_OVERRIDE and nothing else - scores, statuses and blocking
issues stay exactly as measured.
"""

import logging
import threading
from typing import Any, Dict, List, Optional

from backend.evolution.autopilot.models import now_iso
from backend.intelligence.models import CtoGateReport, ReadinessDimension

_logger = logging.getLogger("aiforge.intelligence.cto_gate")

DIMENSIONS = (
    # name, the evidence gates it is computed from, required for approval
    ("Security", ("Static Security Scan",), True),
    ("Architecture", ("API Contract Compatibility",), True),
    ("Testing", ("Python Tests", "Frontend Tests"), True),
    ("Performance", ("Performance",), False),
    ("Database", ("Database Compatibility",), True),
    ("Documentation", ("Documentation",), True),
)
RATED = ("PASSED", "FAILED", "WARNING", "BLOCKED")


class AutonomousCtoGate:
    def __init__(self) -> None:
        self._overrides: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = threading.Lock()

    def evaluate(self, project_id: str) -> CtoGateReport:
        from backend.quality import evidence
        try:
            from backend.routes.project import resolve_generated_project_dir
            project_dir = resolve_generated_project_dir(project_id)
        except Exception:  # noqa: BLE001 - an unknown project simply has no evidence
            project_dir = None
        gates = {g["name"][3:]: g for g in evidence.gates(evidence.collect(project_id, project_dir))}
        dims: List[ReadinessDimension] = []
        blocking: List[str] = []
        for name, sources, required in DIMENSIONS:
            rated = [gates[s] for s in sources if s in gates and gates[s]["status"] in RATED]
            if not rated:
                why = "; ".join(dict.fromkeys(gates[s]["findings"][0] for s in sources if s in gates)) or "no recorded check covers it"
                dims.append(ReadinessDimension(name=name, score=None, status="NOT_EVALUATED", blocking_issue=f"not evaluated: {why}"))
                if required:
                    blocking.append(f"{name} was not evaluated ({why})")
                continue
            passed = sum(1 for g in rated if g["status"] == "PASSED")
            score = round(100.0 * passed / len(rated), 1)
            failed = [g for g in rated if g["status"] in ("FAILED", "BLOCKED")]
            status = "FAIL" if failed else "WARN" if passed < len(rated) else "PASS"
            issue = "; ".join(f"{g['name'][3:]}: {g['findings'][0]}" for g in failed) or None
            dims.append(ReadinessDimension(name=name, score=score, status=status, blocking_issue=issue))
            if failed and required:
                blocking.append(f"{name}: {issue}")
        scored = [d.score for d in dims if d.score is not None]
        report = CtoGateReport(project_id=project_id, overall_score=round(sum(scored) / len(scored), 1) if scored else None,
                               decision="BLOCKED" if blocking else "APPROVED", blocking_issues=blocking, dimensions=dims)
        last = (self._overrides.get(project_id) or [None])[-1]
        if last and report.decision == "BLOCKED":
            report.decision = "APPROVED_BY_OVERRIDE"
            report.override = last
        return report

    def override(self, project_id: str, user_id: str, reason: str) -> CtoGateReport:
        """Record a person's decision to release despite the blocking issues. Nothing measured changes."""
        entry = {"by": user_id, "reason": reason.strip()[:500], "at": now_iso()}
        with self._lock:
            self._overrides.setdefault(project_id, []).append(entry)
        try:
            from backend.time_machine.recorder import emit
            emit(project_id, "approval_granted", "CTO Gate", f"readiness gate overridden by {user_id}: {entry['reason']}",
                 "info", data=entry)
        except Exception as e:  # noqa: BLE001 - the ledger is an observer
            _logger.warning("override not recorded in the Time Machine: %s", e)
        return self.evaluate(project_id)


global_cto_gate = AutonomousCtoGate()
