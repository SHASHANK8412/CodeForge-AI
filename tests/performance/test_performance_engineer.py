"""
AIForge Performance Engineer: static findings, measurement parsing, workload execution, baseline,
plans, approval, the correctness and performance gates, rollback, cancellation, reports, security.

Container runs are replaced by recorded/mock measurements here (no improvement is claimed from
them); the load generator is exercised against a real local HTTP server.
"""

import http.server
import json
import threading
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.evolution.autopilot.plans import PlanError as AutopilotPlanError
from backend.evolution.autopilot.service import AutopilotService
from backend.evolution.autopilot.store import AutopilotStore
from backend.performance.engineer import gate, runner, static
from backend.performance.engineer.models import (Endpoint, EndpointStats, Measurement, Resources, Thresholds,
                                                 Workload)
from backend.performance.engineer.service import PerfStore, PerformanceEngineer, PlanError
from backend.performance.engineer.workload import percentile, run_endpoint, summarize

from tests.performance.sample_project import write_sample

SECRET = "sk-" + "abcdefghijklmnopqrstuvwxyz0123456789"


@pytest.fixture
def sample(tmp_path):
    return write_sample(tmp_path / "shop")


@pytest.fixture
def services(tmp_path, monkeypatch):
    ap = AutopilotService(AutopilotStore(tmp_path / "ap"), background=False)
    pe = PerformanceEngineer(PerfStore(tmp_path / "perf"), autopilot=ap, background=False)
    import backend.performance.engineer.service as svc_module
    monkeypatch.setattr(svc_module, "global_performance_engineer", pe)   # the executor's gate uses it
    return ap, pe


