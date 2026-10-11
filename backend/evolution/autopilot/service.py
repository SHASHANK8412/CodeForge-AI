"""
AIForge Autopilot service: runs analyses and plan executions in background threads, one job per
project at a time, and keeps every state change in the store.
"""

import logging
import threading
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from backend.evolution.autopilot.analyzers import run_analyzers
from backend.evolution.autopilot.codebase import build_project_map
from backend.evolution.autopilot.findings import build_findings, merge_history, summarize
from backend.evolution.autopilot.models import (Analysis, Decision, Execution, Finding, FindingStatus, Plan,
                                                PlanStatus, now_iso)
from backend.evolution.autopilot.plans import PlanError, build_plan
from backend.evolution.autopilot.redact import redact

_logger = logging.getLogger("aiforge.autopilot")


class Busy(RuntimeError):
    pass


class AutopilotService:
    def __init__(self, store=None, background: bool = True):
        from backend.evolution.autopilot.store import global_autopilot_store
        self.store = store or global_autopilot_store
        self.background = background
        self._active: Dict[str, str] = {}               # project_id -> job id
        self._lock = threading.Lock()
        if background:
            try:
                closed = self.store.mark_interrupted()
                if closed:
                    _logger.warning("Autopilot: closed %d job(s) interrupted by a restart", closed)
            except Exception as e:  # noqa: BLE001 - recovery must not stop the server starting
                _logger.warning("Autopilot: could not check for interrupted jobs: %s", e)

    # --- jobs ------------------------------------------------------------------------------

    def _start(self, project_id: str, job_id: str, target: Callable[[], None]) -> None:
        with self._lock:
            if project_id in self._active:
                raise Busy(f"another Autopilot job ({self._active[project_id]}) is running for this project")
            self._active[project_id] = job_id

        def run():
            try:
                target()
            finally:
                with self._lock:
                    self._active.pop(project_id, None)
        if self.background:
            threading.Thread(target=run, name=f"autopilot-{job_id}", daemon=True).start()
        else:
            run()

    def active_job(self, project_id: str) -> Optional[str]:
        with self._lock:
            return self._active.get(project_id)

    # --- analysis ------------------------------------------------------------------------------

    def start_analysis(self, project_id: str, project_dir: Path, user_id: str, run_tests: bool = False) -> Analysis:
        analysis = Analysis(id="ana_" + uuid.uuid4().hex[:12], project_id=project_id, user_id=user_id,
                            started_at=now_iso())
        self.store.put(project_id, "analyses", analysis)
        self._start(project_id, analysis.id, lambda: self._analyze(analysis.id, project_id, Path(project_dir), run_tests))
        return self.store.get(project_id, "analyses", analysis.id)

    def _analyze(self, analysis_id: str, project_id: str, project: Path, run_tests: bool) -> None:
        self.store.update(project_id, "analyses", analysis_id, lambda a: setattr(a, "status", "running"))
        try:
            project_map = build_project_map(project)
            raws, tools, sources = run_analyzers(project, run_tests=run_tests)
            sources.entry_points = set(project_map["entry_points"])
            sources.route_files = {r["file"] for r in project_map["routes"]}
            current = build_findings(project_id, raws, sources)
            previous = {f.id: f for f in self.store.list(project_id, "findings")}
            merged = merge_history(previous, current)
            self.store.replace_findings(project_id, merged)
            current_ids = [f.id for f in current]

            def done(a: Analysis):
                a.status, a.finished_at = "completed", now_iso()
                a.project_map = _compact_map(project_map)
                a.tools = tools
                a.finding_ids = current_ids
                a.summary = {**summarize(merged[i] for i in current_ids), "total": len(current_ids),
                             "resolved_since_last": sum(1 for f in merged.values() if f.id not in current_ids
                                                        and previous.get(f.id) is not None
                                                        and previous[f.id].status in (FindingStatus.OPEN, FindingStatus.PLANNED, FindingStatus.FIX_FAILED)
                                                        and f.status == FindingStatus.RESOLVED)}
            self.store.update(project_id, "analyses", analysis_id, done)
        except Exception as e:  # noqa: BLE001 - recorded on the analysis
            _logger.exception("Autopilot analysis %s failed", analysis_id)
            message = redact(f"{type(e).__name__}: {e}", 1000)

            def failed(a: Analysis):
                a.status, a.finished_at, a.error = "failed", now_iso(), message
            self.store.update(project_id, "analyses", analysis_id, failed)

    # --- findings ----------------------------------------------------------------------------------

    def dismiss(self, project_id: str, finding_id: str, dismissed: bool = True) -> Optional[Finding]:
        def change(f: Finding):
            if dismissed:
                f.status = FindingStatus.DISMISSED
            elif f.status == FindingStatus.DISMISSED:
                f.status = FindingStatus.OPEN
        return self.store.update(project_id, "findings", finding_id, change)

    # --- plans ------------------------------------------------------------------------------------

    def create_plan(self, project_id: str, user_id: str, finding_ids: List[str], objective: str = "") -> Plan:
        stored = {f.id: f for f in self.store.list(project_id, "findings")}
        unknown = [i for i in finding_ids if i not in stored]
        if unknown:
            raise PlanError(f"unknown findings: {', '.join(unknown[:5])}")
        plan = build_plan(project_id, user_id, [stored[i] for i in dict.fromkeys(finding_ids)], objective)
        self.store.put(project_id, "plans", plan)
        self.store.set_finding_status(project_id, plan.finding_ids, FindingStatus.PLANNED.value)
        return plan

    def decide(self, project_id: str, plan_id: str, user_id: str, decision: str, note: str = "",
               extra_files: Optional[List[str]] = None) -> Plan:
        plan = self.store.get(project_id, "plans", plan_id)
        if plan is None:
            raise KeyError(plan_id)
        allowed = {
            "approved": {PlanStatus.AWAITING_APPROVAL, PlanStatus.DRAFT},
            "rejected": {PlanStatus.AWAITING_APPROVAL, PlanStatus.DRAFT, PlanStatus.APPROVED},
            "cancelled": {PlanStatus.AWAITING_APPROVAL, PlanStatus.DRAFT, PlanStatus.APPROVED},
        }
        if plan.status not in allowed[decision]:
            raise PlanError(f"a plan that is '{plan.status.value}' cannot be {decision}")
        if extra_files:
            from backend.generation.project_editor import _validate_paths
            bad = _validate_paths(Path("."), {p: "" for p in extra_files})
            bad.update({p: "absolute or parent path" for p in extra_files if p.startswith(("/", "\\")) or ".." in p.split("/")})
            if bad:
                raise PlanError("files cannot be added to the plan: " + ", ".join(f"{k} ({v})" for k, v in bad.items()))

        def change(p: Plan):
            p.status = {"approved": PlanStatus.APPROVED, "rejected": PlanStatus.REJECTED,
                        "cancelled": PlanStatus.CANCELLED}[decision]
            if extra_files and decision == "approved":
                p.expected_files = sorted(set(p.expected_files) | set(extra_files))
            p.decisions.append(Decision(decision="scope_approved" if extra_files and decision == "approved" else decision,
                                        user_id=user_id, note=note[:500] + (
                                            f" (added files: {', '.join(extra_files)})" if extra_files else "")))
        plan = self.store.update(project_id, "plans", plan_id, change)
        if decision in ("rejected", "cancelled"):
            self.store.set_finding_status(project_id, [i for i in plan.finding_ids
                                                       if (f := self.store.get(project_id, "findings", i))
                                                       and f.status == FindingStatus.PLANNED], FindingStatus.OPEN.value)
        return plan

    # --- executions ---------------------------------------------------------------------------------

    def execute(self, project_id: str, plan_id: str, user_id: str, project_dir: Path,
                generate: Optional[Callable[[str, str], str]] = None, include_tests: bool = True) -> Execution:
        from backend.evolution.autopilot.executor import STAGES, run_execution
        from backend.evolution.autopilot.models import Stage
        plan = self.store.get(project_id, "plans", plan_id)
        if plan is None:
            raise KeyError(plan_id)
        if plan.status != PlanStatus.APPROVED:
            raise PlanError(f"the plan must be approved before it runs (it is '{plan.status.value}')")
        execution = Execution(id="exe_" + uuid.uuid4().hex[:12], plan_id=plan_id, project_id=project_id,
                              user_id=user_id, stages=[Stage(name=n) for n in STAGES], started_at=now_iso())
        self.store.put(project_id, "executions", execution)
        self._start(project_id, execution.id, lambda: run_execution(self.store, execution.id, project_id,
                                                                   Path(project_dir), generate, include_tests))
        return self.store.get(project_id, "executions", execution.id)

    def cancel_execution(self, project_id: str, execution_id: str) -> Optional[Execution]:
        def change(e: Execution):
            if e.status in ("queued", "running"):
                e.cancel_requested = True
        return self.store.update(project_id, "executions", execution_id, change)

    def report(self, project_id: str, execution_id: str) -> Optional[Dict[str, Any]]:
        execution = self.store.get(project_id, "executions", execution_id)
        if execution is None:
            return None
        plan = self.store.get(project_id, "plans", execution.plan_id)
        findings = {f.id: f for f in self.store.list(project_id, "findings")}
        verdict = execution.verdict or {}
        executed = [c for c in execution.after if c.status in ("passed", "failed")]
        not_run = [c for c in execution.after if c.status not in ("passed", "failed")]
        return {
            "execution_id": execution.id, "plan_id": execution.plan_id, "status": execution.status,
            "objective": plan.objective if plan else "",
            "applied_to_project": execution.applied_to_project,
            "changed_files": execution.changed_files,
            "tasks": [r.model_dump() for r in execution.task_results],
            "checks": {
                "baseline": [c.model_dump(exclude={"output"}) for c in execution.baseline],
                "after": [c.model_dump(exclude={"output"}) for c in execution.after],
                "executed": [c.check_id for c in executed],
                "not_executed": [{"check": c.check_id, "status": c.status} for c in not_run],
            },
            "verdict": verdict,
            "verified_findings": [_brief(findings.get(i), i) for i in execution.verified_findings],
            "unresolved_findings": [_brief(findings.get(i), i) for i in execution.unresolved_findings],
            "error": execution.error,
            "started_at": execution.started_at, "finished_at": execution.finished_at,
            "statement": _statement(execution, verdict),
        }


