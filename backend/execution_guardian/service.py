"""
The Autonomous Execution Guardian.

  EXECUTE -> COLLECT -> CLASSIFY -> SELECT AGENT -> TARGETED FIX -> VALIDATE SCOPE -> APPLY -> RERUN FAILED
  CHECKS -> VERIFY THE REST -> CONTINUE OR STOP

API runs (source "api") work on an isolated working copy: the project is never written. When repairs made the
copy pass, the changed files become an Autopilot plan awaiting approval. The generation workflow (source
"workflow") calls verify() on its freshly generated workspace without repairing; its own debug -> patch loop
repairs, using the Guardian's classification and routing.

Bounds: max_repair_attempts (default 3), a per-check timeout, a time limit for the whole run; a failure whose
signature survives a repair unchanged is not attempted again (repeated failure), and the loop stops when nothing
repairable is left. A repair that makes things worse (new failures and nothing resolved, or fewer required
checks passing) is rolled back. The original failures and checks are kept next to the final ones.
"""

import copy
import logging
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from backend.evolution.autopilot.models import now_iso
from backend.evolution.autopilot.redact import redact
from backend.evolution.autopilot.store import AutopilotStore
from backend.execution_guardian import checks as chk
from backend.execution_guardian import classify as cls
from backend.execution_guardian import repair as rep
from backend.execution_guardian.models import Check, RepairAttempt, Verification

_logger = logging.getLogger("aiforge.execution_guardian")
DEFAULTS = {"max_repair_attempts": 3, "check_timeout_seconds": 600, "run_seconds": 3600}
BOUNDS = {"max_repair_attempts": (0, 5), "check_timeout_seconds": (60, 1800), "run_seconds": (120, 7200)}


class GuardianError(ValueError):
    pass


class Busy(RuntimeError):
    pass


class VerificationStore(AutopilotStore):
    KINDS = {"verifications": Verification}
    PRUNE = (("verifications", 50, "started_at"),)
    ENV_DIR = "AIFORGE_EXECUTION_GUARDIAN_DIR"
    DEFAULT_ROOT = Path(__file__).resolve().parents[1] / "data" / "execution_guardian"


def _known_files(root: Path) -> List[str]:
    return [p.relative_to(root).as_posix() for p in root.rglob("*")
            if p.is_file() and not chk._skip_dirs(p.relative_to(root).parts)][:5000]


