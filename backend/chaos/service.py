"""
AIForge Chaos Engineer service.

Lifecycle of an assessment:
  queued -> preflight -> awaiting_approval (or refused) -> [approve] -> running -> evaluating ->
  completed | inconclusive | failed | aborted
Every action is appended to the assessment's audit log. Experiments run in one isolated sandbox per
assessment; it is always removed at the end, after errors and after an abort.

Repairs: a reproduced finding becomes an Autopilot plan (origin "chaos"). After the correctness
checks, the gate runs the same scenario against the original project and the changed copy, each in its
own sandbox, and the change is applied only if the failed criteria now pass and nothing that passed
before fails.
"""

import logging
import threading
import time
import uuid
from pathlib import Path
from typing import Callable, Dict, List, Optional

from backend.chaos import evaluate
from backend.chaos.models import Assessment, AssessmentConfig, ChaosFinding, ScenarioResult, Target
from backend.chaos.sandbox import Sandbox, SandboxError, preflight
from backend.chaos.scenarios import NEEDS_DEPENDENCY, SCENARIOS, Aborted, run_scenario
from backend.evolution.autopilot.models import Plan, PlanTask, now_iso
from backend.evolution.autopilot.redact import redact
from backend.evolution.autopilot.store import AutopilotStore

_logger = logging.getLogger("aiforge.chaos")
ASSESSMENT_DEADLINE_SECONDS = 1800


class ChaosError(ValueError):
    pass


class Busy(RuntimeError):
    pass


class GateResult(Assessment):
    """The repair gate's two runs (original vs changed copy) and its decision."""
    plan_id: Optional[str] = None
    decision: str = "not_measured"               # improved | regressed | inconclusive | not_measured
    reasons: List[str] = []
    candidate_results: List[ScenarioResult] = []


class ChaosStore(AutopilotStore):
    KINDS = {"assessments": Assessment, "findings": ChaosFinding, "gates": GateResult}
    PRUNE = (("assessments", 30, "created_at"), ("gates", 30, "created_at"))
    ENV_DIR = "AIFORGE_CHAOS_DIR"
    DEFAULT_ROOT = Path(__file__).resolve().parents[1] / "data" / "chaos"