def reanalyze_after_execution(store, project_id: str, project: Path, finding_ids: List[str],
                              tests_passed: bool = False) -> Tuple[List[str], List[str]]:
    """Analyze the project again (static analyzers) and mark each addressed finding verified or not."""
    project_map = build_project_map(project)
    raws, _, sources = run_analyzers(project, run_tests=False)
    sources.entry_points = set(project_map["entry_points"])
    sources.route_files = {r["file"] for r in project_map["routes"]}
    current = build_findings(project_id, raws, sources)
    detected = {f.id for f in current}
    previous = {f.id: f for f in store.list(project_id, "findings")}
    merged = merge_history(previous, current)
    verified, unresolved = [], []
    for fid in finding_ids:
        # A failing-test finding is decided by the after-change test run, not the static re-analysis.
        test_only = previous.get(fid) is not None and previous[fid].rule_id == "TESTS-FAILING"
        if (test_only and not tests_passed) or (not test_only and fid in detected):
            unresolved.append(fid)
            if fid in merged:
                merged[fid].status = FindingStatus.FIX_FAILED
        else:
            verified.append(fid)
            if fid in merged:
                merged[fid].status = FindingStatus.FIXED_VERIFIED
    store.replace_findings(project_id, merged)
    return verified, unresolved


def _brief(f: Optional[Finding], fid: str) -> Dict[str, Any]:
    if f is None:
        return {"id": fid}
    return {"id": f.id, "title": f.title, "file": f.file, "severity": f.severity.value, "status": f.status.value}


