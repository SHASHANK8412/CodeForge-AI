"""
AIForge Performance Engineer service.

  analysis   static findings + (if Docker and a FastAPI entry point are available) a measured
             baseline; measured bottlenecks come only from that run
  plan       an optimization plan for one finding, created as an Autopilot plan (origin
             "performance"): same approval, isolated workspace and correctness checks
  gate       during the Autopilot execution, after the correctness checks, the original project and
             the changed copy are measured side by side with the plan's workload; the change is
             applied only when the gate says "improved"
  report     findings, baseline, the change, correctness results, before/after metrics, decision
"""

import logging
import threading
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from backend.evolution.autopilot.models import Plan, PlanTask, now_iso
from backend.evolution.autopilot.redact import redact
from backend.evolution.autopilot.store import AutopilotStore
from backend.performance.engineer import gate as perf_gate
from backend.performance.engineer import runner, static
from backend.performance.engineer.models import (Comparison, Endpoint, Measurement, PerfAnalysis, PerfFinding, PerfPlan,
                                                 PerfRun, Thresholds, Workload)

_logger = logging.getLogger("aiforge.performance")
SLOW_MEDIAN_MS = 100.0
SLOW_P95_MS = 300.0
SLOW_STARTUP_S = 10.0


class PlanError(ValueError):
    pass


class Busy(RuntimeError):
    pass


class PerfStore(AutopilotStore):
    KINDS = {"analyses": PerfAnalysis, "findings": PerfFinding, "runs": PerfRun, "plans": PerfPlan,
             "comparisons": Comparison}
    PRUNE = (("analyses", 20, "started_at"), ("runs", 30, "started_at"), ("comparisons", 50, "created_at"))
    ENV_DIR = "AIFORGE_PERF_DIR"
    DEFAULT_ROOT = Path(__file__).resolve().parents[2] / "data" / "performance"

    def latest(self, project_id: str, kind: str, status: Optional[str] = None):
        items = [i for i in self.list(project_id, kind) if status is None or getattr(i, "status", None) == status]
        key = "started_at" if kind in ("analyses", "runs") else "created_at"
        return max(items, key=lambda i: getattr(i, key) or "", default=None)


def measured_findings(project_id: str, project: Path, m: Measurement) -> List[Dict[str, Any]]:
    """Bottlenecks shown by a baseline run (slow endpoints, errors, slow startup)."""
    from backend.twin.graph import routes_match
    owners = static.endpoint_owner(project)
    found = []

    def owner(endpoint: str):
        method, path = endpoint.split(" ", 1)
        for key, (file, line) in owners.items():
            k_method, k_path = key.split(" ", 1)
            if k_method == method and (k_path == path or routes_match(k_path, path)):
                return file, line
        return None, None

    for e in m.endpoints:
        key = f"{e.method} {e.path}"
        file, line = owner(key)
        if e.error_rate_pct > 0:
            found.append({"rule_id": "PERF-MEASURED-ERRORS", "category": "errors", "title": f"{key} fails under load",
                          "severity": "high" if e.error_rate_pct >= 5 else "medium", "evidence_kind": "measured",
                          "detection": "baseline workload run", "confidence": "high", "file": file, "line": line,
                          "endpoint": key, "measured_ms": e.median_ms,
                          "evidence": f"{e.errors} of {e.requests} requests failed ({e.error_rate_pct}%); status codes {e.status_codes}",
                          "impact": "failed requests; latency numbers for this endpoint only cover successful requests",
                          "recommendation": "Fix the failures first (see the app log in the baseline run).",
                          "validation": "re-run the baseline: error rate 0%"})
        if e.median_ms is not None and (e.median_ms >= SLOW_MEDIAN_MS or (e.p95_ms or 0) >= SLOW_P95_MS):
            found.append({"rule_id": "PERF-MEASURED-SLOW", "category": "slow_endpoint", "title": f"{key} is slow",
                          "severity": "high" if e.median_ms >= 3 * SLOW_MEDIAN_MS else "medium", "evidence_kind": "measured",
                          "detection": "baseline workload run", "confidence": "high", "file": file, "line": line,
                          "endpoint": key, "measured_ms": e.median_ms,
                          "evidence": f"median {e.median_ms} ms, p95 {e.p95_ms} ms, {e.throughput_rps} req/s over "
                                      f"{e.requests} requests (thresholds: median {SLOW_MEDIAN_MS:.0f} ms, p95 {SLOW_P95_MS:.0f} ms)",
                          "impact": f"every request to {key} waits about {e.median_ms} ms",
                          "recommendation": "Look at the static findings linked to this endpoint; otherwise profile its handler.",
                          "validation": f"median latency of {key} drops beyond the run-to-run spread"})
    if m.startup_seconds is not None and m.startup_seconds >= SLOW_STARTUP_S:
        found.append({"rule_id": "PERF-MEASURED-STARTUP", "category": "startup", "title": "Slow application startup",
                      "severity": "low", "evidence_kind": "measured", "detection": "baseline workload run",
                      "confidence": "medium", "file": None, "line": None, "endpoint": None, "measured_ms": None,
                      "evidence": f"{m.startup_seconds}s from container start to the first healthy answer (dependency install excluded)",
                      "impact": "slower deploys and restarts", "recommendation": "Look for work done at import time.",
                      "validation": "compare the measured startup time"})
    return found