class ChaosEngineer:
    def __init__(self, store: Optional[ChaosStore] = None, autopilot=None, background: bool = True):
        self.store = store or ChaosStore()
        self._autopilot = autopilot
        self.background = background
        self._active: Dict[str, str] = {}
        self._lock = threading.Lock()
        if background:
            try:
                self.store.mark_interrupted()
            except Exception as e:  # noqa: BLE001
                _logger.warning("Chaos Engineer: could not check for interrupted jobs: %s", e)

    @property
    def autopilot(self):
        if self._autopilot is None:
            from backend.evolution.autopilot.service import global_autopilot_service
            self._autopilot = global_autopilot_service
        return self._autopilot

    def _audit(self, a: Assessment, action: str, **details) -> None:
        a.audit.append({"at": now_iso(), "action": action, **{k: redact(str(v), 500) for k, v in details.items()}})

    # --- create + preflight ----------------------------------------------------------------------------

    def create(self, project_id: str, project_dir: Path, user_id: str, config: AssessmentConfig) -> Assessment:
        unknown = [s for s in config.scenarios if s not in SCENARIOS]
        if unknown or not config.scenarios:
            raise ChaosError(f"unknown scenarios: {unknown}" if unknown else "choose at least one scenario")
        a = Assessment(id="cha_" + uuid.uuid4().hex[:12], project_id=project_id, user_id=user_id, config=config,
                       status="preflight")
        self._audit(a, "created", user=user_id, scenarios=config.scenarios, environment=config.environment)
        a.preflight = preflight(Path(project_dir), config, NEEDS_DEPENDENCY)
        failed = [c for c in a.preflight if not c.passed]
        if failed:
            a.status = "refused"
            a.error = "preflight failed: " + "; ".join(f"{c.check}: {c.detail}" for c in failed)
            self._audit(a, "refused", reasons=a.error)
        else:
            a.status = "awaiting_approval"
            self._audit(a, "preflight passed; waiting for explicit approval",
                        disruptive=[s for s in config.scenarios if SCENARIOS[s].disruptive])
        self.store.put(project_id, "assessments", a)
        return a

    def approve(self, project_id: str, assessment_id: str, project_dir: Path, user_id: str) -> Assessment:
        a = self.store.get(project_id, "assessments", assessment_id)
        if a is None:
            raise KeyError(assessment_id)
        if a.status != "awaiting_approval":
            raise ChaosError(f"the assessment is '{a.status}'; only one awaiting approval can be approved")
        # preflight again: conditions may have changed since it was created
        a.preflight = preflight(Path(project_dir), a.config, NEEDS_DEPENDENCY)
        if not all(c.passed for c in a.preflight):
            def refuse(x: Assessment):
                x.preflight, x.status = a.preflight, "refused"
                x.error = "preflight failed at approval: " + "; ".join(c.check for c in a.preflight if not c.passed)
                self._audit(x, "refused at approval", reasons=x.error)
            return self.store.update(project_id, "assessments", assessment_id, refuse)

        def approved(x: Assessment):
            x.status, x.approved_by, x.approved_at = "queued", user_id, now_iso()
            self._audit(x, "approved", user=user_id)
        self.store.update(project_id, "assessments", assessment_id, approved)
        self._start(project_id, assessment_id, lambda: self._run(project_id, assessment_id, Path(project_dir)))
        return self.store.get(project_id, "assessments", assessment_id)

    def abort(self, project_id: str, assessment_id: str, user_id: str) -> Optional[Assessment]:
        def change(a: Assessment):
            if a.status in ("queued", "running", "recovering", "evaluating", "preflight"):
                a.abort_requested = True
                self._audit(a, "abort requested", user=user_id)
            elif a.status == "awaiting_approval":
                a.status, a.finished_at = "aborted", now_iso()
                self._audit(a, "cancelled before approval", user=user_id)
        return self.store.update(project_id, "assessments", assessment_id, change)

    def _start(self, project_id: str, job_id: str, target: Callable[[], None]) -> None:
        with self._lock:
            if project_id in self._active:
                raise Busy(f"another chaos experiment ({self._active[project_id]}) is running for this project")
            self._active[project_id] = job_id

        def run():
            try:
                target()
            finally:
                with self._lock:
                    self._active.pop(project_id, None)
        if self.background:
            threading.Thread(target=run, name=f"chaos-{job_id}", daemon=True).start()
        else:
            run()

    def active_job(self, project_id: str) -> Optional[str]:
        with self._lock:
            return self._active.get(project_id)

    # --- the experiment --------------------------------------------------------------------------------

    def execute(self, project: Path, config: AssessmentConfig, label: str,
                should_stop: Callable[[], bool], on_event: Callable[[str, str], None]):
        """Run the configured scenarios in one sandbox. Returns (results, setup steps, cleanup steps)."""
        from backend.chaos.models import ScenarioResult
        deadline = time.monotonic() + ASSESSMENT_DEADLINE_SECONDS
        stop = lambda: should_stop() or time.monotonic() > deadline  # noqa: E731
        sb = Sandbox(project, config, label)
        results: List[ScenarioResult] = []
        setup_steps: List[str] = []
        cleanup_steps: List[str] = []
        try:
            on_event("setup", "creating the isolated sandbox")
            setup_steps = sb.setup()
            health = Target(path=config.health_path or "/health")
            if sb.wait_healthy(health, 60) is None:
                raise SandboxError("the app did not answer its health check within 60s; nothing was injected")
            endpoints = list(config.endpoints) or sb.openapi_endpoints()
            if f"{health.method} {health.path}" not in {f"{e.method} {e.path}" for e in endpoints}:
                endpoints.append(health)
            ctx = {"endpoints": endpoints, "health": health, "limits": config.limits, "should_stop": stop,
                   "dependency": config.dependencies[0].name if config.dependencies else None,
                   "on_step": lambda scenario, text: on_event(scenario, text)}
            order = sorted(config.scenarios, key=lambda s: s == "app_restart")    # the restart last
            for sid in order:
                if stop():
                    raise Aborted("abort requested")
                on_event(sid, "starting")
                results.append(run_scenario(sb, sid, ctx))
                for dep in config.dependencies:          # reset between scenarios
                    try:
                        sb.start_dependency(dep.name)
                        sb.control(dep.name, "ok")
                    except SandboxError:
                        pass
                sb.wait_healthy(health, config.limits.recovery_budget_s)
        finally:
            cleanup_steps = sb.cleanup()
            on_event("cleanup", "; ".join(cleanup_steps) or "nothing to remove")
        return results, setup_steps, cleanup_steps

    def _run(self, project_id: str, assessment_id: str, project: Path) -> None:
        def update(change):
            return self.store.update(project_id, "assessments", assessment_id, change)

        def stopped() -> bool:
            a = self.store.get(project_id, "assessments", assessment_id)
            return bool(a and a.abort_requested)

        def event(scenario: str, text: str):
            def change(a: Assessment):
                a.current = scenario
                if a.status in ("queued", "running", "recovering"):
                    a.status = "recovering" if "restored" in text or "recovery" in text else "running"
                self._audit(a, f"{scenario}: {text}")
            update(change)

        a = self.store.get(project_id, "assessments", assessment_id)
        update(lambda x: (setattr(x, "status", "running"), setattr(x, "started_at", now_iso())))
        results, outcome, error = [], "completed", None
        try:
            results, setup, cleanup = self.execute(project, a.config, assessment_id[-8:], stopped, event)
            update(lambda x: self._audit(x, "sandbox", setup=setup, cleanup=cleanup))
        except Aborted:
            outcome, error = "aborted", "aborted by the user; the sandbox was removed"
        except (SandboxError, TimeoutError) as e:
            outcome, error = "failed", redact(str(e), 1500)
        except Exception as e:  # noqa: BLE001 - recorded on the assessment
            _logger.exception("Chaos assessment %s failed", assessment_id)
            outcome, error = "failed", redact(f"{type(e).__name__}: {e}", 1500)
        update(lambda x: setattr(x, "status", "evaluating"))
        try:
            current = self.store.get(project_id, "assessments", assessment_id)
            current.results = results
            findings = evaluate.build_findings(project_id, project, current) if results else []
            impact = evaluate.impact(project, current) if results else {}
        except Exception as e:  # noqa: BLE001
            _logger.exception("Chaos evaluation %s failed", assessment_id)
            findings, impact = [], {}
            error = (error + "; " if error else "") + f"evaluation failed: {e}"
        sc = evaluate.score(results)
        if outcome == "completed" and results and all(r.status in ("inconclusive", "not_evaluated") for r in results):
            outcome = "inconclusive"
        self._save_findings(project_id, findings)

        def done(x: Assessment):
            x.results, x.score, x.impact = results, sc, impact
            x.finding_ids = [f.id for f in findings]
            x.status, x.error, x.finished_at, x.current = outcome, error, now_iso(), None
            self._audit(x, f"finished: {outcome}", score=sc.get("overall"))
        update(done)
        from backend.time_machine.recorder import emit
        emit(project_id, "resilience_assessed", "Chaos Engineer",
             f"chaos assessment {outcome}: score {sc.get('overall')}; " + ", ".join(f"{r.scenario}: {r.status}" for r in results),
             "success" if outcome == "completed" else "error" if outcome == "failed" else "inconclusive",
             task_id=assessment_id, refs={"chaos_assessment_id": assessment_id}, project_dir=project, error=error,
             data={"score": sc, "results": [{"scenario": r.scenario, "status": r.status, "recovery_seconds": r.recovery_seconds}
                                            for r in results], "findings": [f.id for f in findings]})

    def _save_findings(self, project_id: str, findings: List[ChaosFinding]) -> None:
        previous = {f.id: f for f in self.store.list(project_id, "findings")}
        with self.store._lock:
            data = self.store._load(project_id)
            for f in findings:
                if f.id in previous and previous[f.id].status in ("planned", "dismissed", "verified"):
                    f.status = previous[f.id].status
                data["findings"][f.id] = f.model_dump(mode="json")
            self.store._save(project_id, data)

    # --- repair -------------------------------------------------------------------------------------------

    def create_plan(self, project_id: str, project_dir: Path, user_id: str, finding_id: str) -> Plan:
        from backend.evolution.autopilot.plans import STRATEGY_AGENT
        f = self.store.get(project_id, "findings", finding_id)
        if f is None:
            raise KeyError(finding_id)
        if f.kind != "reproduced" or not f.scenario:
            raise ChaosError("only reproduced failures can be repaired and verified (static suspicions are not)")
        if not f.file or not f.file.endswith(".py"):
            raise ChaosError("the failure is not tied to a Python file that could be changed")
        source = self._assessment_of(project_id, f)
        if source is None:
            raise ChaosError("the assessment that reproduced this failure was not found")
        open_plans = [p for p in self.autopilot.store.list(project_id, "plans") if p.origin == "chaos"
                      and p.origin_ref == f.id and p.status.value in ("awaiting_approval", "approved", "running", "draft")]
        if open_plans:
            raise ChaosError(f"the finding already has an open plan ({open_plans[0].id})")
        request = (f"Resilience fix. Under the controlled failure '{f.scenario}' the endpoint(s) {f.component} failed: "
                   f"{f.expected}\nObserved: {f.observed}\nLikely cause ({f.root_cause_level.replace('_', ' ')}): "
                   f"{f.root_cause}\nFix: {f.remediation}\nKeep the successful responses exactly as they are "
                   f"(same fields and status codes); when the dependency fails, answer quickly with the data that does "
                   f"not need it (the dependent field set to null) or a 503 with a short message - never exception "
                   f"details. Keep explicit timeouts below {source.config.limits.timeout_budget_ms} ms.")
        plan = Plan(
            id="pln_" + uuid.uuid4().hex[:12], project_id=project_id, user_id=user_id,
            objective=f"Resilience: {f.title}", finding_ids=[],
            tasks=[PlanTask(id="t1", title=f.title[:120], finding_ids=[], files=[f.file], strategy="model",
                            agent=STRATEGY_AGENT["model"], modification=f.remediation, request=request)],
            expected_files=[f.file], agents=[STRATEGY_AGENT["model"], "Chaos gate (same experiment before/after)"],
            checks=["python_syntax", "quality_gate", "security_static", "tests", f"chaos: {f.scenario}"],
            risks=["Error handling changes what clients see when the dependency fails; successful responses must "
                   "stay the same (checked by the tests)."],
            assumptions=[f"Created by the Chaos Engineer from finding {f.id}; the change is kept only if the "
                         f"'{f.scenario}' experiment shows the failure is gone and nothing else got worse."],
            approval_required=["Apply the change if correctness checks and the chaos gate pass"],
            completion_criteria=[f"criterion '{f.criterion}' passes in scenario '{f.scenario}'",
                                 "no criterion that passed before fails", "correctness checks do not regress"],
            origin="chaos", origin_ref=f.id)
        self.autopilot.store.put(project_id, "plans", plan)
        self.store.update(project_id, "findings", f.id, lambda x: setattr(x, "status", "planned"))
        return plan

    def _assessment_of(self, project_id: str, f: ChaosFinding) -> Optional[Assessment]:
        items = [a for a in self.store.list(project_id, "assessments") if f.id in a.finding_ids]
        return max(items, key=lambda a: a.created_at, default=None)

    def gate(self, plan: Plan, project: Path, workspace: Path, execution_id: str,
             should_stop: Callable[[], bool], on_stage: Optional[Callable[[str, str], None]] = None) -> GateResult:
        """The Autopilot executor's chaos stage: same scenario on the original and the changed copy."""
        f = self.store.get(plan.project_id, "findings", plan.origin_ref or "")
        source = self._assessment_of(plan.project_id, f) if f else None
        if f is None or source is None:
            return GateResult(id=execution_id, project_id=plan.project_id, user_id="system",
                              config=AssessmentConfig(scenarios=["request_burst"]), decision="not_measured",
                              reasons=["the finding or its assessment was not found"], purpose="repair_gate")
        config = source.config.model_copy(update={"scenarios": [f.scenario]})
        event = on_stage or (lambda a, b: None)
        g = GateResult(id=execution_id, project_id=plan.project_id, user_id="system", config=config,
                       plan_id=plan.id, purpose="repair_gate", status="running", started_at=now_iso())
        try:
            base, _, _ = self.execute(project, config, "gate_base", should_stop, lambda s, t: event("original", f"{s}: {t}"))
            cand, _, _ = self.execute(workspace, config, "gate_cand", should_stop, lambda s, t: event("changed copy", f"{s}: {t}"))
        except Aborted:
            g.status, g.decision, g.reasons = "aborted", "not_measured", ["aborted"]
            self.store.put(plan.project_id, "gates", g)
            return g
        except (SandboxError, TimeoutError) as e:
            g.status, g.decision, g.reasons = "failed", "not_measured", [redact(str(e), 500)]
            self.store.put(plan.project_id, "gates", g)
            return g
        g.results, g.candidate_results = base, cand
        g.decision, g.reasons = compare_runs(base, cand, f.criterion)
        g.status, g.finished_at = "completed", now_iso()
        self.store.put(plan.project_id, "gates", g)
        status = "verified" if g.decision == "improved" else "not_improved"

        def finding(x: ChaosFinding):
            x.status = status
            if g.decision == "improved" and x.root_cause_level == "probable":
                x.root_cause_level = "confirmed"         # the targeted fix removed the failure in the same experiment
        self.store.update(plan.project_id, "findings", f.id, finding)
        return g


