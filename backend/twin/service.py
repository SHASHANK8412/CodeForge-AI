"""
AIForge Digital Twin service: graph analyses and impact simulations as background jobs, impact
reports turned into Autopilot plans (approval and execution reuse Autopilot), and the comparison of
each report's prediction with what the linked execution actually changed.
"""

import logging
import threading
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from backend.evolution.autopilot.models import Plan, PlanTask, now_iso
from backend.evolution.autopilot.redact import redact
from backend.evolution.autopilot.store import AutopilotStore
from backend.twin.graph import DEFAULT_DEADLINE_SECONDS, build_graph, find_cycles, project_fingerprint
from backend.twin.models import GraphAnalysis, ImpactReport, Outcome

_logger = logging.getLogger("aiforge.twin")


class TwinStore(AutopilotStore):
    KINDS = {"graphs": GraphAnalysis, "reports": ImpactReport}
    PRUNE = (("graphs", 3, "started_at"), ("reports", 100, "created_at"))
    ENV_DIR = "AIFORGE_TWIN_DIR"
    DEFAULT_ROOT = Path(__file__).resolve().parents[1] / "data" / "twin"

    def latest_graph(self, project_id: str) -> Optional[GraphAnalysis]:
        done = [g for g in self.list(project_id, "graphs") if g.status == "completed"]
        return max(done, key=lambda g: g.started_at or "", default=None)


class Busy(RuntimeError):
    pass