def _statement(e: Execution, verdict: Dict[str, Any]) -> str:
    if e.status == "completed":
        tests = next((c for c in e.after if c.check_id == "tests"), None)
        caveat = " The project's tests were failing before the change and still fail." \
            if tests is not None and tests.status == "failed" else ""
        return (f"Changes applied to {len(e.changed_files)} file(s). Evidence: {verdict.get('evidence', 'n/a')}. "
                f"{len(e.verified_findings)} finding(s) no longer detected; {len(e.unresolved_findings)} still detected."
                + caveat)
    if e.status == "rejected":
        return "Changes were made in the working copy but rejected by the checks; the project was not modified."
    if e.status == "needs_approval":
        return "The changes need files the plan did not list; nothing was applied. Approve the extra files to continue."
    if e.status == "cancelled":
        return "Cancelled; the project was not modified."
    if e.status in ("queued", "running"):
        return "In progress."
    return "Failed; the project was not modified." if not e.applied_to_project else "Failed after applying changes."


def _compact_map(m: Dict[str, Any]) -> Dict[str, Any]:
    """The stored project map leaves out per-file import lists (large and derivable)."""
    out = {k: v for k, v in m.items() if k not in ("python_imports", "js_imports", "files")}
    out["files_sample"] = m.get("files", [])[:300]
    return out


global_autopilot_service = AutopilotService()