def compare_runs(base, cand, criterion_id: Optional[str]):
    """improved: the target criterion failed before and passes now, and nothing that passed now fails."""
    before = {c.id: c for r in base for c in r.criteria}
    after = {c.id: c for r in cand for c in r.criteria}
    reasons = []
    regressed = [cid for cid, c in before.items() if c.status == "passed" and after.get(cid) and after[cid].status == "failed"]
    if regressed:
        return "regressed", [f"'{cid}' passed before the change and fails after it: {after[cid].evidence}" for cid in regressed]
    target_b, target_a = before.get(criterion_id), after.get(criterion_id)
    affected_before = {ep for r in base for ep in r.affected_endpoints}
    affected_after = {ep for r in cand for ep in r.affected_endpoints}
    if target_b is not None and target_b.status == "failed" and target_a is not None and \
            target_a.status == "not_evaluated" and affected_before and not (affected_before & affected_after):
        # The criterion judges how *affected* endpoints answer; after the change the same failure no longer
        # affects them at all (observed in the same experiment), which removes the failure.
        reasons.append(f"'{criterion_id}' failed before ({target_b.evidence}); after the change the failure no "
                       f"longer affects {sorted(affected_before)} (they answered as at baseline during the failure)")
        return "improved", reasons
    if target_b is None or target_a is None or "not_evaluated" in (target_b.status, target_a.status):
        return "inconclusive", [f"'{criterion_id}' could not be evaluated in both runs"]
    if target_b.status == "failed" and target_a.status == "passed":
        reasons.append(f"'{criterion_id}' failed before ({target_b.evidence}) and passes after ({target_a.evidence})")
        fixed = [cid for cid, c in before.items() if c.status == "failed" and after.get(cid) and after[cid].status == "passed"
                 and cid != criterion_id]
        if fixed:
            reasons.append(f"also fixed: {', '.join(fixed)}")
        return "improved", reasons
    if target_b.status == "passed":
        return "inconclusive", [f"'{criterion_id}' already passed in the original run this time ({target_b.evidence})"]
    return "inconclusive", [f"'{criterion_id}' still fails after the change: {target_a.evidence}"]


global_chaos_engineer = ChaosEngineer()
