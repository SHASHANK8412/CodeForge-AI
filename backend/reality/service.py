"""
AIForge Reality Simulator: a scenario (traffic, resources, dependency latency) is evaluated against an
application model built from real evidence, predicted analytically and - when approved - executed against
isolated copies of the app, then predictions and measurements are compared and recorded for calibration.

  application  Digital Twin routes, outbound-HTTP/database usage (with file:line evidence) and the
               Performance Engineer's static suspicions; unknown facts are listed as unknown
  baseline     a low-load measurement (one request at a time, 3 repetitions) of every endpoint in the mix, in
               the hardened preview container (Performance Engineer runner) -> per-request service times
  predict      analytical.py per alternative (M/M/c with formulas, assumptions and bounds)
  execute      (run_load, approved) per alternative: the open-loop generator (loadgen.py) drives the scenario
               against a fresh container with that alternative's workers / CPU / memory, one alternative at a
               time; dependency-latency alternatives run in the Chaos Engineer's isolated network with its
               controllable stub (normal, then slowed by the scenario's latency)
  compare      predicted vs observed per metric; generator-limited or incompatible runs are not compared;
               comparable pairs become calibration records
  report       bottlenecks labelled measured / model-predicted / static suspicion / insufficient evidence,
               resource needs and (only with user prices) cost, and a recommendation that says what it rests on

v2 (Reality Simulator v2):
  plan         experiment_plan(): the exact workload, containers, limits, timeouts and isolation of a run; a load
               run through the API needs approval of that plan's hash
  probe        a contention probe (probe.py) measures service capacity under concurrency - for the baseline
               configuration, and for every load run in the alternative's own container before its load starts
  predict      model v2 (analytical.predict_v2, measured capacity) next to the raw v1 prediction; calibrated
               values only from validated calibration groups (calibration.py); never labelled as measured
  measure      loadgen v2 metrics (percentiles, timeouts, reliability, the generator measured on its own), cgroup
               CPU usage and throttling (perf runner), verified cleanup
  compare      raw / v2 / calibrated vs observed with absolute and relative errors; only comparable runs (generator
               sustained, errors <= 1%, constant pattern, not cancelled) become calibration records
  findings     evidence-based bottleneck findings (bottlenecks.py)
"""

import logging
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.evolution.autopilot.models import now_iso
from backend.evolution.autopilot.redact import redact
from backend.evolution.autopilot.store import AutopilotStore
from backend.reality import analytical, calibration, loadgen, probe
from backend.reality import bottlenecks as bottlenecks_mod
from backend.reality.models import CalibrationRecord, Scenario, Simulation

_logger = logging.getLogger("aiforge.reality")
CALIBRATION_KEY = "_reality_calibration"
MIN_HISTORY = calibration.MIN_HISTORY
SIM_DEADLINE = 1800
MAX_ERROR_RATE_PCT = 1.0                 # a run with more failed requests is not a calibration observation
PROBE_REQUESTS = 40


class SimulationError(ValueError):
    pass


class Busy(RuntimeError):
    pass


class RealityStore(AutopilotStore):
    KINDS = {"simulations": Simulation, "calibration": CalibrationRecord}
    PRUNE = (("simulations", 50, "created_at"), ("calibration", 2000, "recorded_at"))
    ENV_DIR = "AIFORGE_REALITY_DIR"
    DEFAULT_ROOT = Path(__file__).resolve().parents[1] / "data" / "reality"


def application_model(project: Path) -> Dict[str, Any]:
    """What the simulation knows about the app, each fact with its evidence (Digital Twin + source scan)."""
    import re
    from backend.performance.engineer.static import project_findings
    from backend.twin.graph import build_graph
    b = build_graph(project, deadline_seconds=20)
    routes = [{"endpoint": f"{n.meta.get('method')} {n.meta.get('route')}", "evidence": f"{n.path}:{n.meta.get('line')}",
               "measurable": n.meta.get("method") == "GET" and "{" not in str(n.meta.get("route"))}
              for n in b.nodes.values() if n.type == "route" and n.language == "python"]
    deps, data = [], []
    for p in sorted(Path(project).rglob("*.py")):
        rel = p.relative_to(project).as_posix()
        if any(x in rel.split("/") for x in (".venv", "venv", "node_modules", "tests")) or p.name.startswith("test_"):
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for i, line in enumerate(text.splitlines(), 1):
            if re.search(r"\b(requests|httpx|urllib\.request|aiohttp)\.(get|post|put|delete|request|Client|AsyncClient|urlopen)", line):
                deps.append({"kind": "outbound HTTP", "evidence": f"{rel}:{i}", "code": line.strip()[:120]})
            if re.search(r"\b(sqlite3\.connect|create_engine|psycopg2?\.connect|MongoClient)\b", line):
                data.append({"kind": "database connection", "evidence": f"{rel}:{i}", "code": line.strip()[:120]})
    static, _ = project_findings(Path(project))
    return {"routes": routes, "external_dependencies": deps[:20], "data_access": data[:20],
            "static_suspicions": [{"rule": f["rule_id"], "title": f["title"], "endpoint": f.get("endpoint"),
                                   "evidence": f"{f['file']}:{f['line']}"} for f in static[:20]],
            "unknown": ["background jobs and queues (not detected by the graph)",
                        "production data volume and query plans", "real traffic shape"],
            "verified": "routes and call sites are read from the code; how much traffic each gets is your assumption"}