class PerformanceEngineer:
    def __init__(self, store: Optional[PerfStore] = None, autopilot=None, background: bool = True):
        self.store = store or PerfStore()
        self._autopilot = autopilot
        self.background = background
        self._active: Dict[str, str] = {}
        self._lock = threading.Lock()
        if background:
            try:
                self.store.mark_interrupted()
            except Exception as e:  # noqa: BLE001
                _logger.warning("Performance Engineer: could not check for interrupted jobs: %s", e)

    @property
    def autopilot(self):
        if self._autopilot is None:
            from backend.evolution.autopilot.service import global_autopilot_service
            self._autopilot = global_autopilot_service
        return self._autopilot

    def _start(self, project_id: str, job_id: str, kind: str, target: Callable[[], None]) -> None:
        with self._lock:
            if project_id in self._active:
                self.store.delete(project_id, kind, job_id)
                raise Busy(f"another performance job ({self._active[project_id]}) is running for this project")
            self._active[project_id] = job_id

        def run():
            try:
                target()
            finally:
                with self._lock:
                    self._active.pop(project_id, None)
        if self.background:
            threading.Thread(target=run, name=f"perf-{job_id}", daemon=True).start()
        else:
            run()

    def active_job(self, project_id: str) -> Optional[str]:
        with self._lock:
            return self._active.get(project_id)

    # --- analysis -----------------------------------------------------------------------------

    def start_analysis(self, project_id: str, project_dir: Path, user_id: str, measure: bool = True,
                       workload: Optional[Workload] = None) -> PerfAnalysis:
        a = PerfAnalysis(id="pan_" + uuid.uuid4().hex[:12], project_id=project_id, user_id=user_id, started_at=now_iso())
        self.store.put(project_id, "analyses", a)
        self._start(project_id, a.id, "analyses",
                    lambda: self._analyze(project_id, a.id, Path(project_dir), user_id, measure, workload))
        return self.store.get(project_id, "analyses", a.id)

    def _analyze(self, project_id, analysis_id, project: Path, user_id, measure, workload) -> None:
        from backend.evolution.autopilot.codebase import build_project_map
        from backend.execution.preview_manager import backend_entry, backend_problem
        self.store.update(project_id, "analyses", analysis_id, lambda a: setattr(a, "status", "running"))
        try:
            stack = build_project_map(project).get("stack", [])
            supported = backend_entry(project) is not None
            raws, notes = static.project_findings(project)
            run = None
            if measure and supported:
                run = self._baseline(project_id, project, user_id, workload or Workload())
            measured = measured_findings(project_id, project, run.measurement) \
                if run is not None and run.measurement and run.measurement.status == "measured" else []
            findings = self._store_findings(project_id, raws + measured)

            def done(a: PerfAnalysis):
                a.status, a.finished_at = "completed", now_iso()
                a.stack, a.supported = stack, supported
                a.support_reason = ("FastAPI entry point found; endpoints can be measured in the Docker sandbox"
                                    if supported else f"runtime measurement needs a FastAPI app: {backend_problem(project)}"
                                    " (static findings only)")
                if notes:
                    a.support_reason += "; " + "; ".join(notes)
                a.finding_ids = [f.id for f in findings]
                a.baseline_run_id = run.id if run else None
                a.suggested_workload = run.workload if run else workload
            self.store.update(project_id, "analyses", analysis_id, done)
        except Exception as e:  # noqa: BLE001
            _logger.exception("Performance analysis %s failed", analysis_id)
            message = redact(f"{type(e).__name__}: {e}", 1000)

            def failed(a: PerfAnalysis):
                a.status, a.finished_at, a.error = "failed", now_iso(), message
            self.store.update(project_id, "analyses", analysis_id, failed)

    def _store_findings(self, project_id: str, raws: List[Dict[str, Any]]) -> List[PerfFinding]:
        previous = {f.id: f for f in self.store.list(project_id, "findings")}
        out: List[PerfFinding] = []
        seen = set()
        for raw in raws:
            fid = static.finding_id(project_id, raw)
            if fid in seen:
                continue
            seen.add(fid)
            f = PerfFinding(id=fid, project_id=project_id, **raw)
            if fid in previous and previous[fid].status in ("planned", "dismissed"):
                f.status = previous[fid].status
            out.append(f)
        # link static findings to the measured endpoint they sit in
        from backend.twin.graph import routes_match
        for m in [f for f in out if f.evidence_kind == "measured" and f.endpoint]:
            method, path = m.endpoint.split(" ", 1)
            for s in out:
                if s.evidence_kind == "measured" or not s.endpoint:
                    continue
                s_method, s_path = s.endpoint.split(" ", 1)
                if s_method == method and (s_path == path or routes_match(s_path, path)):
                    m.linked.append(s.id)
                    s.linked.append(m.id)
        # Findings no longer detected are dropped; the analyses and runs keep the history.
        with self.store._lock:
            data = self.store._load(project_id)
            data["findings"] = {f.id: f.model_dump(mode="json") for f in out}
            self.store._save(project_id, data)
        return out

    # --- baseline ----------------------------------------------------------------------------------

    def start_baseline(self, project_id: str, project_dir: Path, user_id: str, workload: Workload) -> PerfRun:
        run = PerfRun(id="prn_" + uuid.uuid4().hex[:12], project_id=project_id, user_id=user_id, workload=workload,
                      started_at=now_iso())
        self.store.put(project_id, "runs", run)
        self._start(project_id, run.id, "runs", lambda: self._baseline(project_id, Path(project_dir), user_id,
                                                                       workload, run.id))
        return self.store.get(project_id, "runs", run.id)

    def _baseline(self, project_id: str, project: Path, user_id: str, workload: Workload,
                  run_id: Optional[str] = None) -> PerfRun:
        if run_id is None:
            run = PerfRun(id="prn_" + uuid.uuid4().hex[:12], project_id=project_id, user_id=user_id, workload=workload,
                          started_at=now_iso())
            self.store.put(project_id, "runs", run)
            run_id = run.id
        self.store.update(project_id, "runs", run_id, lambda r: setattr(r, "status", "running"))

        def cancelled() -> bool:
            r = self.store.get(project_id, "runs", run_id)
            return bool(r and r.cancel_requested)

        def on_stage(name: str, status: str):
            def change(r: PerfRun):
                for s in r.stages:
                    if s["name"] == name:
                        s.update(status=status, at=now_iso())
                        return
                r.stages.append({"name": name, "status": status, "at": now_iso()})
            self.store.update(project_id, "runs", run_id, change)

        try:
            results, env = runner.measure({"baseline": project}, workload, cancelled, on_stage)
            m = results["baseline"]

            def done(r: PerfRun):
                r.measurement, r.environment, r.workload = m, env, workload
                r.status = {"measured": "completed", "cancelled": "cancelled", "unavailable": "unavailable"}.get(m.status, "failed")
                r.error = m.error
                r.finished_at = now_iso()
            from backend.time_machine.recorder import emit
            emit(project_id, "performance_measured", "Performance Engineer",
                 f"baseline run {m.status}: " + "; ".join(f"{e.method} {e.path} median {e.median_ms} ms" for e in m.endpoints[:5]),
                 "success" if m.status == "measured" else "error", task_id=run_id, refs={"run_id": run_id},
                 project_dir=project, error=m.error,
                 data={"endpoints": [{"endpoint": f"{e.method} {e.path}", "median_ms": e.median_ms, "p95_ms": e.p95_ms,
                                      "error_rate_pct": e.error_rate_pct, "rep_medians_ms": e.rep_medians_ms}
                                     for e in m.endpoints],
                       "resources": m.resources.model_dump()},
                 config={"workload": workload.model_dump(), "environment": env.model_dump() if env else None})
            return self.store.update(project_id, "runs", run_id, done)
        except Exception as e:  # noqa: BLE001
            _logger.exception("Baseline run %s failed", run_id)
            message = redact(f"{type(e).__name__}: {e}", 1000)

            def failed(r: PerfRun):
                r.status, r.error, r.finished_at = "failed", message, now_iso()
            return self.store.update(project_id, "runs", run_id, failed)

    def cancel_run(self, project_id: str, run_id: str) -> Optional[PerfRun]:
        def change(r: PerfRun):
            if r.status in ("queued", "running"):
                r.cancel_requested = True
        return self.store.update(project_id, "runs", run_id, change)

    # --- plans ---------------------------------------------------------------------------------------

    def create_plan(self, project_id: str, project_dir: Path, user_id: str, finding_id: str,
                    thresholds: Optional[Thresholds] = None, workload: Optional[Workload] = None) -> PerfPlan:
        from backend.execution.preview_manager import backend_entry
        from backend.evolution.autopilot.plans import STRATEGY_AGENT
        finding = self.store.get(project_id, "findings", finding_id)
        if finding is None:
            raise KeyError(finding_id)
        if finding.status == "dismissed":
            raise PlanError("the finding is dismissed")
        if finding.status == "planned":
            # planned again only once every earlier plan for it has ended without a verified improvement
            open_plans = [pp for pp in self.store.list(project_id, "plans") if pp.finding_id == finding.id
                          and (ap := self.autopilot.store.get(project_id, "plans", pp.autopilot_plan_id or ""))
                          and ap.status.value in ("awaiting_approval", "approved", "running", "draft")]
            if open_plans:
                raise PlanError(f"the finding already has an open plan ({open_plans[0].id})")
        if backend_entry(Path(project_dir)) is None:
            raise PlanError("measured verification needs a FastAPI app; this project has none")
        linked = [self.store.get(project_id, "findings", i) for i in finding.linked]
        linked = [f for f in linked if f is not None]
        files = sorted({f.file for f in [finding] + linked if f.file})
        if not files:
            raise PlanError("the finding is not tied to a file, so there is nothing to change")
        if not all(f.endswith(".py") for f in files):
            raise PlanError("only Python backend changes can be verified by measurement (frontend support comes later)")
        baseline = self.store.latest(project_id, "runs", "completed")
        measured_endpoint = finding.endpoint if finding.evidence_kind == "measured" else next(
            (f.endpoint for f in linked if f.evidence_kind == "measured"), None)
        wl = workload or (baseline.workload.model_copy(deep=True) if baseline else Workload())
        targets: List[str] = []
        if measured_endpoint:
            targets = [measured_endpoint]
        elif finding.endpoint and baseline:
            from backend.twin.graph import routes_match
            method, path = finding.endpoint.split(" ", 1)
            targets = [f"{e.method} {e.path}" for e in wl.endpoints if e.method == method
                       and (e.path == path or routes_match(path, e.path))]
        if not wl.endpoints:
            raise PlanError("no measured workload yet: run an analysis with measurement (Docker) first, or give a workload")
        if not targets:
            targets = [f"{e.method} {e.path}" for e in wl.endpoints]
        evidence = finding.evidence + "".join(f"\n- linked: {f.title} ({f.file}:{f.line}): {f.evidence}" for f in linked)
        # Recommendations that change behaviour (the API contract, data freshness) are not bundled into an
        # optimization: they need their own decision, so they are listed as risks instead.
        behaviour = {"pagination", "caching"}
        applied = [f for f in [finding] + linked if f.category not in behaviour and f.evidence_kind != "measured"]
        separate = [f for f in [finding] + linked if f.category in behaviour]
        if finding.category in behaviour:
            applied, separate = [finding], []     # the user chose this behaviour change explicitly
        conf = {"high": 1.0, "medium": 0.6, "low": 0.3}[finding.confidence]
        impact_ms = finding.measured_ms or next((f.measured_ms for f in linked if f.measured_ms), None)
        score = round((impact_ms or 10.0) * conf / max(1, len(files)), 2)
        risks = ["The change could alter behaviour; correctness checks (syntax, quality gate, tests) must not regress."]
        risks += [f"Not included (changes behaviour, needs its own decision): {f.title} - {f.recommendation}"
                  for f in separate]
        if finding.category in ("caching",):
            risks.append("Caching can serve stale data; only acceptable where freshness is not required.")
        if finding.category in ("blocking_async",):
            risks.append("Switching sync/async code changes how requests share threads; check concurrent behaviour.")
        tests = self._tests_for(Path(project_dir), files)
        plan = PerfPlan(
            id="ppl_" + uuid.uuid4().hex[:12], project_id=project_id, user_id=user_id, finding_id=finding.id,
            problem=finding.title, evidence=evidence,
            proposed_change=" ".join(dict.fromkeys(f.recommendation for f in applied)) or finding.recommendation,
            expected_benefit=("Estimate (not measured): lower latency on " + ", ".join(targets) + " if the cause is "
                              + "; ".join(sorted({f.impact for f in applied} or {finding.impact}))
                              + ". The actual effect is measured after the change."
                              + (f" Current measured median: {impact_ms} ms." if impact_ms else
                                 " This code path has not been measured yet.")),
            files=files, risks=risks, tests=tests, workload=wl, thresholds=thresholds or Thresholds(),
            target_endpoints=targets,
            rollback="The change is made in an isolated copy. It is written to the project only if the correctness "
                     "checks and the performance gate both pass; otherwise the copy is discarded and the project "
                     "stays as it was. After an applied change, the recorded diff can be reverted.",
            completion_criteria=[f"Median latency of {', '.join(targets)} improves by at least "
                                 f"{(thresholds or Thresholds()).min_improvement_pct}% beyond the run-to-run noise",
                                 "No endpoint, error rate, throughput or memory regression beyond the thresholds",
                                 "Correctness checks do not regress"],
            rank_score=score,
            rank_reasons=[f"impact: {impact_ms} ms measured" if impact_ms else "impact: not measured (default weight)",
                          f"confidence {finding.confidence}", f"{len(files)} file(s) to change"],
        )
        request = (f"Performance optimization. Problem: {plan.problem}\nEvidence:\n{evidence}\n\n"
                   f"Proposed change: {plan.proposed_change}\n\nKeep behaviour, response shapes and status codes "
                   f"unchanged: the same requests must return the same data (no pagination or new parameters with "
                   f"defaults that limit results). Do not add caching or concurrency unless the evidence calls for it.")
        ap = Plan(
            id="pln_" + uuid.uuid4().hex[:12], project_id=project_id, user_id=user_id, objective=f"Optimize: {plan.problem}",
            finding_ids=[], tasks=[PlanTask(id="t1", title=plan.problem[:120], finding_ids=[], files=files, strategy="model",
                                            agent=STRATEGY_AGENT["model"], modification=plan.proposed_change,
                                            request=request)],
            expected_files=files, agents=[STRATEGY_AGENT["model"], "Performance gate (measured before/after)"],
            checks=["python_syntax", "quality_gate", "security_static", "tests", "performance"],
            risks=risks, assumptions=["Created by the Performance Engineer (plan " + plan.id + "); the change is kept only "
                                      "if the measured comparison says 'improved'."],
            approval_required=["Apply the optimization if correctness checks and the performance gate pass"],
            completion_criteria=plan.completion_criteria, origin="performance", origin_ref=plan.id,
        )
        plan.autopilot_plan_id = ap.id
        self.autopilot.store.put(project_id, "plans", ap)
        self.store.put(project_id, "plans", plan)
        self.store.update(project_id, "findings", finding.id, lambda f: setattr(f, "status", "planned"))
        return plan

    @staticmethod
    def _tests_for(project: Path, files: List[str]) -> List[str]:
        try:
            from backend.twin.graph import build_graph
            from backend.twin.index import GraphIndex
            from backend.twin.models import GraphAnalysis
            b = build_graph(project, deadline_seconds=20)
            index = GraphIndex(GraphAnalysis(id="tmp", project_id="tmp", user_id="tmp", nodes=list(b.nodes.values()),
                                             edges=list(b.edges.values())))
            return sorted({src for f in files for src, _ in index.dependents(f) if index.node_type(src) == "test"})
        except Exception:  # noqa: BLE001 - test selection is advisory
            return []

    # --- the gate (called by the Autopilot executor) -------------------------------------------------------

    def gate(self, autopilot_plan: Plan, project: Path, workspace: Path, execution_id: str,
             should_stop: Callable[[], bool], on_stage: Optional[Callable[[str, str], None]] = None) -> Comparison:
        plan = self.store.get(autopilot_plan.project_id, "plans", autopilot_plan.origin_ref or "")
        if plan is None:
            return Comparison(id=execution_id, decision="not_measured",
                              reasons=["the performance plan behind this Autopilot plan was not found"])
        results, env = runner.measure({"baseline": project, "candidate": workspace}, plan.workload.model_copy(deep=True),
                                      should_stop, on_stage)
        comparison = perf_gate.compare(results["baseline"], results["candidate"], plan.thresholds, plan.target_endpoints)
        comparison.id, comparison.plan_id, comparison.environment = execution_id, plan.id, env
        self.store.put(plan.project_id, "comparisons", comparison)
        status = {"improved": "verified"}.get(comparison.decision, "not_improved")
        self.store.update(plan.project_id, "findings", plan.finding_id, lambda f: setattr(f, "status", status))
        return comparison

    # --- report ---------------------------------------------------------------------------------------------

    def report(self, project_id: str, plan_id: str) -> Optional[Dict[str, Any]]:
        plan = self.store.get(project_id, "plans", plan_id)
        if plan is None:
            return None
        ap_plan = self.autopilot.store.get(project_id, "plans", plan.autopilot_plan_id or "")
        runs = [e for e in self.autopilot.store.list(project_id, "executions") if e.plan_id == plan.autopilot_plan_id]
        execution = max(runs, key=lambda e: e.started_at or "", default=None)
        comparison = self.store.get(project_id, "comparisons", execution.id) if execution else None
        analysis = self.store.latest(project_id, "analyses")
        baseline = self.store.get(project_id, "runs", analysis.baseline_run_id) if analysis and analysis.baseline_run_id else None
        finding = self.store.get(project_id, "findings", plan.finding_id)
        remaining = [f for f in self.store.list(project_id, "findings") if f.status == "open"]
        decision = comparison.decision if comparison else None
        next_steps = []
        if execution is None:
            next_steps.append("Approve and execute the plan to measure the change.")
        elif decision == "improved" and execution.applied_to_project:
            next_steps.append("Run a new analysis to establish the new baseline.")
        elif decision == "inconclusive":
            next_steps.append("Increase requests or repetitions, or test with more data, to separate the change from noise.")
        elif decision == "regressed":
            next_steps.append("The change made things worse and was not applied; revise the approach.")
        elif decision == "not_measured":
            next_steps.append("Fix the measurement problem (Docker, app start-up, workload) and run again.")
        if remaining:
            next_steps.append(f"{len(remaining)} other finding(s) remain open.")
        return {
            "plan": plan.model_dump(mode="json"),
            "finding": finding.model_dump(mode="json") if finding else None,
            "autopilot_plan_status": ap_plan.status.value if ap_plan else None,
            "baseline": baseline.model_dump(mode="json") if baseline else None,
            "execution": execution.model_dump(mode="json", exclude={"diff"}) if execution else None,
            "diff": execution.diff if execution else "",
            "correctness": {"before": [c.model_dump() for c in execution.baseline], "after": [c.model_dump() for c in execution.after],
                            "verdict": {k: v for k, v in (execution.verdict or {}).items() if k != "performance"}} if execution else None,
            "comparison": comparison.model_dump(mode="json") if comparison else None,
            "applied": bool(execution and execution.applied_to_project),
            "rollback_status": ("not needed: applied after passing both gates" if execution and execution.applied_to_project
                                else "nothing applied: the isolated copy was discarded" if execution and
                                execution.status not in ("queued", "running") else "n/a"),
            "remaining_findings": [{"id": f.id, "title": f.title, "evidence_kind": f.evidence_kind} for f in remaining][:30],
            "next_steps": next_steps,
            "measured_vs_estimated": "Before/after numbers are measurements from the runs above; the plan's expected "
                                     "benefit is an estimate.",
        }


global_performance_engineer = PerformanceEngineer()


def endpoints_from_strings(items: List[str]) -> List[Endpoint]:
    out = []
    for item in items:
        method, _, path = item.strip().partition(" ")
        if path.startswith("/"):
            out.append(Endpoint(method=method.upper(), path=path))
    return out
