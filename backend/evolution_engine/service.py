"""
AIForge Evolution Engine: evidence-driven experiments with several candidate implementations.

  discover   opportunities from existing evidence (discovery.py)
  plan       hypothesis, strategies (ordered by Engineering Memory), metrics, thresholds, limits (planner.py)
  run        (approved) one frozen snapshot of the project -> one workspace per candidate; the coding model
             writes each candidate (secret lines hidden); every candidate gets the same checks:
               correctness  Autopilot checks incl. the project's tests in the Docker sandbox (a failing
                            test is re-run once: passing on the re-run marks it flaky, not a defect)
               security     Security Guardian static analysis of the candidate vs the snapshot
               performance  one Performance Engineer run measuring the snapshot and every candidate side
                            by side with alternating repetitions; the noise-aware perf gate per candidate
               maintainability  changed lines and branch count of the changed files
             -> deterministic selection (selection.py) -> outcome; Engineering Memory records (memory.py)
  approve    a person approves the selected candidate; the approval is bound to the project's source
             revision and the candidate's patch hash
  promote    refused if either changed (stale approval); otherwise an Autopilot plan writes exactly the
             approved files: isolated copy, checks, the Evolution gate (the same measurement on the project
             and the changed copy), apply through the patch engine; then the project's tests run on the
             promoted project and the change is rolled back (exact previous contents) if they do not pass.

The original project is never modified before promotion. Nothing here trains or changes a model.
"""

import ast
import difflib
import hashlib
import logging
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from backend.evolution.autopilot.models import Plan, PlanTask, now_iso
from backend.evolution.autopilot.redact import redact
from backend.evolution.autopilot.store import AutopilotStore
from backend.evolution.autopilot.workspace import COPY_SKIP
from backend.evolution_engine import discovery, memory, planner, selection
from backend.evolution_engine.models import (Approval, Candidate, Experiment, MemoryRecord, Opportunity, Promotion,
                                             Weights)
from backend.performance.engineer.models import Thresholds, Workload

_logger = logging.getLogger("aiforge.evolution_engine")
MODEL_ATTEMPTS = 2
FINAL_STATES = ("evaluated", "rejected", "completed", "failed", "cancelled")
SYSTEM_PROMPT = ("You are AIForge's performance engineer. Return the complete new content of each file you change, "
                 "as '### path' followed by a fenced code block. Change only what the strategy requires.")


class EvolutionError(ValueError):
    pass


class Busy(RuntimeError):
    pass


class EvolutionStore(AutopilotStore):
    KINDS = {"opportunities": Opportunity, "experiments": Experiment, "memory": MemoryRecord}
    PRUNE = (("experiments", 50, "created_at"), ("opportunities", 200, "discovered_at"))
    ENV_DIR = "AIFORGE_EVOLUTION_ENGINE_DIR"
    DEFAULT_ROOT = Path(__file__).resolve().parents[1] / "data" / "evolution_engine"

    def close_interrupted(self) -> int:
        """After a restart, experiments that were running can never finish: they are closed as failed."""
        closed = 0
        if not self.root.is_dir():
            return 0
        for path in self.root.glob("*.json"):
            pid = path.stem
            try:
                items = self.list(pid, "experiments")
            except ValueError:
                continue
            for e in items:
                if e.status in ("queued", "running", "promoting"):
                    def close(x: Experiment):
                        x.error = "interrupted: the server stopped while this was running" + (
                            " (during promotion; check the Autopilot execution)" if x.status == "promoting" else "")
                        x.status, x.finished_at = "failed", now_iso()
                        x.outcome = x.outcome or "inconclusive"
                    self.update(pid, "experiments", e.id, close)
                    closed += 1
        return closed