class RealitySimulator:
    def __init__(self, store: Optional[RealityStore] = None, background: bool = True):
        self.store = store or RealityStore()
        self.background = background
        self._active: Dict[str, str] = {}
        self._lock = threading.Lock()

    # --- lifecycle ----------------------------------------------------------------------------------------------

    @staticmethod
    def experiment_plan(scenario: Scenario, run_load: bool) -> Dict[str, Any]:
        """What a run will do, shown before approval: containers, resources, workload, limits, isolation, cleanup.
        The hash identifies exactly this plan; the API requires it to start a load run."""
        import hashlib
        import json
        from backend.performance.engineer.runner import CONTAINER_TTL_SECONDS, RUN_DEADLINE_SECONDS
        from backend.reality.models import MAX_DURATION, MAX_REQUESTS, MAX_RPS
        tr = scenario.traffic
        peak = max(tr.rps, tr.start_rps if tr.pattern != "constant" else 0)
        steps = [{"step": "baseline", "container": "1 worker, 1 CPU, 1024 MB", "workload": "one request at a time, 3 x 30 "
                  "requests per endpoint + 10 warm-up", "endpoints": list(tr.mix)},
                 {"step": "baseline contention probe", "container": "1 worker, 1 CPU, 1024 MB",
                  "workload": "closed loop at concurrency " + ", ".join(str(c) for c in (1,) + probe.LEVELS)
                              + f", up to {probe.SECONDS_PER_LEVEL:.0f} s each, per endpoint"}]
        if run_load:
            for alt in scenario.alternatives:
                r = alt.resources
                if alt.dependency_latency_ms is not None:
                    steps.append({"step": f"run {alt.id}", "container": f"Chaos sandbox: 1 worker, {min(1.0, r.cpus)} CPU, "
                                  f"{min(1024, r.memory_mb)} MB, internal network, stub '{(scenario.dependency or {}).get('name')}'",
                                  "workload": f"10 probes at concurrency 1 with the dependency normal, 10 with +{alt.dependency_latency_ms} ms"})
                else:
                    steps.append({"step": f"run {alt.id}", "container": f"{r.workers} worker(s), {r.cpus} CPU, {r.memory_mb} MB",
                                  "probe": "contention probe at concurrency " + ", ".join(
                                      str(c) for c in [1] + [k * r.workers for k in probe.LEVELS]) + f" (up to {probe.SECONDS_PER_LEVEL:.0f} s each)",
                                  "workload": f"{tr.pattern} {tr.rps} rps" + (f" (from {tr.start_rps})" if tr.pattern != "constant" else "")
                                  + f" for {tr.duration_seconds} s, at most {int(peak * tr.duration_seconds)} requests, open loop"})
        plan = {"run_load": run_load, "scenario": scenario.name, "steps": steps,
                "limits": {"max_rps": MAX_RPS, "max_duration_s": MAX_DURATION, "max_requests": MAX_REQUESTS,
                           "workers": "1-4", "cpus": "0.25-2", "memory_mb": "128-2048", "request_timeout_s": 10,
                           "max_inflight": loadgen.MAX_INFLIGHT, "simulation_deadline_s": SIM_DEADLINE,
                           "runner_deadline_s": RUN_DEADLINE_SECONDS, "container_ttl_s": CONTAINER_TTL_SECONDS},
                "isolation": ["the app runs from a copy of the project in the hardened preview container (non-root, all capabilities "
                              "dropped, read-only root, CPU/memory/process limits, port on 127.0.0.1 only)",
                              "traffic goes only to containers started for this run - never to a deployed or live service",
                              "dependency alternatives run in the Chaos sandbox's internal network with a stub dependency"],
                "cleanup": "every container and volume of the run is removed after success, failure, cancellation or timeout, "
                           "and the removal is verified"}
        plan["hash"] = hashlib.sha256(json.dumps({k: v for k, v in plan.items() if k != "hash"}, sort_keys=True).encode()).hexdigest()[:16]
        return plan

    def start(self, project_id: str, project: Path, user_id: str, scenario: Scenario, run_load: bool, approved: bool,
              plan_hash: Optional[str] = None) -> Simulation:
        if run_load and not approved:
            raise SimulationError("running the workload starts the app in containers and sends traffic to it: approve it explicitly")
        plan = self.experiment_plan(scenario, run_load)
        if plan_hash is not None and plan_hash != plan["hash"]:
            raise SimulationError("the approved experiment plan differs from this scenario's plan: preview it again and approve it")
        if not scenario.traffic.mix:
            raise SimulationError("the traffic mix is empty: choose the endpoints and their weights")
        if any(a.dependency_latency_ms is not None for a in scenario.alternatives) and run_load and not scenario.dependency:
            raise SimulationError("measuring a dependency-latency alternative needs the dependency stub (name, env var, routes)")
        sim = Simulation(id="rsim_" + uuid.uuid4().hex[:12], project_id=project_id, user_id=user_id, scenario=scenario,
                         run_load=run_load, experiment_plan={**plan, "approved": bool(approved and run_load),
                                                             "approved_hash": plan_hash})
        with self._lock:
            if project_id in self._active:
                raise Busy(f"another simulation ({self._active[project_id]}) is running for this project")
            self._active[project_id] = sim.id
        self.store.put(project_id, "simulations", sim)

        def go():
            try:
                self._run(project_id, sim.id, Path(project))
            finally:
                with self._lock:
                    self._active.pop(project_id, None)
        if self.background:
            threading.Thread(target=go, name=f"reality-{sim.id}", daemon=True).start()
        else:
            go()
        return self.store.get(project_id, "simulations", sim.id)

    def cancel(self, project_id: str, sim_id: str) -> Optional[Simulation]:
        def change(s: Simulation):
            if s.status in ("queued", "running"):
                s.cancel_requested = True
        return self.store.update(project_id, "simulations", sim_id, change)

    def active(self, project_id: str) -> Optional[str]:
        with self._lock:
            return self._active.get(project_id)

    def _stage(self, project_id, sim_id, name, status, detail="") -> None:
        self.store.update(project_id, "simulations", sim_id, lambda s: s.stages.append(
            {"at": now_iso(), "stage": name, "status": status, "detail": redact(detail, 400)}))

    # --- the run ------------------------------------------------------------------------------------------------------

    def _run(self, project_id: str, sim_id: str, project: Path) -> None:
        from backend.evolution_engine.service import source_revision
        deadline = time.monotonic() + SIM_DEADLINE

        def stop() -> bool:
            s = self.store.get(project_id, "simulations", sim_id)
            return bool(s and s.cancel_requested) or time.monotonic() > deadline
        self.store.update(project_id, "simulations", sim_id, lambda s: setattr(s, "status", "running"))
        try:
            sim = self.store.get(project_id, "simulations", sim_id)
            sc = sim.scenario
            rev = source_revision(project)
            self._stage(project_id, sim_id, "application model", "running")
            app = application_model(project)
            known = {r["endpoint"] for r in app["routes"]}
            unknown = [e for e in sc.traffic.mix if e not in known]
            limitations = [f"{e} is not in the Digital Twin graph (a router prefix from another file?); it is measured "
                           "only if it answers" for e in unknown]
            self.store.update(project_id, "simulations", sim_id, lambda s: (setattr(s, "application", app), setattr(s, "revision", rev)))
            self._stage(project_id, sim_id, "application model", "done", f"{len(app['routes'])} routes")
            if stop():
                raise InterruptedError()
            # 1. baseline service times
            self._stage(project_id, sim_id, "baseline (low load)", "running")
            baseline = self._baseline(project, list(sc.traffic.mix), stop)
            self.store.update(project_id, "simulations", sim_id, lambda s: setattr(s, "baseline", baseline))
            self._stage(project_id, sim_id, "baseline (low load)", "done" if baseline["status"] == "measured" else "failed",
                        baseline.get("error") or ", ".join(f"{k}: {v['median_ms']} ms" for k, v in baseline["endpoints"].items()))
            # 2. predictions
            predictions, costs, predictions_v2 = {}, {}, {}
            if baseline["status"] == "measured":
                for alt in sc.alternatives:
                    p = analytical.predict(baseline, sc.traffic.mix, sc.traffic.rps, alt.resources.workers, alt.resources.cpus,
                                           alt.dependency_latency_ms, sc.dependent_endpoints, sc.traffic.duration_seconds)
                    if p["status"] == "predicted" and sc.traffic.pattern != "constant":
                        p["saturation_onset_s"] = analytical.saturation_onset(sc.traffic.model_dump(), p["capacity_rps"])
                        p["pattern_note"] = (f"the model is evaluated at the peak rate ({sc.traffic.rps} rps); the onset is when "
                                             "the offered rate first exceeds the predicted capacity")
                    if p["status"] == "predicted" and alt.dependency_latency_ms is None:
                        p["calibrated"] = self.calibrated(p)
                    p["predicted_at"] = now_iso()
                    predictions[alt.id] = p
                    if alt.dependency_latency_ms is None:
                        predictions_v2[alt.id] = self._predict_v2(sc, alt, baseline,
                                                                  probe.scaled_from_baseline(baseline.get("contention_probe"),
                                                                                             alt.resources.workers, alt.resources.cpus),
                                                                  "before any run: the baseline probe scaled to this configuration")
                    if p["status"] == "predicted":
                        costs[alt.id] = analytical.cost(p, baseline, sc.prices.model_dump() if sc.prices else None,
                                                        sc.target_utilization, sc.traffic.rps)
            else:
                limitations.append("no baseline could be measured, so nothing could be predicted: " + (baseline.get("error") or ""))
            self.store.update(project_id, "simulations", sim_id, lambda s: (setattr(s, "predictions", predictions), setattr(s, "costs", costs),
                                                                            setattr(s, "predictions_v2", dict(predictions_v2))))
            # 3. execution
            measurements: Dict[str, Any] = {}
            if sim.run_load and baseline["status"] == "measured":
                for alt in sc.alternatives:
                    if stop():
                        raise InterruptedError()
                    self._stage(project_id, sim_id, f"run {alt.id}", "running")
                    if alt.dependency_latency_ms is not None:
                        measurements[alt.id] = self._dependency_run(project, sc, alt, baseline, stop)
                    else:
                        measurements[alt.id] = self._load_run(project, sc, alt, stop, baseline)
                        informed = measurements[alt.id].pop("probe_prediction", None)
                        if informed:
                            informed["superseded"] = {k: (predictions_v2.get(alt.id) or {}).get(k) for k in ("stage", "mean_ms", "throughput_rps")}
                            predictions_v2[alt.id] = informed
                    self.store.update(project_id, "simulations", sim_id, lambda s, m=dict(measurements), v=dict(predictions_v2): (
                        setattr(s, "measurements", m), setattr(s, "predictions_v2", v)))
                    self._stage(project_id, sim_id, f"run {alt.id}", "done" if measurements[alt.id].get("status") == "measured" else "failed",
                                measurements[alt.id].get("error") or "")
            elif not sim.run_load:
                limitations.append("predictions only: the workload was not executed, so nothing here is measured under load")
            # 4. compare, calibrate, analyse
            comparisons = {aid: self._compare(project_id, sim_id, rev, sc, aid, predictions.get(aid), m, baseline,
                                              predictions_v2.get(aid))
                           for aid, m in measurements.items()}
            bottlenecks = self._bottlenecks(sc, app, baseline, predictions, measurements)
            findings = [f for alt in sc.alternatives if alt.id in measurements
                        for f in bottlenecks_mod.detect(alt.id, alt.resources.model_dump(),
                                                        sc.traffic.rps if sc.traffic.pattern == "constant" else None,
                                                        measurements[alt.id], predictions.get(alt.id), predictions_v2.get(alt.id),
                                                        alt.dependency_latency_ms)]
            rec = self._recommend(sc, predictions, measurements, costs)
            self.store.update(project_id, "simulations", sim_id, lambda s: (
                setattr(s, "comparisons", comparisons), setattr(s, "bottlenecks", bottlenecks), setattr(s, "recommendation", rec),
                setattr(s, "findings", findings),
                setattr(s, "limitations", limitations), setattr(s, "status", "completed"),
                setattr(s, "finished_at", now_iso())))
        except InterruptedError:
            self.store.update(project_id, "simulations", sim_id, lambda s: (
                setattr(s, "status", "cancelled"), setattr(s, "finished_at", now_iso()),
                setattr(s, "error", "cancelled (by the user or the time limit); partial results are kept and labelled")))
        except Exception as e:  # noqa: BLE001
            _logger.exception("Reality simulation %s failed", sim_id)
            msg = redact(f"{type(e).__name__}: {e}", 800)
            self.store.update(project_id, "simulations", sim_id, lambda s: (
                setattr(s, "status", "failed"), setattr(s, "error", msg), setattr(s, "finished_at", now_iso())))
        finally:
            s = self.store.get(project_id, "simulations", sim_id)
            from backend.time_machine.recorder import emit
            emit(project_id, "performance_measured", "Reality Simulator",
                 f"simulation '{s.scenario.name}' {s.status}" + (" (predictions only)" if not s.run_load else ""),
                 "success" if s.status == "completed" else "error" if s.status == "failed" else "cancelled",
                 task_id=sim_id, refs={"simulation_id": sim_id}, project_dir=project,
                 data={"predictions": {k: {m: v.get(m) for m in ("utilization", "throughput_rps", "mean_ms", "p95_ms")}
                                       for k, v in s.predictions.items() if isinstance(v, dict)},
                       "measured": {k: {m: v.get(m) for m in ("throughput_rps", "mean_ms", "p95_ms", "error_rate_pct")}
                                    for k, v in s.measurements.items()}},
                 config={"scenario": s.scenario.model_dump()})

    # --- measurements -------------------------------------------------------------------------------------------------

    def _baseline(self, project: Path, mix: List[str], stop) -> Dict[str, Any]:
        from backend.performance.engineer import runner
        from backend.performance.engineer.models import Endpoint, Workload
        load = Workload(endpoints=[Endpoint(method="GET", path=e.split(" ", 1)[1]) for e in mix], requests_per_endpoint=30,
                        concurrency=1, warmup_requests=10, repetitions=3, max_seconds_per_endpoint=30)
        res, env = runner.measure({"baseline": project}, load, stop, resources={"workers": 1, "cpus": 1.0, "memory_mb": 1024})
        m = res["baseline"]
        if m.status != "measured":
            return {"status": m.status, "error": m.error, "endpoints": {}}
        return {"status": "measured", "label": "measured: one request at a time, 3 repetitions, 1 worker / 1 CPU",
                "endpoints": {f"{e.method} {e.path}": {"median_ms": e.median_ms, "p95_ms": e.p95_ms, "mean_ms": e.mean_ms,
                                                       "rep_medians_ms": e.rep_medians_ms, "requests": e.requests,
                                                       "error_rate_pct": e.error_rate_pct} for e in m.endpoints},
                "peak_memory_mb": m.resources.mem_max_mb, "environment": env.model_dump(), "run_id": f"baseline@{now_iso()}",
                "resources": {"workers": 1, "cpus": 1.0}, "contention_probe": self._baseline_probe(project, mix, stop)}

    def _baseline_probe(self, project: Path, mix: List[str], stop) -> Optional[Dict[str, Any]]:
        """The contention probe in the baseline configuration (1 worker, 1 CPU); None (and the reason) if it fails."""
        from backend.performance.engineer import runner
        from backend.performance.engineer.models import Workload
        try:
            res, env = runner.measure({"probe": project}, Workload(), stop, resources={"workers": 1, "cpus": 1.0, "memory_mb": 1024},
                                      drive=lambda url, st: probe.contention_probe(url, mix, 1, st, PROBE_REQUESTS))
            m = res["probe"]
            if m.status != "measured":
                return {"status": m.status, "error": m.error, "endpoints": {}}
            return {**m.custom, "status": "measured", "cleanup": env.cleanup}
        except Exception as e:  # noqa: BLE001 - the v2 model then reports insufficient evidence
            return {"status": "unavailable", "error": redact(f"{type(e).__name__}: {e}", 300), "endpoints": {}}

    def _predict_v2(self, sc: Scenario, alt, baseline: Dict[str, Any], pr: Optional[Dict[str, Any]], stage: str) -> Dict[str, Any]:
        usable = pr if pr and pr.get("status", "measured") == "measured" and pr.get("endpoints") else None
        p = analytical.predict_v2(baseline, sc.traffic.mix, sc.traffic.rps, alt.resources.workers, alt.resources.cpus,
                                  None, sc.dependent_endpoints, sc.traffic.duration_seconds, usable)
        if p.get("status") == "predicted":
            if sc.traffic.pattern != "constant":
                p["saturation_onset_s"] = analytical.saturation_onset(sc.traffic.model_dump(), p["capacity_rps"])
            p["calibrated"] = self.calibrated(p)
            p["calibration_groups"] = {m: calibration.group_key(p, m) for m in ("throughput_rps", "mean_ms", "p95_ms")}
        elif pr and pr.get("error"):
            p["reason"] = f"{p.get('reason')}: {pr['error']}"
        p.update(stage=stage, predicted_at=now_iso())
        return p

    def _load_run(self, project: Path, sc: Scenario, alt, stop, baseline: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        from backend.performance.engineer import runner
        from backend.performance.engineer.models import Workload
        traffic = sc.traffic.model_dump()
        state: Dict[str, Any] = {}

        def pre(url, st):
            # in this alternative's container, before its load: measure capacity under concurrency, then predict
            state["probe"] = probe.contention_probe(url, list(sc.traffic.mix), alt.resources.workers, st, PROBE_REQUESTS)
            if baseline:
                state["prediction"] = self._predict_v2(sc, alt, baseline, state["probe"],
                                                       "before the load: probe measured in this configuration")
            return state["probe"]
        res, env = runner.measure({alt.id: project}, Workload(), stop, resources=alt.resources.model_dump(),
                                  drive=lambda url, should_stop: loadgen.run(url, traffic, should_stop), pre_drive=pre)
        m = res[alt.id]
        if m.status != "measured":
            return {"status": m.status, "error": m.error, "cleanup": env.cleanup}
        custom = dict(m.custom)
        out = {"status": "measured", **custom, "resources": m.resources.model_dump(), "cpu_stat": m.cpu_stat,
               "contention_probe": custom.pop("pre_drive", state.get("probe")), "probe_prediction": state.get("prediction"),
               "container": alt.resources.model_dump(), "environment": env.model_dump(), "cleanup": env.cleanup}
        out.pop("pre_drive", None)
        out["provenance"] = {**(out.get("provenance") or {}),
                             "cpu_stat": m.cpu_stat.get("source") if m.cpu_stat.get("available") else
                             f"unavailable: {m.cpu_stat.get('reason', 'not collected')}",
                             "resources": m.resources.method if m.resources.samples else "unavailable: docker stats returned no samples",
                             "contention_probe": "closed-loop probe in this container before the load"}
        if m.custom.get("cancelled"):
            out["status"] = "cancelled"
        return out

    def _dependency_run(self, project: Path, sc: Scenario, alt, baseline, stop) -> Dict[str, Any]:
        """Low-load probes in the Chaos sandbox with the stub normal, then slowed by the scenario's latency."""
        from backend.chaos.models import AssessmentConfig, DependencySpec, Limits, Target
        from backend.chaos.sandbox import Sandbox, SandboxError
        targets = [Target(path=e.split(" ", 1)[1]) for e in sc.dependent_endpoints]
        cfg = AssessmentConfig(scenarios=["dependency_slow"], dependencies=[DependencySpec(**sc.dependency)],
                               limits=Limits(cpus=min(1.0, alt.resources.cpus), memory_mb=min(1024, alt.resources.memory_mb)))
        sb = Sandbox(project, cfg, "reality")
        try:
            sb.setup()
            health = Target(path=targets[0].path)
            if sb.wait_healthy(health, 60) is None:
                raise SandboxError("the app did not answer in the sandbox")
            normal = sb.probe(targets, count=10, concurrency=1)
            sb.control(sc.dependency["name"], "slow", delay_ms=int(alt.dependency_latency_ms))
            slow = sb.probe(targets, count=10, concurrency=1)

            def stats(rows):
                ok = [r["ms"] for r in rows if r.get("status") and r["status"] < 400]
                return {"mean_ms": round(sum(ok) / len(ok), 2) if ok else None, "ok": len(ok), "total": len(rows),
                        "statuses": sorted({str(r.get("status") or r.get("error")) for r in rows})}
            return {"status": "measured", "label": "measured in the Chaos Engineer sandbox (low load, concurrency 1)",
                    "normal": stats(normal), "slowed": stats(slow), "added_latency_ms": alt.dependency_latency_ms,
                    "note": "measured at low load; workers are fixed at 1 in the chaos sandbox"}
        except (SandboxError, Exception) as e:  # noqa: BLE001
            return {"status": "unavailable", "error": redact(f"{type(e).__name__}: {e}", 400)}
        finally:
            sb.cleanup()

    # --- comparison, calibration, analysis ---------------------------------------------------------------------------

    def _compare(self, project_id, sim_id, rev, sc: Scenario, aid: str, pred: Optional[Dict[str, Any]], meas: Dict[str, Any],
                 baseline: Dict[str, Any], pred_v2: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        alt = next(a for a in sc.alternatives if a.id == aid)
        context = {"resources": alt.resources.model_dump(), "workload": sc.traffic.model_dump(),
                   "generator_sustained": (meas.get("generator") or {}).get("sustained", not meas.get("generator_limited")),
                   "generator_reasons": (meas.get("generator") or {}).get("reasons", [])}
        if meas.get("status") != "measured" or (alt.dependency_latency_ms is None and (not pred or pred.get("status") != "predicted")):
            return {"comparable": False, "reason": "a prediction or a measurement is missing", **context}
        pred = pred or {"method": "additive dependency latency", "inputs": {}, "saturated": False}
        rows, rows_v2, records = [], [], []
        if alt.dependency_latency_ms is not None:
            # the measurement ran at low load: compare with the model's no-queue response time for those conditions
            # the endpoint needs the stub, so its latency with the dependency at normal speed is measured in the same
            # sandbox run; the model predicts the slowed latency as that plus the added (waiting) latency D
            normal = (meas.get("normal") or {}).get("mean_ms")
            observed = (meas.get("slowed") or {}).get("mean_ms")
            if normal is None or observed is None:
                return {"comparable": False, "reason": "no successful request with the dependency normal and slowed", **context}
            rows.append(self._row("dependency_mean_ms", round(normal + alt.dependency_latency_ms, 2), None, observed,
                                  "measured latency with the dependency at normal speed + D (low load, no queueing)"))
        else:
            if meas.get("generator_limited"):
                return {"comparable": False, "reason": "the load generator itself fell behind or dropped requests: the run "
                                                       "does not show the app's limits, so it is not compared", **context}
            if meas.get("cancelled"):
                return {"comparable": False, "reason": "the run was cancelled before it finished", **context}
            if (meas.get("error_rate_pct") or 0) > MAX_ERROR_RATE_PCT:
                return {"comparable": False, "reason": f"{meas.get('error_rate_pct')}% of requests failed (> {MAX_ERROR_RATE_PCT}%): an "
                                                       "overloaded or failing run is not a calibration observation",
                        "observed": {k: meas.get(k) for k in ("throughput_rps", "mean_ms", "p95_ms", "error_rate_pct", "timeouts")},
                        **context}
            if sc.traffic.pattern != "constant":
                obs_onset = next((t["second"] for t in meas["timeline"]
                                  if t["p50_ms"] and t["p50_ms"] > 2 * pred["mean_service_ms"] or t["errors"]), None)
                return {"comparable": False, "reason": "ramp/burst runs are compared by the saturation onset only",
                        "onset": {"predicted_s": pred.get("saturation_onset_s"),
                                  "predicted_v2_s": (pred_v2 or {}).get("saturation_onset_s"), "observed_s": obs_onset}, **context}
            for model, p_, target in (("raw", pred, rows), ("v2", pred_v2, rows_v2)):
                if not p_ or p_.get("status") != "predicted":
                    continue
                for k in ["throughput_rps"] + ([] if p_.get("saturated") else ["mean_ms", "p95_ms"]):
                    if p_.get(k) is None or meas.get(k) is None:
                        continue
                    lo, hi = (p_["bounds"].get(k) or [None, None])
                    r = self._row(k, p_[k], (lo, hi), meas[k], p_["method"])
                    r["calibrated"] = ((p_.get("calibrated") or {}).get(k) or {}).get("value")
                    if r["calibrated"] is not None:
                        r["calibrated_error_pct"] = round((meas[k] - r["calibrated"]) / r["calibrated"] * 100, 1)
                    r["model"] = model
                    target.append(r)
        key_base = f"{'dependency' if alt.dependency_latency_ms is not None else 'load'}|{'saturated' if pred.get('saturated') else 'stable'}"
        groups = {}
        for model, p_, rs in (("raw", pred, rows), ("v2", pred_v2, rows_v2)):
            for r in rs:
                if alt.dependency_latency_ms is not None:
                    key, version = f"{pred['method']}|{r['metric']}|{key_base}", analytical.MODEL_VERSION_RAW
                else:
                    key, version = calibration.group_key(p_, r["metric"]), p_.get("model_version", analytical.MODEL_VERSION_RAW)
                rec = CalibrationRecord(id="cal_" + uuid.uuid4().hex[:10], project_id=project_id, simulation_id=sim_id, alternative=aid,
                                        method=(p_ or pred)["method"], metric=r["metric"], revision=rev, inputs=(p_ or pred)["inputs"],
                                        predicted=r["predicted"], low=r["low"], high=r["high"], observed=r["observed"],
                                        error_pct=r["error_pct"], within_bounds=r["within_bounds"], comparable_key=key,
                                        model_version=version, kind=model, absolute_error=round(r["observed"] - r["predicted"], 3),
                                        relative_error=round((r["observed"] - r["predicted"]) / r["predicted"], 4) if r["predicted"] else None,
                                        calibration_method=calibration.CALIBRATION_METHOD,
                                        group={"workers": alt.resources.workers, "cpus": alt.resources.cpus,
                                               "band": calibration.band(p_ or pred), "state": key_base},
                                        predicted_at=(p_ or pred).get("predicted_at"))
                self.store.put(CALIBRATION_KEY, "calibration", rec)
                records.append(rec.id)
                groups[f"{model}:{r['metric']}"] = key
        explanation = self._explain(rows + rows_v2, meas, pred_v2)
        group_state = {}
        for name, key in groups.items():
            ev = calibration.evaluate([{"predicted": x.predicted, "observed": x.observed}
                                       for x in self.store.list(CALIBRATION_KEY, "calibration") if x.comparable_key == key])
            group_state[name] = {"key": key, "records": ev["records"], "established": ev["established"],
                                 "correction_applied": ev.get("applied", False)}
        return {"comparable": True, "rows": rows, "rows_v2": rows_v2, "calibration_records": records, "groups": group_state,
                "explanation": explanation or ["every compared metric fell within the prediction's bounds or its error is shown"],
                **context}

    @staticmethod
    def _explain(rows: List[Dict[str, Any]], meas: Dict[str, Any], pred_v2: Optional[Dict[str, Any]]) -> List[str]:
        """Discrepancies explained only with what was measured and the models' stated assumptions."""
        cs = meas.get("cpu_stat") or {}
        observed_facts = []
        if cs.get("available"):
            if cs.get("throttled_ratio") is not None:
                observed_facts.append(f"the kernel throttled the container in {cs['throttled_ratio']:.0%} of CPU periods "
                                      f"({cs.get('throttled_ms')} ms)")
            if cs.get("cpu_utilization_of_limit") is not None:
                observed_facts.append(f"CPU use was {cs['cpu_utilization_of_limit']:.0%} of the limit (cgroup)")
        effs = {k: v["efficiency"] for k, v in ((meas.get("contention_probe") or {}).get("endpoints") or {}).items() if v.get("available")}
        if effs:
            observed_facts.append(f"the contention probe measured an efficiency of {min(effs.values())} under concurrency")
        gen = meas.get("generator") or {}
        if gen.get("process_cpu_pct_of_one_core") is not None:
            observed_facts.append(f"the generator process used {gen['process_cpu_pct_of_one_core']}% of one core on the same host")
        out = []
        for r in rows:
            if r["within_bounds"]:
                continue
            side = "optimistic (observed is higher)" if r["observed"] > r["predicted"] else "pessimistic (observed is lower)"
            if r["metric"] == "throughput_rps":
                side = "optimistic (observed is lower)" if r["observed"] < r["predicted"] else "pessimistic (observed is higher)"
            assumption = ("v1 assumes the CPU limit is shared perfectly (speed = cpus / workers)" if r.get("model") == "raw" else
                          "v2 assumes the probe's capacity (2 x workers concurrency) holds at the scenario's load")
            out.append(f"[{r.get('model', 'raw')}] {r['metric']}: predicted {r['predicted']} vs observed {r['observed']} "
                       f"({r['error_pct']:+}%), the model was {side}. Observed: {'; '.join(observed_facts) or 'no resource counters'}. "
                       f"Assumption at stake: {assumption}.")
        return out

    @staticmethod
    def _row(metric, predicted, bounds, observed, how) -> Dict[str, Any]:
        lo, hi = bounds if bounds else (None, None)
        err = round((observed - predicted) / predicted * 100, 1) if predicted else 0.0
        within = (lo is not None and hi is not None and lo <= observed <= hi) or abs(err) <= 10
        return {"metric": metric, "predicted": predicted, "low": lo, "high": hi, "observed": observed, "error_pct": err,
                "within_bounds": within, "how": how}

    def calibrated(self, pred: Dict[str, Any]) -> Dict[str, Any]:
        """Calibrated values for a new prediction: model x the validated correction of its calibration group (same
        model, method, metric, state, workers, CPU limit and utilisation band). A group needs MIN_HISTORY comparable
        runs AND a correction that lowered the held-out (leave-one-out) error; otherwise there is no calibrated value."""
        recs = self.store.list(CALIBRATION_KEY, "calibration")
        out: Dict[str, Any] = {}
        for metric in ("throughput_rps", "mean_ms", "p95_ms"):
            if pred.get(metric) is None:
                continue
            key = calibration.group_key(pred, metric)
            ev = calibration.evaluate([{"predicted": r.predicted, "observed": r.observed} for r in recs if r.comparable_key == key])
            c = calibration.correct(pred[metric], ev)
            c.update(group=key, records=ev.get("records", 0), established=ev.get("established", False),
                     bias_pct=ev.get("bias_pct"), loo_mean_abs_error_pct=ev.get("loo_mean_abs_error_pct"),
                     raw_mean_abs_error_pct=ev.get("raw_mean_abs_error_pct"))
            if c["value"] is not None:
                c["note"] += "; an empirical correction for this machine, still an estimate"
            out[metric] = c
        return out

    def calibration(self, method: Optional[str] = None) -> Dict[str, Any]:
        recs = self.store.list(CALIBRATION_KEY, "calibration")
        groups: Dict[str, List[CalibrationRecord]] = {}
        for r in recs:
            if method and r.method != method:
                continue
            groups.setdefault(r.comparable_key, []).append(r)
        out = []
        for key, rs in sorted(groups.items()):
            n = len(rs)
            ev = calibration.evaluate([{"predicted": r.predicted, "observed": r.observed} for r in rs])
            out.append({"key": key, "records": n, "model_version": rs[-1].model_version, "kind": rs[-1].kind,
                        "legacy": rs[-1].calibration_method is None,
                        "mean_abs_error_pct": round(sum(abs(r.error_pct) for r in rs) / n, 1),
                        "within_bounds_pct": round(100 * sum(r.within_bounds for r in rs) / n, 1),
                        "bias_pct": ev.get("bias_pct"), "established": ev["established"],
                        "loo_mean_abs_error_pct": ev.get("loo_mean_abs_error_pct"), "correction_validated": ev.get("validated", False),
                        "factor": ev.get("factor"), "evaluation": ev.get("note"),
                        "assessment": "insufficient history" if n < MIN_HISTORY else "measured accuracy",
                        "last": rs[-1].recorded_at})
        return {"groups": out, "method": calibration.CALIBRATION_METHOD,
                "note": f"only records with the same key are combined; fewer than {MIN_HISTORY} records do not support any claim "
                        "about accuracy; a correction's accuracy is measured on held-out runs only (leave-one-out)"}

    def _bottlenecks(self, sc, app, baseline, predictions, measurements) -> List[Dict[str, Any]]:
        out = []
        for aid, m in measurements.items():
            if m.get("status") != "measured" or "throughput_rps" not in m:
                continue
            offered = sc.traffic.rps if sc.traffic.pattern == "constant" else None
            if offered and not m.get("generator_limited") and m["throughput_rps"] < 0.9 * offered * (m["sent"] / max(1, m["planned_requests"])):
                out.append({"label": "measured bottleneck", "alternative": aid,
                            "detail": f"served {m['throughput_rps']} of {offered} rps offered"})
            if (m.get("error_rate_pct") or 0) > 1:
                out.append({"label": "measured bottleneck", "alternative": aid, "detail": f"error rate {m['error_rate_pct']}% ({m['status_codes']})"})
            cpu, limit = (m.get("resources") or {}).get("cpu_avg_pct"), m["container"]["cpus"] * 100
            if cpu is not None and cpu >= 0.85 * limit:
                out.append({"label": "measured bottleneck", "alternative": aid, "detail": f"CPU {cpu}% of a {limit:.0f}% limit (docker stats)"})
        for aid, p in predictions.items():
            if p.get("status") != "predicted":
                out.append({"label": "insufficient evidence", "alternative": aid, "detail": p.get("reason")})
            elif p["utilization"] >= 0.85:
                out.append({"label": "model-predicted bottleneck", "alternative": aid,
                            "detail": f"predicted utilisation {p['utilization']} (capacity {p['capacity_rps']} rps)"})
            if p.get("threadpool_saturated"):
                out.append({"label": "model-predicted bottleneck", "alternative": aid, "detail": "threadpool saturation (dependency waits)"})
        for s in app.get("static_suspicions", []):
            if s.get("endpoint") in sc.traffic.mix:
                out.append({"label": "static-analysis suspicion", "detail": f"{s['title']} ({s['evidence']})", "endpoint": s["endpoint"]})
        return out

    def _recommend(self, sc, predictions, measurements, costs) -> Dict[str, Any]:
        cands = []
        for alt in sc.alternatives:
            m, p = measurements.get(alt.id) or {}, predictions.get(alt.id) or {}
            measured = m.get("status") == "measured" and "mean_ms" in m and not m.get("generator_limited")
            if measured and (m.get("error_rate_pct") or 0) <= 1:
                cands.append((m["mean_ms"], alt.resources.workers * alt.resources.cpus, alt.id, "measured"))
            elif not measured and p.get("status") == "predicted" and not p.get("saturated"):
                cands.append((p["mean_ms"], alt.resources.workers * alt.resources.cpus, alt.id, "predicted"))
        if not cands:
            return {"recommendation": None, "basis": "none", "reason": "no alternative met the scenario without saturating or "
                                                                    "errors; consider code changes (Evolution Engine)"}
        best = min(c[0] for c in cands)
        # among alternatives within 10% of the best latency, prefer the one using the fewest resources
        choice = sorted([c for c in cands if c[0] <= best * 1.1], key=lambda c: (c[1], c[0]))[0]
        exps = []
        if choice[3] == "predicted":
            exps.append("run the workload (approved) to measure this alternative before relying on it")
        return {"recommendation": choice[2], "basis": choice[3], "mean_ms": choice[0],
                "reason": f"{'measured' if choice[3] == 'measured' else 'predicted'} mean latency {choice[0]} ms, within 10% of the "
                          "best, with the fewest workers x CPUs", "cost": costs.get(choice[2]),
                "recommended_experiments": exps + ["code-level changes (caching, queries) are evaluated with the Evolution Engine"]}


global_reality_simulator = RealitySimulator()