class TwinService:
    def __init__(self, store: Optional[TwinStore] = None, autopilot=None, background: bool = True,
                 deadline_seconds: float = DEFAULT_DEADLINE_SECONDS):
        self.store = store or TwinStore()
        self._autopilot = autopilot
        self.background = background
        self.deadline_seconds = deadline_seconds
        self._active: Dict[str, str] = {}
        self._lock = threading.Lock()
        if background:
            try:
                self.store.mark_interrupted()
            except Exception as e:  # noqa: BLE001 - recovery must not stop the server starting
                _logger.warning("Digital Twin: could not check for interrupted jobs: %s", e)

    @property
    def autopilot(self):
        if self._autopilot is None:
            from backend.evolution.autopilot.service import global_autopilot_service
            self._autopilot = global_autopilot_service
        return self._autopilot

    def _start(self, project_id: str, job_id: str, target: Callable[[], None], kind: str = "") -> None:
        with self._lock:
            if project_id in self._active:
                if kind:                      # the record saved for this job would otherwise stay 'queued'
                    self.store.delete(project_id, kind, job_id)
                raise Busy(f"another Digital Twin job ({self._active[project_id]}) is running for this project")
            self._active[project_id] = job_id

        def run():
            try:
                target()
            finally:
                with self._lock:
                    self._active.pop(project_id, None)
        if self.background:
            threading.Thread(target=run, name=f"twin-{job_id}", daemon=True).start()
        else:
            run()

    def active_job(self, project_id: str) -> Optional[str]:
        with self._lock:
            return self._active.get(project_id)

    # --- graph -------------------------------------------------------------------------------

    def start_analysis(self, project_id: str, project_dir: Path, user_id: str) -> GraphAnalysis:
        g = GraphAnalysis(id="grf_" + uuid.uuid4().hex[:12], project_id=project_id, user_id=user_id, started_at=now_iso())
        self.store.put(project_id, "graphs", g)
        self._start(project_id, g.id, lambda: self._build(project_id, g.id, Path(project_dir)), "graphs")
        return self.store.get(project_id, "graphs", g.id)

    def _build(self, project_id: str, graph_id: str, project: Path) -> GraphAnalysis:
        self.store.update(project_id, "graphs", graph_id, lambda g: setattr(g, "status", "running"))
        try:
            b = build_graph(project, self.deadline_seconds)
            file_ids = [n for n in b.nodes if n.startswith("file:")]
            cycles = find_cycles(file_ids, [(e.source, e.target) for e in b.edges.values() if e.type == "imports"])
            languages: Dict[str, int] = {}
            for n in b.nodes.values():
                if n.type in ("file", "test") and n.language:
                    languages[n.language] = languages.get(n.language, 0) + 1
            types: Dict[str, int] = {}
            for n in b.nodes.values():
                types[n.type] = types.get(n.type, 0) + 1
            edge_types: Dict[str, int] = {}
            for e in b.edges.values():
                edge_types[e.type] = edge_types.get(e.type, 0) + 1
            from backend.evolution.autopilot.codebase import build_project_map
            stack = build_project_map(project).get("stack", [])

            def done(g: GraphAnalysis):
                g.status, g.finished_at = "completed", now_iso()
                g.fingerprint = b.fingerprint()
                g.nodes, g.edges = list(b.nodes.values()), list(b.edges.values())
                g.unresolved, g.cycles, g.limits = b.unresolved[:500], cycles, b.limits
                g.stats = {"files": len(b.files), "parsed_files": len(b.sources), "nodes": len(b.nodes),
                           "edges": len(b.edges), "node_types": types, "edge_types": edge_types,
                           "languages": languages, "stack": stack,
                           "inferred_edges": sum(1 for e in b.edges.values() if e.certainty == "inferred"),
                           "unresolved": len(b.unresolved), "cycles": len(cycles)}
            return self.store.update(project_id, "graphs", graph_id, done)
        except Exception as e:  # noqa: BLE001 - recorded on the analysis
            _logger.exception("Digital Twin graph %s failed", graph_id)
            message = redact(f"{type(e).__name__}: {e}", 1000)

            def failed(g: GraphAnalysis):
                g.status, g.finished_at, g.error = "failed", now_iso(), message
            return self.store.update(project_id, "graphs", graph_id, failed)

    def is_stale(self, project_id: str, project_dir: Path, graph: Optional[GraphAnalysis] = None) -> bool:
        graph = graph or self.store.latest_graph(project_id)
        return graph is None or graph.fingerprint != project_fingerprint(Path(project_dir))

    # --- simulation ----------------------------------------------------------------------------

    def simulate(self, project_id: str, project_dir: Path, user_id: str, request: str, *,
                 target_files: Optional[List[str]] = None, alternatives: Optional[List[str]] = None,
                 use_model: bool = False, generate: Optional[Callable[[str, str], str]] = None) -> ImpactReport:
        report = ImpactReport(id="imp_" + uuid.uuid4().hex[:12], project_id=project_id, user_id=user_id,
                              request=request.strip()[:2000])
        self.store.put(project_id, "reports", report)
        if use_model and generate is None:
            from backend.services.llm import generate_text

            def generate(system, user):
                return generate_text(system, user, task="planning")
        self._start(project_id, report.id, lambda: self._simulate(
            project_id, report.id, Path(project_dir), target_files, alternatives, generate if use_model else None),
            "reports")
        return self.store.get(project_id, "reports", report.id)

    def _simulate(self, project_id, report_id, project: Path, target_files, alternatives, generate) -> None:
        from backend.twin.simulate import simulate
        self.store.update(project_id, "reports", report_id, lambda r: setattr(r, "status", "running"))
        try:
            graph = self.store.latest_graph(project_id)
            rebuilt = False
            if graph is None or self.is_stale(project_id, project, graph):
                g = GraphAnalysis(id="grf_" + uuid.uuid4().hex[:12], project_id=project_id, user_id="system",
                                  started_at=now_iso())
                self.store.put(project_id, "graphs", g)
                graph, rebuilt = self._build(project_id, g.id, project), True
                if graph is None or graph.status != "completed":
                    raise RuntimeError("the dependency graph could not be built")
            report = self.store.get(project_id, "reports", report_id)
            options, planner, assumptions, limitations, changed = simulate(
                project, graph, report.request, target_files=target_files, alternatives=alternatives,
                generate=generate, history=self._history(project_id))

            def done(r: ImpactReport):
                r.status, r.finished_at = "completed", now_iso()
                r.graph_id, r.graph_stale = graph.id, False
                r.options, r.planner, r.assumptions = options, planner, assumptions
                r.limitations = limitations + (["the graph was rebuilt for this simulation because the project "
                                                "changed since the last analysis"] if rebuilt else [])
                r.files_written = changed
            self.store.update(project_id, "reports", report_id, done)
        except Exception as e:  # noqa: BLE001 - recorded on the report
            _logger.exception("Digital Twin simulation %s failed", report_id)
            message = redact(f"{type(e).__name__}: {e}", 1000)

            def failed(r: ImpactReport):
                r.status, r.finished_at, r.error = "failed", now_iso(), message
            self.store.update(project_id, "reports", report_id, failed)

    def _history(self, project_id: str) -> Dict[str, Any]:
        """Files with open Autopilot findings that show failed validation (syntax, blocking quality errors, tests)."""
        try:
            findings = self.autopilot.store.list(project_id, "findings")
        except Exception:  # noqa: BLE001 - no Autopilot history is a normal state
            return {}
        failing = sorted({f.file for f in findings if f.file and f.status.value in ("open", "planned", "fix_failed")
                          and (f.category.value in ("syntax", "tests") or (f.category.value == "quality"
                                                                             and f.severity.value == "high"))})
        return {"failing_files": failing}

    # --- approval through Autopilot -------------------------------------------------------------------

    def create_plan(self, project_id: str, report_id: str, user_id: str, option: int = 0) -> Plan:
        from backend.evolution.autopilot.plans import PlanError, STRATEGY_AGENT
        report = self.store.get(project_id, "reports", report_id)
        if report is None:
            raise KeyError(report_id)
        if report.status != "completed":
            raise PlanError(f"the report is '{report.status}'")
        if report.plan_id:
            existing = self.autopilot.store.get(project_id, "plans", report.plan_id)
            if existing is not None and existing.status.value in ("awaiting_approval", "approved", "running"):
                raise PlanError(f"plan {report.plan_id} for this report is already {existing.status.value}")
        if not 0 <= option < len(report.options):
            raise PlanError("unknown option")
        pred = report.options[option]
        if not pred.modify_scope and not pred.create_scope:
            raise PlanError("the report has no modification scope; choose the target files and simulate again")
        files = sorted(set(pred.modify_scope) | set(pred.create_scope))
        context = [d["path"] for d in pred.direct][:4]
        request = (f"{pred.request}\n\nImpact analysis: these files depend on the ones you change - keep them "
                   f"working: {', '.join(context) or 'none found'}."
                   + ("\nInterfaces other files use: " + "; ".join(f"{i['symbol']} ({i['file']}, used by "
                                                                    f"{len(i['used_by'])})" for i in pred.interfaces_at_risk[:6])
                      if pred.interfaces_at_risk else ""))
        task = PlanTask(id="t1", title=pred.request[:120], finding_ids=[], files=files, strategy="model",
                        agent=STRATEGY_AGENT["model"], modification=f"Implement the change within: {', '.join(files)}",
                        request=request, context_files=context)
        approval = ["Apply the change to the project after validation"]
        if pred.security_review:
            approval.append("Confirm the security review of this authentication/authorization change")
        plan = Plan(
            id="pln_" + uuid.uuid4().hex[:12], project_id=project_id, user_id=user_id, objective=pred.request[:500],
            finding_ids=[], tasks=[task], expected_files=files, agents=[STRATEGY_AGENT["model"]],
            checks=["python_syntax", "quality_gate", "security_static", "tests"],
            risks=[f"Digital Twin risk: {pred.risk} ({pred.risk_points} points) - "
                   + "; ".join(f.reason for f in pred.risk_factors[:4])] + pred.uncertainties[:3],
            assumptions=["Created from Digital Twin impact report " + report.id + "; files outside the predicted "
                         "scope stop the run for approval and are recorded as unexpected."] + report.assumptions[:2],
            approval_required=approval,
            completion_criteria=["No check regresses against the baseline.",
                                 f"Selected tests: {', '.join(t.path for t in pred.tests[:6]) or 'none found'}"],
            origin="digital_twin", origin_ref=report.id, security_review_required=pred.security_review,
        )
        self.autopilot.store.put(project_id, "plans", plan)
        self.store.update(project_id, "reports", report_id, lambda r: setattr(r, "plan_id", plan.id))
        return plan

    # --- prediction versus reality -------------------------------------------------------------------

    def outcome(self, project_id: str, report_id: str) -> Optional[Outcome]:
        report = self.store.get(project_id, "reports", report_id)
        if report is None:
            raise KeyError(report_id)
        if not report.plan_id:
            return None
        runs = [e for e in self.autopilot.store.list(project_id, "executions") if e.plan_id == report.plan_id]
        finished = [e for e in runs if e.status not in ("queued", "running")]
        if not finished:
            return report.outcome
        latest = max(finished, key=lambda e: e.started_at or "")
        if report.outcome is not None and report.outcome.execution_id == latest.id:
            return report.outcome
        outcome = compare_outcome(report, latest)
        self.store.update(project_id, "reports", report_id, lambda r: setattr(r, "outcome", outcome))
        return outcome

    def accuracy(self, project_id: str) -> Dict[str, Any]:
        rows = []
        for r in self.store.list(project_id, "reports"):
            if r.plan_id:
                try:
                    o = self.outcome(project_id, r.id)
                except KeyError:
                    o = None
                if o is not None:
                    rows.append((r, o))
        scored = [o for _, o in rows if o.precision is not None and o.recall is not None]
        return {
            "compared": len(rows),
            "mean_precision": round(sum(o.precision for o in scored) / len(scored), 3) if scored else None,
            "mean_recall": round(sum(o.recall for o in scored) / len(scored), 3) if scored else None,
            "unexpected_files": sum(len(o.unexpected_files) for _, o in rows),
            "with_validation_failures": sum(1 for _, o in rows if o.validation_failures),
            "note": "precision = predicted files that were changed / all changed files; recall = changed predicted "
                    "files / all predicted files. Based on few, uncontrolled samples; descriptive only.",
            "items": [{"report_id": r.id, "request": r.request[:120], "execution_status": o.execution_status,
                       "precision": o.precision, "recall": o.recall, "unexpected": o.unexpected_files}
                      for r, o in rows],
        }