def source_revision(root: Path) -> str:
    """Content hash of the project's sources (the files a working copy contains)."""
    root = Path(root).resolve()
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        if COPY_SKIP & set(rel.parts) or p.is_symlink() or not p.is_file():
            continue
        h.update(rel.as_posix().encode() + b"\0" + hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()


def patch_hash(changes: Dict[str, str]) -> str:
    h = hashlib.sha256()
    for rel in sorted(changes):
        h.update(rel.encode() + b"\0" + changes[rel].encode() + b"\0")
    return h.hexdigest()


def _branches(source: str) -> int:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return 0
    kinds = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.BoolOp, ast.IfExp, ast.comprehension)
    return sum(isinstance(n, kinds) for n in ast.walk(tree))


def _safe_write(root: Path, rel: str, content: str) -> None:
    target = (root / rel).resolve()
    if root.resolve() not in target.parents:
        raise EvolutionError(f"path outside the workspace: {rel}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8", newline="")


class EvolutionEngine:
    def __init__(self, store: Optional[EvolutionStore] = None, autopilot=None, background: bool = True,
                 generate: Optional[Callable[[str, str], str]] = None):
        self.store = store or EvolutionStore()
        self._autopilot = autopilot
        self.background = background
        self.generate = generate            # None: the local coding model; tests inject a fixed generator
        self._active: Dict[str, str] = {}
        self._lock = threading.Lock()
        if background:
            try:
                self.store.close_interrupted()
            except Exception as e:  # noqa: BLE001
                _logger.warning("Evolution Engine: could not close interrupted experiments: %s", e)

    @property
    def autopilot(self):
        if self._autopilot is None:
            from backend.evolution.autopilot.service import global_autopilot_service
            self._autopilot = global_autopilot_service
        return self._autopilot

    # --- jobs ----------------------------------------------------------------------------------------------

    def _start(self, project_id: str, job_id: str, target: Callable[[], None]) -> None:
        with self._lock:
            if project_id in self._active:
                raise Busy(f"another Evolution Engine job ({self._active[project_id]}) is running for this project")
            self._active[project_id] = job_id

        def run():
            try:
                target()
            finally:
                with self._lock:
                    self._active.pop(project_id, None)
        if self.background:
            threading.Thread(target=run, name=f"evolution-{job_id}", daemon=True).start()
        else:
            run()

    def active_job(self, project_id: str) -> Optional[str]:
        with self._lock:
            return self._active.get(project_id)

    def _audit(self, project_id: str, eid: str, action: str, **details) -> None:
        def add(e: Experiment):
            e.audit.append({"at": now_iso(), "action": action, **{k: redact(str(v), 400) for k, v in details.items()}})
            e.current = action
        self.store.update(project_id, "experiments", eid, add)

    def _cancelled(self, project_id: str, eid: str, deadline: float) -> bool:
        e = self.store.get(project_id, "experiments", eid)
        return bool(e and e.cancel_requested) or time.monotonic() > deadline

    # --- discovery and planning ---------------------------------------------------------------------------------

    def discover(self, project_id: str, project: Path, criteria: Optional[Dict[str, float]] = None) -> List[Opportunity]:
        ops = discovery.discover(project_id, project, criteria)
        for op in ops:
            self.store.put(project_id, "opportunities", op)
        return ops

    def create_experiment(self, project_id: str, project: Path, user_id: str, opportunity_id: str, max_candidates: int = 2,
                          weights: Optional[Weights] = None, thresholds: Optional[Thresholds] = None,
                          overrides: Optional[Dict[str, str]] = None, workload: Optional[Workload] = None) -> Experiment:
        op = self.store.get(project_id, "opportunities", opportunity_id)
        if op is None:
            raise KeyError(opportunity_id)
        plan = planner.plan_experiment(op, project, max_candidates, weights, thresholds, overrides, workload)
        exp = Experiment(id="evx_" + uuid.uuid4().hex[:12], project_id=project_id, user_id=user_id, opportunity=op, plan=plan,
                         status="rejected" if plan.rejected_reasons else "planned",
                         outcome="failed" if plan.rejected_reasons else None, outcome_reasons=plan.rejected_reasons)
        exp.audit.append({"at": now_iso(), "action": "planned" if not plan.rejected_reasons else "plan rejected",
                          "user": user_id, "strategies": [s.id for s in plan.strategies]})
        self.store.put(project_id, "experiments", exp)
        return exp

    # --- run ---------------------------------------------------------------------------------------------------

    def run(self, project_id: str, project: Path, user_id: str, experiment_id: str, approved: bool) -> Experiment:
        exp = self.store.get(project_id, "experiments", experiment_id)
        if exp is None:
            raise KeyError(experiment_id)
        if exp.status != "planned":
            raise EvolutionError(f"the experiment is '{exp.status}'; only a planned experiment can run")
        if not approved:
            raise EvolutionError("running candidates executes generated code in the sandbox: approve it explicitly")
        self.store.update(project_id, "experiments", experiment_id, lambda e: (
            setattr(e, "status", "queued"),
            e.audit.append({"at": now_iso(), "action": "run approved", "user": user_id})))
        try:
            self._start(project_id, experiment_id, lambda: self._run(project_id, experiment_id, Path(project)))
        except Busy:
            self.store.update(project_id, "experiments", experiment_id, lambda e: setattr(e, "status", "planned"))
            raise
        return self.store.get(project_id, "experiments", experiment_id)

    def abort(self, project_id: str, experiment_id: str) -> Optional[Experiment]:
        def change(e: Experiment):
            if e.status in ("queued", "running"):
                e.cancel_requested = True
                e.audit.append({"at": now_iso(), "action": "abort requested"})
        return self.store.update(project_id, "experiments", experiment_id, change)

    def _run(self, project_id: str, eid: str, project: Path) -> None:
        from backend.evolution.autopilot import validation
        from backend.evolution.autopilot.workspace import create_workspace, discard_workspace
        exp = self.store.get(project_id, "experiments", eid)
        deadline = time.monotonic() + exp.plan.max_seconds
        started = time.monotonic()
        workspaces: List[Path] = []
        stop = lambda: self._cancelled(project_id, eid, deadline)  # noqa: E731

        def save(change):
            self.store.update(project_id, "experiments", eid, change)

        def check():
            if stop():
                raise InterruptedError("cancelled (by the user or the experiment's time limit)")
        save(lambda e: (setattr(e, "status", "running"), setattr(e, "started_at", now_iso())))
        try:
            self._audit(project_id, eid, "freezing a snapshot of the project")
            snapshot = create_workspace(project, prefix="aiforge_evolve_src_")
            workspaces.append(snapshot)
            revision = source_revision(snapshot)
            save(lambda e: setattr(e, "source_revision", revision))
            check()
            self._audit(project_id, eid, "baseline checks (tests in the Docker sandbox)")
            baseline = validation.run_checks(snapshot, include_tests=True)
            base_sec = self._security_findings(project_id, snapshot)
            save(lambda e: (setattr(e, "baseline_checks", baseline),
                            setattr(e, "baseline_security", {"critical_high": sorted(base_sec["serious"]),
                                                             "total": len(base_sec["all"])})))
            tests_base = next((c for c in baseline if c.check_id == "tests"), None)
            if tests_base is None or tests_base.status not in ("passed", "failed"):
                raise RuntimeError("the project's tests could not run on the baseline "
                                   f"({tests_base.status if tests_base else 'missing'}): correctness cannot be judged")
            # candidates, each in its own copy of the snapshot
            candidates: List[Candidate] = []
            ws_of: Dict[str, Path] = {}
            seen: Dict[str, str] = {}
            for i, strategy in enumerate(exp.plan.strategies, start=1):
                check()
                cand = Candidate(id=f"c{i}", strategy=strategy.id, status="generating")
                self._audit(project_id, eid, f"generating candidate c{i} ({strategy.id})")
                ws = create_workspace(snapshot, prefix=f"aiforge_evolve_c{i}_")
                workspaces.append(ws)
                t0 = time.monotonic()
                self._generate(project_id, exp, strategy, ws, cand)
                cand.durations["generate_s"] = round(time.monotonic() - t0, 2)
                if cand.patch_hash and cand.patch_hash in seen:
                    cand.status, cand.duplicate_of = "duplicate", seen[cand.patch_hash]
                    cand.generation_error = f"identical to {seen[cand.patch_hash]}"
                elif cand.patch_hash:
                    seen[cand.patch_hash] = cand.id
                ws_of[cand.id] = ws
                candidates.append(cand)
                save(lambda e, c=cand: e.candidates.append(Candidate(**c.model_dump())))
            # correctness, security, maintainability per candidate
            for cand in candidates:
                if cand.status != "generating":
                    continue
                check()
                cand.status = "evaluating"
                self._audit(project_id, eid, f"testing candidate {cand.id} in the Docker sandbox")
                t0 = time.monotonic()
                self._evaluate_static(project_id, exp, cand, ws_of[cand.id], baseline, base_sec, snapshot)
                cand.durations["checks_s"] = round(time.monotonic() - t0, 2)
                self._save_candidate(project_id, eid, cand)
            # performance: one side-by-side run for the snapshot and every candidate that is still in
            to_measure = [c for c in candidates if c.status == "evaluating" and c.correctness.get("accepted")
                          and not c.security.get("new_serious")]
            for c in candidates:
                if c.status == "evaluating" and c not in to_measure:
                    c.performance = {"decision": "not_measured", "reasons": ["not measured: it failed a mandatory check first"],
                                     "infrastructure": False}
            if to_measure:
                check()
                self._audit(project_id, eid, f"measuring the baseline and {len(to_measure)} candidate(s) side by side")
                self._measure(project_id, eid, exp, snapshot, to_measure, ws_of, stop)
            for c in candidates:
                if c.status == "evaluating":
                    c.status = "evaluated"
                self._save_candidate(project_id, eid, c)
            exp = self.store.get(project_id, "experiments", eid)
            selected, outcome, reasons = selection.select(exp)
            exp.selected, exp.outcome, exp.outcome_reasons = selected, outcome, reasons
            exp.selection = {"method": "mandatory constraints first, then weighted ranking (selection.py)",
                             "weights": exp.plan.weights.model_dump(),
                             "ranking": [{"candidate": c.id, "strategy": c.strategy, "eligible": c.eligible, "score": c.score}
                                         for c in sorted(exp.candidates, key=lambda c: -(c.score or -1))]}
            exp.status, exp.finished_at = "evaluated", now_iso()
            exp.duration_seconds = round(time.monotonic() - started, 1)
            exp.audit.append({"at": now_iso(), "action": f"evaluated: {outcome}", "selected": selected or "-"})
            self.store.put(project_id, "experiments", exp)
            memory.record_experiment(exp, self.store)
        except InterruptedError as e:
            why = str(e)
            save(lambda x: (setattr(x, "status", "cancelled"), setattr(x, "outcome", "inconclusive"),
                            setattr(x, "outcome_reasons", [why]), setattr(x, "finished_at", now_iso())))
        except Exception as e:  # noqa: BLE001 - recorded on the experiment
            _logger.exception("Evolution experiment %s failed", eid)
            msg = redact(f"{type(e).__name__}: {e}", 800)
            save(lambda x: (setattr(x, "status", "failed"), setattr(x, "outcome", "inconclusive"),
                            setattr(x, "error", msg), setattr(x, "outcome_reasons", [msg]), setattr(x, "finished_at", now_iso())))
        finally:
            for ws in workspaces:
                discard_workspace(ws)
            self._audit(project_id, eid, f"cleaned up {len(workspaces)} workspace(s)")

    def _save_candidate(self, project_id: str, eid: str, cand: Candidate) -> None:
        data = Candidate(**cand.model_dump())

        def change(e: Experiment):
            e.candidates = [data if c.id == cand.id else c for c in e.candidates]
        self.store.update(project_id, "experiments", eid, change)

    # --- candidate generation ---------------------------------------------------------------------------------

    def _generate(self, project_id: str, exp: Experiment, strategy, ws: Path, cand: Candidate) -> None:
        import os
        from backend.evolution.autopilot.executor import HiddenLineChanged, model_changes
        op = exp.opportunity
        request = (f"Performance problem: {op.title}\nEvidence: " + "; ".join(e["detail"] for e in op.evidence)[:800] +
                   f"\nEndpoint to speed up: {op.endpoint}\nStrategy ({strategy.id}): {strategy.instructions}")
        cand.model = {"source": "injected generator (tests)" if self.generate else "local coding model (Ollama)",
                      "model": None if self.generate else (os.environ.get("AIFORGE_CODING_MODEL") or "model router default"),
                      "system_prompt_sha": hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest()[:12],
                      "request_sha": hashlib.sha256(request.encode()).hexdigest()[:12], "attempts": 0,
                      "note": "configuration only; the model's own explanation is not evidence"}
        feedback = ""
        for attempt in range(1, MODEL_ATTEMPTS + 1):
            cand.model["attempts"] = attempt
            try:
                changes = model_changes(ws, project_id, exp.plan.allowed_files, [], request, self.generate, feedback,
                                        topic=op.title, system_prompt=SYSTEM_PROMPT)
            except HiddenLineChanged as e:
                feedback = str(e)
                continue
            except Exception as e:  # noqa: BLE001 - recorded on the candidate
                cand.status, cand.generation_error = "failed", redact(f"{type(e).__name__}: {e}", 400)
                return
            outside = [p for p in changes if p not in exp.plan.allowed_files]
            if outside:
                feedback = "you changed files outside the allowed list: " + ", ".join(outside)
                continue
            changes = {p: c for p, c in changes.items() if c is not None}
            if not changes:
                feedback = "no change was proposed"
                continue
            before = {p: (ws / p).read_text(encoding="utf-8") for p in changes if (ws / p).is_file()}
            for p, c in changes.items():
                _safe_write(ws, p, c)
            cand.changes = changes
            cand.patch_hash = patch_hash(changes)
            cand.diff = redact("".join("".join(difflib.unified_diff((before.get(p) or "").splitlines(True), c.splitlines(True),
                                                                    f"a/{p}", f"b/{p}")) for p, c in changes.items()), 20000)
            cand.maintainability = {
                "changed_lines": sum(1 for line in cand.diff.splitlines() if line[:1] in "+-" and line[:3] not in ("+++", "---")),
                "branches_delta": sum(_branches(c) - _branches(before.get(p, "")) for p, c in changes.items()),
                "method": "changed lines in the diff and the change in branch count (if/for/while/try/boolean/comprehension)"}
            return
        cand.status, cand.generation_error = "failed", f"no usable change after {MODEL_ATTEMPTS} attempts: {feedback}"

    # --- evaluation ---------------------------------------------------------------------------------------------------

    def _security_findings(self, project_id: str, root: Path) -> Dict[str, Any]:
        from backend.guardian.service import analyze
        findings, runs, _ = analyze(project_id, root)
        return {"serious": {f"{f.rule_id}|{f.file}" for f in findings if f.severity in ("critical", "high")},
                "all": {f"{f.rule_id}|{f.file}": f for f in findings},
                "tools": {r.tool: r.status for r in runs}}

    def _evaluate_static(self, project_id: str, exp: Experiment, cand: Candidate, ws: Path, baseline, base_sec, snapshot) -> None:
        from backend.evolution.autopilot import validation
        checks = validation.run_checks(ws, include_tests=True)
        verdict = validation.compare(baseline, checks)
        flaky = False
        if any("tests" in r for r in verdict["regressions"]):
            # a failing test is re-run once: passing now means the result is not reproducible (flaky)
            rerun = validation.check_tests(ws)
            if rerun.status == "passed":
                flaky = True
                verdict["notes"].append("the tests failed, then passed on a re-run: flaky, not counted as a defect")
            else:
                verdict["notes"].append(f"the failure was reproduced on a re-run ({rerun.status})")
        cand.checks = checks
        tests = next((c for c in checks if c.check_id == "tests"), None)
        cand.correctness = {**verdict, "accepted": verdict["accepted"] and not flaky, "flaky": flaky,
                            "tests": {"status": tests.status, "counts": tests.counts, "environment": tests.environment,
                                      "output_tail": redact(tests.output[-1500:])} if tests else None}
        if cand.correctness["accepted"] is False and not flaky:
            cand.failure_kind = "infrastructure" if verdict["unverified"] and not verdict["regressions"] else "candidate_defect"
        elif flaky:
            cand.failure_kind = "flaky"
        try:
            after = self._security_findings(project_id, ws)
        except Exception as e:  # noqa: BLE001
            cand.security = {"status": "unavailable", "detail": f"Security Guardian analysis failed: {type(e).__name__}"}
            return
        changed = set(cand.changes)
        new = [k for k in after["all"] if k not in base_sec["all"] and k.split("|", 1)[1] in changed]
        cand.security = {
            "status": "evaluated", "method": "Security Guardian static analysis of the candidate vs the snapshot",
            "new_serious": [f"{after['all'][k].title} ({k.split('|')[1]}:{after['all'][k].line})" for k in new
                            if after["all"][k].severity in ("critical", "high")],
            "new_other": [f"{after['all'][k].title} ({k.split('|')[1]})" for k in new
                          if after["all"][k].severity not in ("critical", "high")],
            "tools": after["tools"],
            "detail": "no new findings in the changed files" if not new else f"{len(new)} new finding(s) in the changed files"}
        if cand.security["new_serious"] and cand.failure_kind is None:
            cand.failure_kind = "candidate_defect"

    def _measure(self, project_id: str, eid: str, exp: Experiment, snapshot: Path, cands: List[Candidate],
                 ws_of: Dict[str, Path], stop) -> None:
        from backend.performance.engineer import gate as perf_gate
        from backend.performance.engineer import runner
        versions = {"baseline": snapshot, **{c.id: ws_of[c.id] for c in cands}}
        t0 = time.monotonic()
        results, env = runner.measure(versions, exp.plan.workload.model_copy(deep=True), stop,
                                      lambda name, status: self._audit(project_id, eid, f"measurement: {name} {status}"))
        self.store.update(project_id, "experiments", eid, lambda e: setattr(e, "measurement", {
            "environment": env.model_dump(), "baseline": results["baseline"].model_dump(),
            "seconds": round(time.monotonic() - t0, 1)}))
        for c in cands:
            m = results[c.id]
            comp = perf_gate.compare(results["baseline"], m, exp.plan.thresholds, exp.plan.target_endpoints)
            rows = [r for r in comp.per_endpoint if r["endpoint"] in exp.plan.target_endpoints] or comp.per_endpoint
            reps = min((len(r["after"].get("rep_medians_ms") or []) for r in rows), default=0)
            c.performance = {"decision": comp.decision, "reasons": comp.reasons, "target_rows": rows,
                             "per_endpoint": comp.per_endpoint, "resources": comp.resources, "status": m.status,
                             "error": m.error, "infrastructure": m.status != "measured",
                             "evidence": "sufficient" if reps >= 2 and comp.decision != "not_measured" else "insufficient",
                             "thresholds": exp.plan.thresholds.model_dump()}
            c.resources = {"cpu_avg_pct": m.resources.cpu_avg_pct, "mem_max_mb": m.resources.mem_max_mb,
                           "startup_seconds": m.startup_seconds, "method": m.resources.method}
            if comp.decision == "regressed" and c.failure_kind is None:
                c.failure_kind = "candidate_defect"
        c_dur = round(time.monotonic() - t0, 2)
        for c in cands:
            c.durations["measurement_s_shared"] = c_dur

    # --- approval and promotion ---------------------------------------------------------------------------------------

    def approve(self, project_id: str, project: Path, user_id: str, experiment_id: str, candidate_id: Optional[str] = None) -> Experiment:
        exp = self.store.get(project_id, "experiments", experiment_id)
        if exp is None:
            raise KeyError(experiment_id)
        cid = candidate_id or exp.selected
        if exp.status != "evaluated" or exp.outcome != "awaiting_approval" or cid != exp.selected:
            raise EvolutionError("only the selected candidate of an experiment with a measured improvement can be approved")
        cand = next(c for c in exp.candidates if c.id == cid)
        current = source_revision(project)
        if current != exp.source_revision:
            raise EvolutionError("the project changed since the experiment ran: run a new experiment on the current code")
        approval = Approval(candidate_id=cid, approved_by=user_id, source_revision=current, patch_hash=cand.patch_hash or "")
        self.store.update(project_id, "experiments", experiment_id, lambda e: (
            setattr(e, "approval", approval), setattr(e, "status", "approved"),
            e.audit.append({"at": now_iso(), "action": "approved", "user": user_id, "candidate": cid,
                            "source_revision": current[:12], "patch_hash": (cand.patch_hash or "")[:12]})))
        return self.store.get(project_id, "experiments", experiment_id)

    def promote(self, project_id: str, project: Path, user_id: str, experiment_id: str) -> Experiment:
        exp = self.store.get(project_id, "experiments", experiment_id)
        if exp is None:
            raise KeyError(experiment_id)
        if exp.status != "approved" or exp.approval is None or not exp.approval.valid:
            raise EvolutionError("approve the selected candidate before promoting it")
        cand = next(c for c in exp.candidates if c.id == exp.approval.candidate_id)
        stale = None
        if source_revision(project) != exp.approval.source_revision:
            stale = "the project changed after the approval"
        elif patch_hash(cand.changes) != exp.approval.patch_hash:
            stale = "the candidate's patch changed after the approval"
        if stale:
            self.store.update(project_id, "experiments", experiment_id, lambda e: (
                setattr(e.approval, "valid", False), setattr(e.approval, "invalidated_reason", stale),
                setattr(e, "status", "evaluated"), setattr(e, "promotion", Promotion(status="stale", error=stale)),
                e.audit.append({"at": now_iso(), "action": "approval invalidated", "reason": stale})))
            raise EvolutionError(f"approval is stale: {stale}; approve again (or run a new experiment)")
        self.store.update(project_id, "experiments", experiment_id, lambda e: (
            setattr(e, "status", "promoting"), setattr(e, "promotion", Promotion(status="running", started_at=now_iso()))))
        self._start(project_id, experiment_id, lambda: self._promote(project_id, experiment_id, Path(project), user_id))
        return self.store.get(project_id, "experiments", experiment_id)

    def _promote(self, project_id: str, eid: str, project: Path, user_id: str) -> None:
        from backend.evolution.autopilot import validation
        from backend.evolution.autopilot.executor import apply_all
        from backend.evolution.autopilot.plans import STRATEGY_AGENT
        exp = self.store.get(project_id, "experiments", eid)
        cand = next(c for c in exp.candidates if c.id == exp.approval.candidate_id)
        files = sorted(cand.changes)

        def promo(change):
            self.store.update(project_id, "experiments", eid, lambda e: change(e.promotion))
        try:
            originals = {rel: ((project / rel).read_text(encoding="utf-8") if (project / rel).is_file() else None) for rel in files}
            plan = Plan(
                id="pln_" + uuid.uuid4().hex[:12], project_id=project_id, user_id=user_id,
                objective=f"Evolution: {exp.opportunity.title} ({cand.strategy})", finding_ids=[],
                tasks=[PlanTask(id="t1", title=f"apply candidate {cand.id} ({cand.strategy})", finding_ids=[], files=files,
                                strategy="write_files", agent=STRATEGY_AGENT["write_files"],
                                modification=f"the approved candidate from experiment {eid}", contents=dict(cand.changes))],
                expected_files=files, agents=[STRATEGY_AGENT["write_files"], "Evolution gate (re-measurement)"],
                checks=["python_syntax", "quality_gate", "security_static", "tests", "evolution re-measure"],
                risks=exp.opportunity.possible_regressions,
                assumptions=[f"approved by {exp.approval.approved_by} for revision {exp.approval.source_revision[:12]}"],
                approval_required=["approved in the Evolution Engine"],
                completion_criteria=["checks pass", "the same measurement shows the improvement", "tests pass after promotion"],
                origin="evolution", origin_ref=eid)
            ap = self.autopilot
            ap.store.put(project_id, "plans", plan)
            ap.decide(project_id, plan.id, exp.approval.approved_by, "approved", note=f"Evolution Engine experiment {eid}")
            execution = ap.execute(project_id, plan.id, user_id, project, include_tests=True)
            promo(lambda p: (setattr(p, "autopilot_plan_id", plan.id), setattr(p, "execution_id", execution.id)))
            while True:
                execution = ap.store.get(project_id, "executions", execution.id)
                if execution.status not in ("queued", "running"):
                    break
                time.sleep(2)
            gate = (execution.verdict or {}).get("evolution") or {}
            promo(lambda p: setattr(p, "gate", gate))
            if not execution.applied_to_project:
                status = "rejected"
                outcome = "regression" if execution.status == "rejected" else "inconclusive"
                promo(lambda p: (setattr(p, "status", status), setattr(p, "error", execution.error),
                                 setattr(p, "finished_at", now_iso())))
                self._finish(project_id, eid, outcome, [f"promotion stopped before applying: {execution.error}"])
                return
            final = validation.check_tests(project)
            promo(lambda p: setattr(p, "final_tests", final))
            if final.status != "passed":
                restore = {rel: c for rel, c in originals.items() if c is not None}
                written, ok = apply_all(project, restore, f"roll back Evolution experiment {eid}")
                for rel, c in originals.items():
                    if c is None and (project / rel).exists():
                        (project / rel).unlink()
                detail = (f"final tests {final.status} after promotion; restored {len(written)} file(s) to their previous "
                          f"contents" + ("" if ok else " (the rollback could not write every file: check them)"))
                promo(lambda p: (setattr(p, "status", "rolled_back"), setattr(p, "rolled_back", True),
                                 setattr(p, "rollback_detail", detail), setattr(p, "finished_at", now_iso())))
                self._finish(project_id, eid, "regression", [detail])
                return
            promo(lambda p: (setattr(p, "status", "promoted"), setattr(p, "finished_at", now_iso())))
            self._finish(project_id, eid, "validated_improvement",
                         [f"applied after the checks and the re-measurement passed; final tests passed ({final.counts})",
                          *gate.get("reasons", [])[:2]])
        except Exception as e:  # noqa: BLE001
            _logger.exception("Evolution promotion %s failed", eid)
            msg = redact(f"{type(e).__name__}: {e}", 800)
            promo(lambda p: (setattr(p, "status", "failed"), setattr(p, "error", msg), setattr(p, "finished_at", now_iso())))
            self._finish(project_id, eid, "inconclusive", [f"promotion failed: {msg}"])

    def _finish(self, project_id: str, eid: str, outcome: str, reasons: List[str]) -> None:
        self.store.update(project_id, "experiments", eid, lambda e: (
            setattr(e, "status", "completed"), setattr(e, "outcome", outcome), setattr(e, "outcome_reasons", reasons),
            e.audit.append({"at": now_iso(), "action": f"promotion finished: {outcome}"})))
        memory.set_final_outcome(eid, outcome, self.store)

    # --- the Autopilot gate (MEASURED_GATES["evolution"]) ---------------------------------------------------------------

    def gate(self, plan: Plan, project: Path, workspace: Path, execution_id: str, should_stop, on_stage=None):
        from backend.performance.engineer import gate as perf_gate
        from backend.performance.engineer import runner
        from backend.performance.engineer.models import Comparison
        exp = self.store.get(plan.project_id, "experiments", plan.origin_ref or "")
        if exp is None:
            return Comparison(id=execution_id, decision="not_measured", reasons=["the experiment behind this plan was not found"])
        results, env = runner.measure({"baseline": project, "candidate": workspace}, exp.plan.workload.model_copy(deep=True),
                                      should_stop, on_stage)
        comparison = perf_gate.compare(results["baseline"], results["candidate"], exp.plan.thresholds, exp.plan.target_endpoints)
        comparison.id, comparison.environment = execution_id, env
        return comparison


global_evolution_engine = EvolutionEngine()