def stats(path, medians, method="GET", errors=0, requests=100, rps=None):
    """Endpoint statistics with the given per-repetition medians (mock data for unit tests)."""
    med = sorted(medians)[len(medians) // 2]
    spread = round((max(medians) - min(medians)) / med * 100, 2) if len(medians) > 1 else None
    return EndpointStats(method=method, path=path, requests=requests, errors=errors,
                         error_rate_pct=round(errors / requests * 100, 3), median_ms=med, p95_ms=med * 1.5,
                         mean_ms=med, throughput_rps=rps or round(1000 / med * 4, 2), rep_medians_ms=medians,
                         spread_pct=spread)


def measurement(label, endpoints, mem=60.0, status="measured"):
    return Measurement(label=label, status=status, startup_seconds=2.0, readiness_probe="GET /health -> 200",
                       endpoints=endpoints, resources=Resources(samples=10, cpu_avg_pct=50, cpu_max_pct=90,
                                                                mem_avg_mb=mem, mem_max_mb=mem))


def fake_measure(results_by_label):
    """A stand-in for runner.measure returning prepared measurements."""
    def measure(projects, workload, should_stop=None, on_stage=None):
        if not workload.endpoints:
            workload.endpoints = [Endpoint(path="/api/orders"), Endpoint(path="/health")]
        return {label: results_by_label[label].model_copy(deep=True) for label in projects}, runner.environment(workload)
    return measure


SLOW = measurement("baseline", [stats("/api/orders", [2000.0, 2050.0, 2030.0]), stats("/health", [2.1, 2.0, 2.2])])


# 1 ------------------------------------------------------------------------------------------------
@pytest.fixture
def api(tmp_path, sample, monkeypatch, services):
    import backend.performance.routes as routes
    import backend.routes.export as export
    from backend.auth.dependencies import get_current_user
    from backend.generation.store import global_generation_store
    ap, pe = services
    monkeypatch.setattr(routes, "global_performance_engineer", pe)
    records = {
        "gen_mine": {"generation_id": "gen_mine", "user_id": "alice", "status": "completed", "project_path": str(sample)},
        "gen_theirs": {"generation_id": "gen_theirs", "user_id": "bob", "status": "completed", "project_path": str(sample)},
        "gen_paused": {"generation_id": "gen_paused", "user_id": "alice", "status": "waiting_for_approval",
                       "project_path": str(sample)},
    }
    monkeypatch.setattr(global_generation_store, "get", lambda gid, default=None: records.get(gid, default))
    monkeypatch.setattr(export, "_safe_project_dir", lambda p: sample if p == str(sample) else None)
    app = FastAPI()
    app.include_router(routes.performance_router)
    from backend.evolution.routes import autopilot_evolution_router
    import backend.evolution.routes as ev_routes
    monkeypatch.setattr(ev_routes, "global_autopilot_service", ap)
    app.include_router(autopilot_evolution_router)
    app.dependency_overrides[get_current_user] = lambda: {"id": "alice"}
    return TestClient(app)


def test_project_access_is_validated(api):
    assert api.post("/api/projects/gen_theirs/performance/analyses", json={}).status_code == 403
    assert api.get("/api/projects/missing/performance/findings").status_code == 404
    assert api.get("/api/projects/..%2F..%2Fx/performance/findings").status_code == 404


# 2 ------------------------------------------------------------------------------------------------
def test_static_bottlenecks_are_detected_and_labelled(sample):
    (sample / "backend/slow.py").write_text(
        "import time, json, requests\nfrom fastapi import APIRouter\nrouter = APIRouter(prefix='/x')\n\n"
        "@router.get('/a')\nasync def a(db):\n    time.sleep(1)\n    db.query(1).all()\n    db.query(1).all()\n"
        "    return requests.get('http://upstream')\n", encoding="utf-8")
    (sample / "frontend/src").mkdir(parents=True)
    (sample / "frontend/src/List.jsx").write_text(
        "import { useEffect, useState } from 'react'\nexport default function List() {\n  const [x, setX] = useState([])\n"
        "  useEffect(() => { fetch('/api/orders').then(r => r.json()).then(setX) })\n  return null\n}\n", encoding="utf-8")
    (sample / "frontend/package.json").write_text(json.dumps({"dependencies": {"moment": "2"}}), encoding="utf-8")
    found, _ = static.project_findings(sample)
    rules = {(f["rule_id"], f["file"]) for f in found}
    assert ("PERF-N-PLUS-ONE", "backend/main.py") in rules and ("PERF-NO-PAGINATION", "backend/main.py") in rules
    assert ("PERF-BLOCKING-ASYNC", "backend/slow.py") in rules and ("PERF-REPEATED-QUERY", "backend/slow.py") in rules
    assert ("PERF-NO-CACHE", "backend/slow.py") in rules
    assert ("PERF-EFFECT-NO-DEPS", "frontend/src/List.jsx") in rules and ("PERF-HEAVY-DEPENDENCY", "frontend/package.json") in rules
    n1 = next(f for f in found if f["rule_id"] == "PERF-N-PLUS-ONE")
    assert n1["endpoint"] == "GET /api/orders" and n1["evidence_kind"] == "hypothesis" and n1["line"] == 62
    sleep = next(f for f in found if f["rule_id"] == "PERF-BLOCKING-ASYNC" and "sleep" in f["evidence"])
    assert sleep["evidence_kind"] == "static_warning" and sleep["endpoint"] == "GET /x/a"
    assert len({(f["rule_id"], f["file"], f["line"]) for f in found if f["line"]}) == len([f for f in found if f["line"]])


# 3 ------------------------------------------------------------------------------------------------
def test_measurement_parsing():
    assert runner.parse_docker_stats('{"CPUPerc":"94.51%","MemUsage":"58.7MiB / 1GiB"}') == (94.51, 58.7)
    assert runner.parse_docker_stats('{"CPUPerc":"1.5%","MemUsage":"1.2GiB / 2GiB"}') == (1.5, 1228.8)
    assert runner.parse_docker_stats("not json") is None
    assert percentile([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 95) == 10 and percentile([], 50) is None
    s = summarize(Endpoint(path="/a"), [([10.0, 12.0, 11.0], {"200": 3}, 0, 0.1), ([20.0, 22.0], {"200": 2, "500": 1}, 1, 0.1)])
    assert s.requests == 6 and s.errors == 1 and s.rep_medians_ms == [11.0, 21.0] and s.median_ms == 12.0
    assert s.spread_pct == round((21 - 11) / 12 * 100, 2)
    r = runner.resources_of([(10.0, 50.0), (30.0, 70.0)])
    assert (r.cpu_avg_pct, r.cpu_max_pct, r.mem_max_mb) == (20.0, 30.0, 70.0)
    assert runner.resources_of([]).cpu_avg_pct is None             # not measured is None, never a default


# 4 ------------------------------------------------------------------------------------------------
def test_baseline_creates_measured_findings_linked_to_static_ones(sample, services, monkeypatch):
    _, pe = services
    monkeypatch.setattr(runner, "measure", fake_measure({"baseline": SLOW}))
    a = pe.start_analysis("p1", sample, "u1")
    a = pe.store.get("p1", "analyses", a.id)
    assert a.status == "completed" and a.supported and a.baseline_run_id
    run = pe.store.get("p1", "runs", a.baseline_run_id)
    assert run.status == "completed" and run.measurement.status == "measured"
    findings = {f.rule_id: f for f in pe.store.list("p1", "findings")}
    slow = findings["PERF-MEASURED-SLOW"]
    assert slow.evidence_kind == "measured" and slow.endpoint == "GET /api/orders" and slow.measured_ms == 2030.0
    assert slow.file == "backend/main.py" and findings["PERF-N-PLUS-ONE"].id in slow.linked
    assert "GET /health" not in {f.endpoint for f in findings.values() if f.evidence_kind == "measured"}


# 5 ------------------------------------------------------------------------------------------------
def test_failed_readiness_check_is_reported():
    assert runner.wait_ready("http://127.0.0.1:9", None, 1.0, lambda: False) is None   # nothing listens on port 9


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/slow":
            time.sleep(0.5)
        code = 500 if self.path == "/error" else 200
        self.send_response(code)
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *args):
        pass


@pytest.fixture
def local_server():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


# 6 ------------------------------------------------------------------------------------------------
def test_workload_execution_counts_requests_and_errors(local_server):
    lat, codes, errors, elapsed = run_endpoint(local_server, Endpoint(path="/ok"), 40, 4, 5.0)
    assert len(lat) == 40 and codes == {"200": 40} and errors == 0 and elapsed > 0
    lat, codes, errors, _ = run_endpoint(local_server, Endpoint(path="/error"), 10, 2, 5.0)
    assert lat == [] and errors == 10 and codes == {"500": 10}
    assert runner.wait_ready(local_server, "/ok", 5.0, lambda: False) == "GET /ok -> 200"


# 7 ------------------------------------------------------------------------------------------------
def test_request_timeouts_and_time_budget(local_server):
    lat, codes, errors, _ = run_endpoint(local_server, Endpoint(path="/slow"), 4, 2, 0.1)
    assert errors == 4 and lat == [] and set(codes) == {"ReadTimeout"}
    began = time.perf_counter()
    lat, _, _, _ = run_endpoint(local_server, Endpoint(path="/slow"), 1000, 2, 5.0, max_seconds=1.0)
    assert time.perf_counter() - began < 3 and 2 <= len(lat) < 20


# 8 ------------------------------------------------------------------------------------------------
def test_resource_limits_are_enforced(sample):
    from backend.execution.preview_manager import backend_commands, backend_entry
    cmd = backend_commands(sample, "t1", backend_entry(sample), 60)["run"]
    joined = " ".join(cmd)
    for flag in ("--memory 1g", "--cpus 1", "--pids-limit 128", "--read-only", "--cap-drop ALL", "--user 1000:1000",
                 "-p 127.0.0.1::8000"):
        assert flag in joined
    env = runner.environment(Workload())
    assert env.limits == {"memory": "1g", "cpus": "1", "pids-limit": "128"}
    with pytest.raises(Exception):
        Workload(concurrency=500)
    with pytest.raises(Exception):
        Workload(requests_per_endpoint=10**6)


# 9 ------------------------------------------------------------------------------------------------
def test_optimization_plan_is_generated_from_evidence(sample, services, monkeypatch):
    ap, pe = services
    monkeypatch.setattr(runner, "measure", fake_measure({"baseline": SLOW}))
    pe.start_analysis("p1", sample, "u1")
    slow = next(f for f in pe.store.list("p1", "findings") if f.rule_id == "PERF-MEASURED-SLOW")
    plan = pe.create_plan("p1", sample, "u1", slow.id)
    assert plan.target_endpoints == ["GET /api/orders"] and plan.files == ["backend/main.py"]
    assert plan.expected_benefit.startswith("Estimate (not measured)") and "2030.0 ms" in plan.expected_benefit
    assert "N+1" in plan.evidence or "inside a loop" in plan.evidence
    # pagination changes what the endpoint returns: listed as a separate decision, not bundled into the change
    assert "limit/offset" not in plan.proposed_change and "eager loading" in plan.proposed_change
    assert any(r.startswith("Not included") and "pagination" in r.lower() or "every row" in r for r in plan.risks)
    assert "harmless while the table is small" not in plan.expected_benefit
    assert plan.rank_score > 0 and plan.rollback and plan.tests == ["tests/test_orders.py"]
    ap_plan = ap.store.get("p1", "plans", plan.autopilot_plan_id)
    assert ap_plan.origin == "performance" and ap_plan.status.value == "awaiting_approval"
    assert "performance" in ap_plan.checks and ap_plan.tasks[0].request.startswith("Performance optimization")
    with pytest.raises(PlanError):
        pe.create_plan("p1", sample, "u1", slow.id)                       # already planned
    effect = {"rule_id": "PERF-EFFECT-NO-DEPS", "category": "rerender", "title": "t", "severity": "high",
              "evidence_kind": "static_warning", "detection": "d", "confidence": "high", "file": "frontend/a.jsx",
              "line": 1, "evidence": "e", "impact": "", "recommendation": "", "validation": "", "endpoint": None}
    f = pe._store_findings("p1", [effect])[0]
    with pytest.raises(PlanError):
        pe.create_plan("p1", sample, "u1", f.id)                          # frontend: not measurable yet


def _approved(pe, ap, sample, monkeypatch, baseline=SLOW):
    monkeypatch.setattr(runner, "measure", fake_measure({"baseline": baseline}))
    pe.start_analysis("p1", sample, "u1")
    slow = next(f for f in pe.store.list("p1", "findings") if f.rule_id == "PERF-MEASURED-SLOW")
    plan = pe.create_plan("p1", sample, "u1", slow.id)
    return plan


FIXED_MAIN_REPLY = None


def _model_fix(sample):
    main = (sample / "backend/main.py").read_text(encoding="utf-8")
    fixed = main.replace("        items = db.query(Item).filter(Item.order_id == order.id).order_by(Item.id).all()\n",
                         "        items = sorted(order.items, key=lambda i: i.id)\n")
    return lambda system, prompt: "### backend/main.py\n```python\n" + fixed + "```\n"


# 10 -----------------------------------------------------------------------------------------------
def test_nothing_runs_without_approval(sample, services, monkeypatch):
    ap, pe = services
    plan = _approved(pe, ap, sample, monkeypatch)
    with pytest.raises(AutopilotPlanError):
        ap.execute("p1", plan.autopilot_plan_id, "u1", sample, generate=_model_fix(sample), include_tests=False)


# 11 -----------------------------------------------------------------------------------------------
def test_a_correctness_regression_stops_before_measuring(sample, services, monkeypatch):
    ap, pe = services
    plan = _approved(pe, ap, sample, monkeypatch)
    ap.decide("p1", plan.autopilot_plan_id, "u1", "approved")
    calls = []
    monkeypatch.setattr(runner, "measure", lambda *a, **k: calls.append(1))
    broken = lambda s, p: "### backend/main.py\n```python\nfrom fastapi import FastAPI\napp = FastAPI()\nx = undefined_name\n```\n"
    e = ap.execute("p1", plan.autopilot_plan_id, "u1", sample, generate=broken, include_tests=False)
    assert e.status == "rejected" and not e.applied_to_project and calls == []
    assert any(s.name.startswith("performance") and s.status == "skipped" for s in e.stages)


# 12 -----------------------------------------------------------------------------------------------
def test_performance_comparison_rules():
    t = Thresholds()
    after = measurement("candidate", [stats("/api/orders", [395.0, 406.0, 390.0]), stats("/health", [2.1, 2.1, 2.0])])
    c = gate.compare(SLOW, after, t, ["GET /api/orders"])
    assert c.decision == "improved" and "-80" in c.reasons[0]
    worse = measurement("candidate", [stats("/api/orders", [395.0, 406.0, 390.0]), stats("/health", [9.0, 9.5, 9.2])])
    assert gate.compare(SLOW, worse, t, ["GET /api/orders"]).decision == "regressed"            # another endpoint slower
    errors = measurement("candidate", [stats("/api/orders", [395.0, 406.0, 390.0], errors=5), stats("/health", [2.1, 2.1, 2.0])])
    assert gate.compare(SLOW, errors, t, ["GET /api/orders"]).decision == "regressed"            # error rate up
    memory = measurement("candidate", after.endpoints, mem=200.0)
    assert gate.compare(SLOW, memory, t, ["GET /api/orders"]).decision == "regressed"            # memory up


# 13 -----------------------------------------------------------------------------------------------
def test_noisy_or_small_differences_are_inconclusive():
    t = Thresholds()
    noisy_before = measurement("baseline", [stats("/a", [100.0, 140.0, 120.0])])
    noisy_after = measurement("candidate", [stats("/a", [90.0, 130.0, 105.0])])
    c = gate.compare(noisy_before, noisy_after, t, ["GET /a"])
    assert c.decision == "inconclusive" and "overlap" in c.reasons[0]
    tiny = gate.compare(measurement("baseline", [stats("/a", [100.0, 101.0, 100.5])]),
                        measurement("candidate", [stats("/a", [97.0, 97.5, 97.2])]), t, ["GET /a"])
    assert tiny.decision == "inconclusive" and "below the 10.0% threshold" in tiny.reasons[0]
    single = gate.compare(measurement("baseline", [stats("/a", [100.0])]), measurement("candidate", [stats("/a", [50.0])]),
                          t, ["GET /a"])
    assert single.decision == "inconclusive" and "only one repetition" in single.reasons[0]


# 14 -----------------------------------------------------------------------------------------------
def test_a_slower_candidate_is_rolled_back(sample, services, monkeypatch):
    ap, pe = services
    plan = _approved(pe, ap, sample, monkeypatch)
    ap.decide("p1", plan.autopilot_plan_id, "u1", "approved")
    slower = measurement("candidate", [stats("/api/orders", [3000.0, 3100.0, 3050.0]), stats("/health", [2.1, 2.0, 2.2])])
    monkeypatch.setattr(runner, "measure", fake_measure({"baseline": SLOW, "candidate": slower}))
    before = (sample / "backend/main.py").read_text(encoding="utf-8")
    e = ap.execute("p1", plan.autopilot_plan_id, "u1", sample, generate=_model_fix(sample), include_tests=False)
    assert e.status == "rejected" and e.verdict["performance"]["decision"] == "regressed"
    assert not e.applied_to_project and (sample / "backend/main.py").read_text(encoding="utf-8") == before
    assert pe.store.get("p1", "findings", plan.finding_id).status == "not_improved"


# 15 -----------------------------------------------------------------------------------------------
def test_missing_docker_means_static_only_and_not_measured(sample, services, monkeypatch):
    _, pe = services
    import backend.execution.docker_test_sandbox as sandbox
    monkeypatch.setattr(sandbox, "docker_available", lambda: False)
    results, env = runner.measure({"baseline": sample}, Workload())
    assert results["baseline"].status == "unavailable" and "Docker is not available" in results["baseline"].error
    assert results["baseline"].endpoints == [] and "not available" in env.profiling
    a = pe.store.get("p1", "analyses", pe.start_analysis("p1", sample, "u1").id)
    assert a.status == "completed" and pe.store.get("p1", "runs", a.baseline_run_id).status == "unavailable"
    kinds = {f.evidence_kind for f in pe.store.list("p1", "findings")}
    assert "measured" not in kinds and "hypothesis" in kinds


# 16 -----------------------------------------------------------------------------------------------
def test_cancellation(sample, services, monkeypatch):
    ap, pe = services
    plan = _approved(pe, ap, sample, monkeypatch)
    ap.decide("p1", plan.autopilot_plan_id, "u1", "approved")

    def measure_then_cancel(projects, workload, should_stop=None, on_stage=None):
        running = [e for e in ap.store.list("p1", "executions") if e.status == "running"][0]
        ap.cancel_execution("p1", running.id)
        assert should_stop()                                                       # the runner sees the request
        return {label: Measurement(label=label, status="cancelled") for label in projects}, runner.environment(workload)
    monkeypatch.setattr(runner, "measure", measure_then_cancel)
    before = (sample / "backend/main.py").read_text(encoding="utf-8")
    e = ap.execute("p1", plan.autopilot_plan_id, "u1", sample, generate=_model_fix(sample), include_tests=False)
    assert e.status == "cancelled" and (sample / "backend/main.py").read_text(encoding="utf-8") == before
    run = pe.start_baseline("p1", sample, "u1", Workload(endpoints=[Endpoint(path="/health")]))
    assert pe.cancel_run("p1", run.id).status in ("completed", "cancelled", "failed", "unavailable")


# 17 -----------------------------------------------------------------------------------------------
def test_improvement_is_applied_and_reported(sample, services, monkeypatch):
    ap, pe = services
    plan = _approved(pe, ap, sample, monkeypatch)
    ap.decide("p1", plan.autopilot_plan_id, "u1", "approved")
    faster = measurement("candidate", [stats("/api/orders", [395.0, 406.0, 390.0]), stats("/health", [2.1, 2.1, 2.0])])
    monkeypatch.setattr(runner, "measure", fake_measure({"baseline": SLOW, "candidate": faster}))
    e = ap.execute("p1", plan.autopilot_plan_id, "u1", sample, generate=_model_fix(sample), include_tests=False)
    assert e.status == "completed", e.error
    assert "order.items" in (sample / "backend/main.py").read_text(encoding="utf-8")
    report = pe.report("p1", plan.id)
    assert report["applied"] and report["comparison"]["decision"] == "improved"
    assert report["comparison"]["per_endpoint"][0]["median_change_pct"] < -50
    assert report["correctness"]["verdict"]["accepted"] and "estimate" in report["measured_vs_estimated"]
    assert report["rollback_status"].startswith("not needed") and report["baseline"]["status"] == "completed"
    assert pe.store.get("p1", "findings", plan.finding_id).status == "verified"


# 18 -----------------------------------------------------------------------------------------------
def test_secrets_are_redacted(sample):
    (sample / "backend/upstream.py").write_text(
        f"import requests\nfrom fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/u')\nasync def u():\n"
        f"    return requests.get('http://x', headers={{'Authorization': 'Bearer {SECRET}'}})\n", encoding="utf-8")
    found, _ = static.project_findings(sample)
    assert found and all(SECRET not in f["evidence"] for f in found)
    from backend.evolution.autopilot.redact import redact
    assert SECRET not in redact(f"app log: token={SECRET}")


# 19 -----------------------------------------------------------------------------------------------
def test_unsafe_paths_and_paused_generations_are_rejected(api):
    base = "/api/projects/gen_mine/performance"
    for path in ("/../../etc/passwd", "http://evil.example/x", "no-slash"):
        r = api.post(f"{base}/baselines", json={"workload": {"endpoints": [{"method": "GET", "path": path}]}})
        assert r.status_code == 400, path
    r = api.post(f"{base}/baselines", json={"workload": {"endpoints": [{"method": "TRACE", "path": "/x"}]}})
    assert r.status_code == 400
    assert api.post("/api/projects/gen_paused/evolution/plans/pln_x/execute", json={}).status_code == 409


# 20 -----------------------------------------------------------------------------------------------
def test_readiness_reports_unmeasured_performance_honestly(monkeypatch, services, sample):
    _, pe = services
    import backend.performance.engineer.service as svc_module
    from backend.readiness.checks import ReadinessCheckCollector
    checks = ReadinessCheckCollector().collect_all_checks("never_measured_project")
    perf = next(c for c in checks if c.category == "Performance")
    assert perf.status.value == "NOT_AVAILABLE" and "Not measured" in perf.evidence
    monkeypatch.setattr(runner, "measure", fake_measure({"baseline": SLOW}))
    pe.start_analysis("p1", sample, "u1")
    assert svc_module.global_performance_engineer is pe
    perf = next(c for c in ReadinessCheckCollector().collect_all_checks("p1")
                if c.category == "Performance")
    assert perf.status.value == "WARN" and "3045.0 ms" in perf.evidence              # real numbers, not a constant
    from backend.evolution.autopilot.executor import STAGES, stages_for
    from backend.evolution.autopilot.models import Plan
    plain = Plan(id="p", project_id="p", user_id="u", objective="o", finding_ids=[], tasks=[], expected_files=[],
                 agents=[], checks=[], risks=[], assumptions=[], approval_required=[], completion_criteria=[])
    assert stages_for(plain) == STAGES                                                 # Autopilot plans are unchanged