def compare_outcome(report: ImpactReport, execution) -> Outcome:
    pred = report.options[0] if report.options else None
    predicted = sorted(set(pred.modify_scope)) if pred else []
    folders = tuple(pred.create_scope) if pred else ()
    affected = sorted(set(predicted) | {d["path"] for d in (pred.direct + pred.transitive)}) if pred else []
    scoped = [t for t in execution.task_results if t.status == "out_of_scope"]
    out_of_scope = sorted({f for t in scoped for f in (t.outside or t.files)})
    actual = sorted(set(execution.changed_files) | {f for t in scoped for f in t.files} | set(out_of_scope))
    inside = [f for f in actual if f in predicted or (folders and f.startswith(tuple(d for d in folders if d != "./")))]
    unexpected = sorted(set(actual) - set(inside))
    failures = list((execution.verdict or {}).get("regressions", [])) + list((execution.verdict or {}).get("unverified", []))
    before = {c.check_id: c for c in execution.baseline}
    for c in execution.after:
        if c.status not in ("failed", "error"):
            continue
        counts = f" ({', '.join(f'{k} {v}' for k, v in c.counts.items())})" if c.counts else ""
        b = before.get(c.check_id)
        already = " - already failing before the change" + (
            f" ({', '.join(f'{k} {v}' for k, v in b.counts.items())})" if b.counts else "") \
            if b is not None and b.status in ("failed", "error") else " - new since the change"
        failures.append(f"{c.label}: {c.status}{counts}{already}")
    failures += [f"task {t.task_id}: {t.status} - {t.detail}" for t in execution.task_results if t.status == "failed"]
    limitations = ["Only modified files are compared; whether the predicted dependent files actually broke is shown "
                   "only by the checks, not by this comparison."]
    if execution.status != "completed":
        limitations.append(f"the execution ended '{execution.status}', so the change was not applied; the comparison "
                           "describes the attempted change in the working copy")
    if any(c.check_id == "tests" and c.status not in ("passed", "failed") for c in execution.after):
        limitations.append("tests did not run after the change, so behavioural impact was not observed")
    return Outcome(
        execution_id=execution.id, execution_status=execution.status, predicted_files=predicted,
        predicted_affected=affected, actual_files=actual, out_of_scope_files=out_of_scope, unexpected_files=unexpected,
        predicted_not_changed=sorted(set(predicted) - set(actual)), validation_failures=failures[:30],
        precision=round(len(inside) / len(actual), 3) if actual else None,
        recall=round(len(set(predicted) & set(actual)) / len(predicted), 3) if predicted else None,
        limitations=limitations,
    )


global_twin_service = TwinService()