class ExecutionGuardian:
    def __init__(self, store: Optional[VerificationStore] = None, background: bool = True,
                 generate: Optional[Callable[[str, str], str]] = None, classify_llm: Optional[Callable[[str, str], str]] = None,
                 autopilot=None):
        self.store = store or VerificationStore()
        self.background = background
        self.generate = generate               # None: the local coding model (tests inject fixed answers)
        self.classify_llm = classify_llm       # None: rule-only classification (+ labelled fallback)
        self.autopilot = autopilot
        self._active: Dict[str, str] = {}
        self._lock = threading.Lock()

    # --- lifecycle -------------------------------------------------------------------------------------------------

    @staticmethod
    def settings_of(raw: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        out = dict(DEFAULTS)
        for k, v in (raw or {}).items():
            if k not in BOUNDS:
                raise GuardianError(f"unknown setting {k}")
            lo, hi = BOUNDS[k]
            if not isinstance(v, (int, float)) or not lo <= v <= hi:
                raise GuardianError(f"setting {k} must be within {lo}-{hi}")
            out[k] = v
        return out

    def start(self, project_id: str, project: Path, user_id: str, settings: Optional[Dict[str, Any]] = None,
              requirements: str = "") -> Verification:
        project = Path(project).resolve()
        if not project.is_dir():
            raise GuardianError("the project folder does not exist")
        cfg = self.settings_of(settings)
        v = Verification(id="ver_" + uuid.uuid4().hex[:12], project_id=project_id, user_id=user_id, source="api",
                         settings={**cfg, "requirements": requirements[:4000]})
        with self._lock:
            if project_id in self._active:
                raise Busy(f"verification {self._active[project_id]} is already running for this project")
            self._active[project_id] = v.id
        self.store.put(project_id, "verifications", v)

        def go():
            try:
                self._run(project_id, v.id, project)
            finally:
                with self._lock:
                    self._active.pop(project_id, None)
        if self.background:
            threading.Thread(target=go, name=f"guardian-{v.id}", daemon=True).start()
        else:
            go()
        return self.get(project_id, v.id)

    def cancel(self, project_id: str, vid: str) -> Verification:
        return self.store.update(project_id, "verifications", vid, lambda x: setattr(x, "cancel_requested", True))

    def get(self, project_id: str, vid: str) -> Verification:
        v = self.store.get(project_id, "verifications", vid)
        if v is None:
            raise KeyError(vid)
        return v

    def active(self, project_id: str) -> Optional[str]:
        with self._lock:
            return self._active.get(project_id)

    # --- helpers ------------------------------------------------------------------------------------------------------

    def _save(self, project_id: str, vid: str, **fields) -> None:
        def change(x: Verification):
            for k, val in fields.items():
                setattr(x, k, val)
        self.store.update(project_id, "verifications", vid, change)

    def _activity(self, project_id: str, vid: str, actor: str, text: str) -> None:
        def add(x: Verification):
            x.current_operation = text[:200]
            x.activity.append({"at": now_iso(), "actor": actor, "text": redact(text, 600)})
            x.activity = x.activity[-200:]
        self.store.update(project_id, "verifications", vid, add)

    def _tm(self, project_id: str, vid: str, type_: str, summary: str, outcome: str, data: Optional[Dict[str, Any]] = None) -> None:
        try:
            from backend.time_machine.recorder import emit
            emit(project_id, type_, "Execution Guardian", summary, outcome, task_id=vid, refs={"verification_id": vid},
                 data=data or {})
        except Exception as e:  # noqa: BLE001 - the ledger is an observer, never a reason to fail a verification
            _logger.warning("time machine event not recorded: %s", e)

    # --- the loop -----------------------------------------------------------------------------------------------------

    def _run(self, project_id: str, vid: str, project: Path) -> None:
        from backend.evolution.autopilot.workspace import create_workspace, discard_workspace
        v = self.get(project_id, vid)
        cfg = v.settings
        deadline = time.monotonic() + float(cfg["run_seconds"])

        def stop() -> bool:
            x = self.store.get(project_id, "verifications", vid)
            return bool(x and x.cancel_requested) or time.monotonic() > deadline
        ws = None
        try:
            self._activity(project_id, vid, "Execution Guardian", "copying the project into an isolated working copy")
            ws = create_workspace(project, prefix="aiforge_guardian_")
            stack = chk.detect(ws)
            checks = chk.select(stack)
            self._save(project_id, vid, stack=stack, checks=checks)
            self._activity(project_id, vid, "Execution Guardian",
                           f"detected {', '.join(stack['languages']) or 'no supported language'}"
                           + (f" ({', '.join(stack['frameworks'])})" if stack['frameworks'] else "")
                           + f"; {sum(1 for c in checks if c.status != 'SKIPPED')} check(s) selected")
            checks = self._execute(project_id, vid, checks, ws, stack, cfg, stop)
            failures = cls.classify(checks, _known_files(ws), 0, self.classify_llm)
            self._save(project_id, vid, checks=checks, original_checks=copy.deepcopy(checks), failures=failures,
                       original_failures=copy.deepcopy(failures))
            self._repair_loop(project_id, vid, ws, stack, cfg, stop)
            v = self.get(project_id, vid)
            status, warnings = chk.final_status(v.checks)
            if v.cancel_requested:
                status = "CANCELLED"
            changed = sorted({f for r in v.repairs if not r.rolled_back for f in r.files_changed})
            self._save(project_id, vid, status=status, finished_at=now_iso(), current_operation="finished")
            self._report(project_id, vid, warnings)
            if changed and status in ("VERIFIED", "VERIFIED_WITH_WARNINGS"):
                self._deliver(project_id, vid, ws, changed)
            self._tm(project_id, vid, "test_executed", f"verification {status}",
                     "success" if status.startswith("VERIFIED") else "failure",
                     {"checks": {c.name: c.status for c in self.get(project_id, vid).checks}})
        except Exception as e:  # noqa: BLE001 - recorded on the verification, never hidden
            _logger.exception("verification %s failed", vid)
            self._save(project_id, vid, status="BLOCKED", error=redact(f"{type(e).__name__}: {e}", 800), finished_at=now_iso(),
                       current_operation="stopped by an internal error")
            self._report(project_id, vid, [])
        finally:
            if ws is not None:
                discard_workspace(ws)

    def _execute(self, project_id, vid, checks: List[Check], ws: Path, stack, cfg, stop, only: Optional[List[str]] = None) -> List[Check]:
        def progress(op):
            self._activity(project_id, vid, "Execution Guardian", op)
        # checks that do not apply stay SKIPPED; everything about to run starts again from PENDING
        never = {"api_contract"} | ({"python_tests"} if not stack["python_tests"] else set())
        for c in checks:
            if (only is None and c.status != "SKIPPED" or only is not None and c.name in only) and c.name not in never:
                c.status, c.reason, c.log_excerpt, c.error_summary, c.timed_out = "PENDING", "", "", "", False
        self._save(project_id, vid, checks=checks)
        return chk.run_all(checks, ws, stack, cfg, stop, only=only, on_progress=progress)

    def _repair_loop(self, project_id: str, vid: str, ws: Path, stack: Dict[str, Any], cfg: Dict[str, Any], stop) -> None:
        from backend.evolution.autopilot.executor import apply_all
        exhausted: set = set()
        for attempt in range(1, int(cfg["max_repair_attempts"]) + 1):
            v = self.get(project_id, vid)
            status, _ = chk.final_status(v.checks)
            if status != "FAILED" or stop():
                return
            group = rep.pick_group(v.failures, exhausted)
            if not group:
                self._activity(project_id, vid, "Execution Guardian", "no repairable failure left (infrastructure, "
                               "repeated, or no agent can repair it): stopping")
                return
            agent = group[0].responsible_agent
            before = {c.name: c.status for c in v.checks}
            before_checks, before_failures = copy.deepcopy(v.checks), copy.deepcopy(v.failures)
            before_sigs = {f.signature for f in v.failures}
            self._activity(project_id, vid, f"{agent} agent", f"repair attempt {attempt}: {len(group)} {group[0].category} failure(s)")
            ra = RepairAttempt(attempt=attempt, failure_ids=[f.id for f in group], agent=agent, strategy="", before=before)
            try:
                strategy, changes, note = rep.propose(group, agent, ws, stack, project_id, self.generate,
                                                      v.settings.get("requirements", ""))
            except Exception as e:  # noqa: BLE001 - a failed proposal is a recorded, unproductive attempt
                strategy, changes, note = f"model:{agent}", {}, redact(f"{type(e).__name__}: {e}", 300)
            ra.strategy = strategy or "none"
            accepted, rejected = rep.validate(changes, agent, stack, ws, sorted({x for f in group for x in f.files}))
            ra.rejected_paths = rejected
            if not accepted:
                ra.outcome, ra.note, ra.finished_at = ("rejected" if rejected else "no_fix"), note or (
                    "every proposed change was outside the allowed scope" if rejected else "no change was proposed"), now_iso()
                exhausted |= {f.signature for f in group}
                self._add_repair(project_id, vid, ra)
                continue
            backup = {p: ((ws / p).read_text(encoding="utf-8", errors="replace") if (ws / p).is_file() else None) for p in accepted}
            written, ok = apply_all(ws, accepted, f"Execution Guardian repair {attempt} ({agent})")
            if not ok:
                ra.outcome, ra.note, ra.finished_at = "rejected", "the patch engine rejected the change (rolled back)", now_iso()
                exhausted |= {f.signature for f in group}
                self._add_repair(project_id, vid, ra)
                continue
            ra.files_changed = sorted(accepted)
            # rerun the checks that failed or could not run, then - if they pass - every other check
            rerun = [c.name for c in v.checks if c.status in ("FAILED", "BLOCKED") and c.name != "api_contract"]
            checks = self._execute(project_id, vid, v.checks, ws, stack, cfg, stop, only=rerun)
            if not any(c.status in ("FAILED", "BLOCKED") for c in checks if c.name in rerun and c.required):
                others = [c.name for c in checks if c.name not in rerun and c.status not in ("SKIPPED",)]
                if others:
                    self._activity(project_id, vid, "Execution Guardian", "re-verifying the related checks")
                    checks = self._execute(project_id, vid, checks, ws, stack, cfg, stop, only=others)
            failures = cls.classify(checks, _known_files(ws), attempt, self.classify_llm)
            after_sigs = {f.signature for f in failures}
            ra.after = {c.name: c.status for c in checks}
            ra.resolved = sorted(before_sigs - after_sigs)
            ra.new_failures = [f"{f.category}: {f.summary}" for f in failures if f.signature not in before_sigs]
            passed_before = sum(1 for s_ in before.values() if s_ == "PASSED")
            passed_after = sum(1 for c in checks if c.status == "PASSED")
            group_sigs = {f.signature for f in group}
            if (ra.new_failures and not ra.resolved) or passed_after < passed_before:
                apply_all(ws, backup, f"Execution Guardian rollback of repair {attempt}")
                ra.rolled_back, ra.outcome = True, "regressed"
                ra.note = "the repair introduced new failures or fewer checks passed: rolled back"
                self._save(project_id, vid, checks=before_checks, failures=before_failures)
                exhausted |= group_sigs
            else:
                ra.outcome = ("resolved" if not (group_sigs & after_sigs) and not ra.new_failures
                              else "improved" if ra.resolved else "no_change")
                exhausted |= group_sigs & after_sigs      # a failure that survived its repair is not attempted again
                self._save(project_id, vid, checks=checks, failures=failures)
            ra.finished_at = now_iso()
            self._add_repair(project_id, vid, ra)

    def _add_repair(self, project_id: str, vid: str, ra: RepairAttempt) -> None:
        self.store.update(project_id, "verifications", vid, lambda x: x.repairs.append(ra))
        self._activity(project_id, vid, f"{ra.agent} agent", f"repair {ra.attempt}: {ra.outcome}"
                       + (f" ({', '.join(ra.files_changed)})" if ra.files_changed else "") + (f" - {ra.note}" if ra.note else ""))

    # --- workflow use (no repairs: the graph's debug -> patch loop repairs) -------------------------------------------

    def verify(self, project_id: str, project: Path, user_id: str = "workflow", attempt: int = 0,
               settings: Optional[Dict[str, Any]] = None) -> Verification:
        """Run every applicable check against a copy of `project` and record the result (source 'workflow')."""
        from backend.evolution.autopilot.workspace import create_workspace, discard_workspace
        cfg = self.settings_of(settings)
        v = Verification(id="ver_" + uuid.uuid4().hex[:12], project_id=project_id, user_id=user_id, source="workflow",
                         settings={**cfg, "workflow_attempt": attempt})
        self.store.put(project_id, "verifications", v)
        ws = create_workspace(Path(project), prefix="aiforge_guardian_")
        try:
            stack = chk.detect(ws)
            checks = chk.select(stack)
            checks = self._execute(project_id, v.id, checks, ws, stack, cfg, lambda: False)
            failures = cls.classify(checks, _known_files(ws), attempt, self.classify_llm)
            status, warnings = chk.final_status(checks)
            self._save(project_id, v.id, stack=stack, checks=checks, original_checks=copy.deepcopy(checks), failures=failures,
                       original_failures=copy.deepcopy(failures), status=status, finished_at=now_iso(), current_operation="finished")
            self._report(project_id, v.id, warnings)
        except Exception as e:  # noqa: BLE001
            _logger.exception("workflow verification failed")
            self._save(project_id, v.id, status="BLOCKED", error=redact(f"{type(e).__name__}: {e}", 800), finished_at=now_iso())
            self._report(project_id, v.id, [])
        finally:
            discard_workspace(ws)
        return self.get(project_id, v.id)

    # --- report and delivery -------------------------------------------------------------------------------------------

    def _report(self, project_id: str, vid: str, warnings: List[str]) -> None:
        v = self.get(project_id, vid)
        by = {c.name: c for c in v.checks}
        counts = {s: sum(1 for c in v.checks if c.status == s) for s in ("PASSED", "FAILED", "SKIPPED", "BLOCKED")}
        tests = {n: by[n].counts for n in ("python_tests", "frontend_tests") if n in by and by[n].counts}
        tested, not_tested = [], []
        for c in v.checks:
            (tested if c.status in ("PASSED", "FAILED") else not_tested).append(
                f"{c.label}: {c.status}" + (f" - {c.reason}" if c.reason and c.status not in ("PASSED", "FAILED") else ""))
        original = {f.signature: f for f in v.original_failures}
        current = {f.signature for f in v.failures}
        stack = v.stack or {}
        run = []
        if stack.get("requirements"):
            run.append(f"pip install -r {stack['requirements']}")
        if stack.get("fastapi_app"):
            wd, mod = stack["fastapi_app"].split("/", 1)
            run.append(("" if wd == "." else f"cd {wd} && ") + f"uvicorn {mod} --reload")
        if stack.get("python_tests"):
            run.append("pytest")
        if stack.get("frontend") is not None:
            prefix = "" if stack["frontend"] == "." else f"cd {stack['frontend']} && "
            run += [f"{prefix}npm install", f"{prefix}npm run dev"]
        statement = {
            "VERIFIED": "every required check ran and passed",
            "VERIFIED_WITH_WARNINGS": "every required check that applies ran and passed; see the warnings for what was not run",
            "FAILED": "at least one required check failed",
            "BLOCKED": "at least one required check could not run, so the project is not verified",
            "CANCELLED": "the verification was cancelled", "RUNNING": "still running"}.get(v.status, v.status)
        rep_ = {
            "project_id": v.project_id, "verification_id": v.id, "source": v.source, "status": v.status, "statement": statement,
            "verified": v.status in ("VERIFIED", "VERIFIED_WITH_WARNINGS"),
            "technology_stack": stack, "started_at": v.started_at, "finished_at": v.finished_at,
            "checks": [{"name": c.name, "label": c.label, "required": c.required, "status": c.status,
                        "duration_seconds": c.duration_seconds, "environment": c.environment, "error_summary": c.error_summary,
                        "reason": c.reason, "counts": c.counts, "provenance": c.provenance} for c in v.checks],
            "counts": counts, "test_summaries": tests,
            "runtime_startup": ({"status": by["backend_startup"].status, "detail": by["backend_startup"].reason or by["backend_startup"].error_summary}
                                if "backend_startup" in by else {"status": "not applicable", "detail": "no FastAPI app was found"}),
            "repair_attempts": len(v.repairs),
            "failures_discovered": [{"category": f.category, "summary": f.summary, "check": f.check} for f in v.original_failures],
            "failures_resolved": [{"category": f.category, "summary": f.summary} for s, f in original.items() if s not in current],
            "remaining_failures": [{"category": f.category, "summary": f.summary, "responsible_agent": f.responsible_agent,
                                    "next_action": f.next_action} for f in v.failures],
            "warnings": warnings, "what_was_tested": tested, "what_was_not_tested": not_tested,
            "how_to_run": run, "error": v.error,
            "limitations": ["checks run the project's own tests and startup; behaviour the tests do not cover is not verified",
                            "frontend-to-backend calls are not exercised without an API contract (see Swarm missions)"],
        }
        self._save(project_id, vid, report=rep_)

    def _autopilot_service(self):
        if self.autopilot is not None:
            return self.autopilot
        from backend.evolution.autopilot.service import global_autopilot_service
        return global_autopilot_service

    def _deliver(self, project_id: str, vid: str, ws: Path, changed: List[str]) -> None:
        """Repaired files as an Autopilot plan awaiting approval; the project itself is never written here."""
        from backend.evolution.autopilot.models import Plan, PlanTask
        from backend.evolution.autopilot.plans import STRATEGY_AGENT
        v = self.get(project_id, vid)
        contents = {p: (ws / p).read_text(encoding="utf-8") for p in changed if (ws / p).is_file()}
        plan = Plan(id="pln_" + uuid.uuid4().hex[:12], project_id=project_id, user_id=v.user_id,
                    objective=f"Execution Guardian repairs ({v.status})", finding_ids=[],
                    tasks=[PlanTask(id="t1", title="apply the verified repairs", finding_ids=[], files=sorted(contents),
                                    strategy="write_files", agent=STRATEGY_AGENT["write_files"],
                                    modification=f"files repaired and verified by {vid}", contents=contents)],
                    expected_files=sorted(contents), agents=sorted({r.agent for r in v.repairs}),
                    checks=["python_syntax", "quality_gate", "security_static", "tests"],
                    risks=["agent-generated repairs: review the diff before approving"],
                    assumptions=[f"verified in an isolated working copy by {vid}"],
                    approval_required=["apply the repaired files"],
                    completion_criteria=["the project's checks pass with the files applied"], origin="execution_guardian", origin_ref=vid)
        try:
            self._autopilot_service().store.put(project_id, "plans", plan)
            self._save(project_id, vid, delivery={"autopilot_plan_id": plan.id, "files": sorted(contents),
                                                  "status": "awaiting approval in Autopilot", "project_modified": False})
        except Exception as e:  # noqa: BLE001
            self._save(project_id, vid, delivery={"error": f"the Autopilot plan could not be created: {type(e).__name__}",
                                                  "project_modified": False})


global_execution_guardian = ExecutionGuardian()
