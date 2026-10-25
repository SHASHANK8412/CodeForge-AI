"""
AIForge Reality Simulator tests. The queueing formulas are checked against textbook values; the load generator
is checked against a real local HTTP server; scenario limits, approval, calibration and labelling are checked
through the service. Docker-bound steps (baseline and load runs in containers) are replaced by doubles in fast
tests only; the genuine test at the end measures a real app in isolated containers and the Chaos sandbox.
"""

import http.server
import json
import math
import threading
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.reality import analytical, loadgen
from backend.reality.models import Alternative, Resources, Scenario, Traffic
from backend.reality.service import RealitySimulator, RealityStore, SimulationError
from tests.reality.sample import write_sample

BASELINE = {"status": "measured", "run_id": "b1", "peak_memory_mb": 80.0,
            "endpoints": {"GET /api/compute": {"median_ms": 20.0, "rep_medians_ms": [19.0, 20.0, 22.0], "p95_ms": 24.0},
                          "GET /api/light": {"median_ms": 2.0, "rep_medians_ms": [2.0, 2.0, 2.5], "p95_ms": 3.0}}}


def scenario(**kw):
    t = dict(pattern="constant", rps=20, duration_seconds=10, mix={"GET /api/compute": 1})
    t.update(kw.pop("traffic", {}))
    return Scenario(name="s", traffic=Traffic(**t), alternatives=kw.pop("alternatives", [Alternative(id="current", title="current")]), **kw)


# 1 the analytical model --------------------------------------------------------------------------------------------
def test_erlang_c_matches_textbook_values():
    assert analytical.erlang_c(1, 0.5) == pytest.approx(0.5)                   # M/M/1: P(wait) = rho
    assert analytical.erlang_c(2, 1.0) == pytest.approx(1 / 3)                  # c=2, a=1
    assert analytical.erlang_c(3, 3.5) == 1.0                                   # unstable


def test_single_server_prediction_is_the_mm1_formula():
    p = analytical.predict(BASELINE, {"GET /api/compute": 1}, 25, workers=1, cpus=1.0, dep_ms=None, dependent=[], duration_s=10)
    rho = 25 * 0.020
    assert p["status"] == "predicted" and p["label"].startswith("analytical estimate") and p["utilization"] == pytest.approx(rho)
    assert p["mean_ms"] == pytest.approx(20 / (1 - rho), rel=0.01)              # M/M/1: R = S / (1 - rho)
    assert p["capacity_rps"] == pytest.approx(50) and not p["saturated"]
    lo, hi = p["bounds"]["mean_ms"]
    assert lo < p["mean_ms"] < hi                                               # bounds from the repetition spread
    assert p["formulas"] and p["assumptions"] and p["inputs"]["baseline_run"] == "b1"


def test_cpu_limits_workers_saturation_and_threadpool():
    half = analytical.predict(BASELINE, {"GET /api/compute": 1}, 20, 1, 0.5, None, [], 10)
    assert half["cpu_speed"] == 0.5 and half["mean_service_ms"] == pytest.approx(40) and half["utilization"] == pytest.approx(0.8)
    two = analytical.predict(BASELINE, {"GET /api/compute": 1}, 60, 2, 2.0, None, [], 10)
    assert two["capacity_rps"] == pytest.approx(100) and not two["saturated"]
    over = analytical.predict(BASELINE, {"GET /api/compute": 1}, 80, 1, 1.0, None, [], 20)
    assert over["saturated"] and over["throughput_rps"] == pytest.approx(50) and over["queue_growth_rps"] == pytest.approx(30)
    assert "grows" in over["note"] and over["p95_ms"] is None
    dep = analytical.predict(BASELINE, {"GET /api/light": 1}, 100, 1, 1.0, 500, ["GET /api/light"], 10)
    assert dep["threadpool_utilization"] == pytest.approx(100 * 0.502 / 40, rel=0.01) and dep["threadpool_saturated"]
    assert dep["per_endpoint"]["GET /api/light"]["mean_ms"] > 500


def test_steady_service_times_use_the_allen_cunneen_correction():
    steady = {"run_id": "b2", "endpoints": {"GET /api/compute": {"median_ms": 20.0, "mean_ms": 20.2, "p95_ms": 21.0,
                                                                 "rep_medians_ms": [19.8, 20.0, 20.3]}}}
    mm = analytical.predict(BASELINE, {"GET /api/compute": 1}, 25, 1, 1.0, None, [], 10)        # no mean: M/M/c
    mg = analytical.predict(steady, {"GET /api/compute": 1}, 25, 1, 1.0, None, [], 10)
    assert mm["method"].startswith("M/M/c") and mg["method"].startswith("M/G/c")
    assert mg["service_cv2"] < 0.01 and mg["waiting_factor"] == pytest.approx(0.5, abs=0.01)
    # M/D/1 waits half as long as M/M/1: Wq = rho S / (2 (1 - rho))
    assert mg["mean_wait_ms"] == pytest.approx(0.5 * 20 / (2 * 0.5), rel=0.02)
    assert mg["mean_ms"] < mm["mean_ms"]


def test_missing_measurements_mean_no_prediction():
    p = analytical.predict(BASELINE, {"GET /api/unknown": 1}, 10, 1, 1.0, None, [], 10)
    assert p["status"] == "insufficient_evidence" and "GET /api/unknown" in p["reason"]


def test_costs_need_user_prices():
    p = analytical.predict(BASELINE, {"GET /api/compute": 1}, 20, 1, 1.0, None, [], 10)
    none = analytical.cost(p, BASELINE, None, 0.7, 20)
    assert none["monthly_cost"] is None and "enter unit prices" in none["note"]
    assert none["vcpus_needed"] == pytest.approx(20 * 0.020 / 0.7, rel=0.01)
    priced = analytical.cost(p, BASELINE, {"vcpu_hour": 0.05, "gb_hour": 0.01, "currency": "USD"}, 0.7, 20)
    assert priced["monthly_cost"] > 0 and priced["label"].startswith("estimate")


# 2 scenarios ----------------------------------------------------------------------------------------------------------
def test_scenarios_are_validated_and_bounded():
    with pytest.raises(ValidationError):
        Traffic(rps=500, mix={"GET /a": 1})                                     # > 200 rps
    with pytest.raises(ValidationError):
        Traffic(rps=200, duration_seconds=120, mix={"GET /a": 1})               # 24,000 requests
    with pytest.raises(ValidationError):
        Traffic(mix={"GET /api/items/{id}": 1})                                 # needs path values
    with pytest.raises(ValidationError):
        Traffic(mix={"POST /api/items": 1})
    with pytest.raises(ValidationError):
        Resources(workers=16)
    with pytest.raises(ValidationError):
        scenario(alternatives=[Alternative(id="a", title="a"), Alternative(id="a", title="b")])
    with pytest.raises(ValidationError):
        scenario(alternatives=[Alternative(id="slow", title="slow dep", dependency_latency_ms=200)])   # which endpoints?


def test_arrival_schedules_are_seeded_and_follow_the_pattern():
    t = scenario().traffic.model_dump()
    a, b = loadgen.schedule(t, 7), loadgen.schedule(t, 7)
    assert a == b and 150 <= len(a) <= 250                                       # ~20 rps x 10 s (Poisson)
    ramp = scenario(traffic={"pattern": "ramp", "start_rps": 1, "rps": 40, "duration_seconds": 20}).traffic.model_dump()
    s = loadgen.schedule(ramp, 1)
    assert sum(1 for x in s if x["at"] >= 10) > 2 * sum(1 for x in s if x["at"] < 10)
    burst = scenario(traffic={"pattern": "burst", "start_rps": 2, "rps": 60, "burst_seconds": 4, "duration_seconds": 20}).traffic.model_dump()
    assert analytical.rate_at(burst, 10) == 60 and analytical.rate_at(burst, 1) == 2
    assert analytical.saturation_onset(ramp, 20) == pytest.approx(10, abs=1)


class _Slow(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        time.sleep(0.01)
        code = 500 if self.path == "/broken" else 200
        self.send_response(code)
        self.end_headers()
        self.wfile.write(b'{"ok": true}')

    def log_message(self, *a):
        pass


@pytest.fixture
def server():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Slow)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def test_the_open_loop_generator_measures_a_real_server(server):
    t = scenario(traffic={"rps": 30, "duration_seconds": 5, "mix": {"GET /ok": 3, "GET /broken": 1}}).traffic.model_dump()
    r = loadgen.run(server, t, lambda: False)
    assert r["label"].startswith("measured") and r["sent"] == r["planned_requests"] and r["dropped_by_generator"] == 0
    assert 0.1 < r["error_rate_pct"] / 100 < 0.45 and r["status_codes"].get("500")          # the 500s are counted
    assert 10 <= r["mean_ms"] < 500 and r["p95_ms"] >= r["p50_ms"]
    assert len(r["timeline"]) == 5 and sum(x["sent"] for x in r["timeline"]) == r["sent"]
    tiny = loadgen.run(server, t, lambda: False, max_inflight=1)
    assert tiny["generator_limited"]                                             # the rig's own limit is reported


# 3 the service ----------------------------------------------------------------------------------------------------------
@pytest.fixture
def doubles(monkeypatch):
    """Containers replaced: the baseline returns BASELINE-like stats; load runs return supplied results."""
    from backend.performance.engineer import runner
    from backend.performance.engineer.models import EndpointStats, Environment, Measurement, Resources as R
    box = {"load": {}}

    def measure(projects, workload, stop=None, on_stage=None, resources=None, drive=None, pre_drive=None):
        label = next(iter(projects))
        m = Measurement(label=label, status="measured", resources=R(samples=3, cpu_avg_pct=box.get("cpu", 40.0), mem_max_mb=80.0))
        if drive is None:
            m.endpoints = [EndpointStats(method="GET", path=e.path, requests=90, errors=0, error_rate_pct=0.0, median_ms=20.0,
                                         rep_medians_ms=[19.0, 20.0, 22.0]) for e in workload.endpoints]
        else:
            m.custom = box["load"][label]
        return {label: m}, Environment(method="double (test)")
    monkeypatch.setattr(runner, "measure", measure)
    return box


def sim(tmp_path):
    return RealitySimulator(RealityStore(tmp_path / "reality"), background=False)


def test_predict_only_measures_a_baseline_and_labels_everything(tmp_path, doubles):
    project = write_sample(tmp_path / "app")
    s = sim(tmp_path).start("p1", project, "u1", scenario(), run_load=False, approved=False)
    assert s.status == "completed" and s.measurements == {} and s.baseline["status"] == "measured"
    assert s.predictions["current"]["label"].startswith("analytical estimate")
    assert any("predictions only" in x for x in s.limitations)
    assert any(r["endpoint"] == "GET /api/compute" for r in s.application["routes"])
    assert s.recommendation["basis"] == "predicted" and "run the workload" in s.recommendation["recommended_experiments"][0]


def test_load_runs_need_approval_and_a_mix(tmp_path):
    project = write_sample(tmp_path / "app")
    with pytest.raises(SimulationError, match="approve"):
        sim(tmp_path).start("p1", project, "u1", scenario(), run_load=True, approved=False)
    with pytest.raises(SimulationError, match="mix"):
        sim(tmp_path).start("p1", project, "u1", scenario(traffic={"mix": {}}), run_load=False, approved=False)


def _load(throughput, mean, p95, limited=False, errors=0.0):
    return {"label": "measured (open-loop load against an isolated copy)", "planned_requests": 200, "sent": 200, "completed_ok": 200, "errors": 0, "dropped_by_generator": 0,
            "error_rate_pct": errors, "throughput_rps": throughput, "mean_ms": mean, "p50_ms": mean, "p95_ms": p95,
            "status_codes": {"200": 200}, "per_endpoint": {}, "timeline": [], "generator_lag_ms": {}, "generator_limited": limited,
            "cancelled": False}


def test_predictions_and_measurements_are_compared_and_calibrated(tmp_path, doubles):
    project = write_sample(tmp_path / "app")
    doubles["load"] = {"current": _load(19.8, 31.0, 70.0), "limited": _load(12.0, 20.0, 30.0, limited=True)}
    sc = scenario(alternatives=[Alternative(id="current", title="current"), Alternative(id="limited", title="limited")])
    engine = sim(tmp_path)
    s = engine.start("p1", project, "u1", sc, run_load=True, approved=True)
    c = s.comparisons["current"]
    assert c["comparable"] and {r["metric"] for r in c["rows"]} == {"throughput_rps", "mean_ms", "p95_ms"}
    mean = next(r for r in c["rows"] if r["metric"] == "mean_ms")
    assert mean["predicted"] == s.predictions["current"]["mean_ms"] and mean["observed"] == 31.0
    assert s.comparisons["limited"]["comparable"] is False and "generator" in s.comparisons["limited"]["reason"]
    cal = engine.calibration()
    assert cal["groups"] and all(g["assessment"] == "insufficient history" for g in cal["groups"])   # < 5 records
    assert s.measurements["current"]["label"].startswith("measured")


def test_calibrated_estimates_need_enough_comparable_history(tmp_path):
    from backend.reality.models import CalibrationRecord
    from backend.reality.service import CALIBRATION_KEY
    engine = sim(tmp_path)
    pred = analytical.predict({**BASELINE, "endpoints": {"GET /api/compute": {**BASELINE["endpoints"]["GET /api/compute"], "mean_ms": 20.5}}},
                              {"GET /api/compute": 1}, 20, 1, 1.0, None, [], 10)
    from backend.reality.calibration import group_key
    key = group_key(pred, "mean_ms")                      # model, method, metric, state, workers, CPU limit, utilisation band
    assert engine.calibrated(pred)["mean_ms"]["value"] is None                       # no history: no correction
    for i, ratio in enumerate([2.0, 2.4, 2.2, 1.9, 2.1]):
        engine.store.put(CALIBRATION_KEY, "calibration", CalibrationRecord(
            id=f"c{i}", project_id="p", simulation_id="s", alternative="a", method=pred["method"], metric="mean_ms",
            predicted=10.0, observed=10.0 * ratio, error_pct=(ratio - 1) * 100, within_bounds=False, comparable_key=key))
    engine.store.put(CALIBRATION_KEY, "calibration", CalibrationRecord(
        id="other", project_id="p", simulation_id="s", alternative="a", method=pred["method"], metric="mean_ms",
        predicted=10.0, observed=100.0, error_pct=900, within_bounds=False, comparable_key=key.replace("|stable|", "|saturated|")))
    cal = engine.calibrated(pred)["mean_ms"]
    assert cal["records"] == 5 and cal["factor"] == pytest.approx(2.1) and cal["value"] == pytest.approx(pred["mean_ms"] * 2.1, rel=0.01)
    assert "still an estimate" in cal["note"]                                          # the saturated record was not mixed in


def test_bottlenecks_are_labelled_by_evidence(tmp_path, doubles):
    project = write_sample(tmp_path / "app")
    doubles["load"] = {"current": _load(12.0, 900.0, 2000.0, errors=5.0)}
    doubles["cpu"] = 97.0
    s = sim(tmp_path).start("p1", project, "u1", scenario(traffic={"rps": 45}), run_load=True, approved=True)
    labels = {b["label"] for b in s.bottlenecks}
    assert {"measured bottleneck", "model-predicted bottleneck"} <= labels
    assert any("CPU 97.0%" in b["detail"] for b in s.bottlenecks) and any("served 12.0 of 45" in b["detail"] for b in s.bottlenecks)


def test_dependency_alternatives_compare_with_the_sandbox_measurement(tmp_path, doubles, monkeypatch):
    project = write_sample(tmp_path / "app")
    engine = sim(tmp_path)
    monkeypatch.setattr(engine, "_dependency_run", lambda *a: {"status": "measured", "normal": {"mean_ms": 12.0},
                                                               "slowed": {"mean_ms": 215.0}, "added_latency_ms": 200})
    sc = scenario(alternatives=[Alternative(id="slow", title="slow payments", dependency_latency_ms=200)],
                  dependent_endpoints=["GET /api/checkout"], dependency={"name": "payments", "env_var": "PAYMENTS_URL", "routes": {}})
    s = engine.start("p1", project, "u1", sc, run_load=True, approved=True)
    row = s.comparisons["slow"]["rows"][0]
    assert row["metric"] == "dependency_mean_ms" and row["predicted"] == 212.0 and row["observed"] == 215.0 and row["within_bounds"]


def test_cancellation_keeps_partial_results(tmp_path, doubles):
    project = write_sample(tmp_path / "app")
    engine = sim(tmp_path)
    original = engine._baseline

    def slow_baseline(*a):
        out = original(*a)
        engine.store.update("p1", "simulations", engine.store.list("p1", "simulations")[0].id, lambda x: setattr(x, "cancel_requested", True))
        return out
    engine._baseline = slow_baseline
    doubles["load"] = {"current": _load(19.0, 30.0, 60.0)}
    s = engine.start("p1", project, "u1", scenario(), run_load=True, approved=True)
    assert s.status == "cancelled" and s.baseline["status"] == "measured" and s.measurements == {}


# 4 API ---------------------------------------------------------------------------------------------------------------------
@pytest.fixture
def api(tmp_path, doubles, monkeypatch):
    import backend.reality.routes as routes
    import backend.routes.export as export
    from backend.auth.dependencies import get_current_user
    from backend.generation.store import global_generation_store
    project = write_sample(tmp_path / "app")
    monkeypatch.setattr(routes, "global_reality_simulator", sim(tmp_path))
    records = {"gen_mine": {"generation_id": "gen_mine", "user_id": "alice", "status": "completed", "project_path": str(project)},
               "gen_theirs": {"generation_id": "gen_theirs", "user_id": "bob", "status": "completed", "project_path": str(project)}}
    monkeypatch.setattr(global_generation_store, "get", lambda gid, default=None: records.get(gid, default))
    monkeypatch.setattr(export, "_safe_project_dir", lambda p: project if p == str(project) else None)
    app = FastAPI()
    app.include_router(routes.reality_router)
    app.dependency_overrides[get_current_user] = lambda: {"id": "alice"}
    return TestClient(app)


def test_api_access_validation_and_report(api):
    base = "/api/projects/gen_mine/reality"
    body = {"scenario": json.loads(scenario().model_dump_json())}
    assert api.post("/api/projects/gen_theirs/reality/simulations", json=body).status_code == 403
    assert api.post(f"{base}/simulations", json={**body, "run_load": True}).status_code == 400          # not approved
    bad = json.loads(json.dumps(body))
    bad["scenario"]["traffic"]["rps"] = 1000
    assert api.post(f"{base}/simulations", json=bad).status_code == 422
    assert any(r["endpoint"] == "GET /api/checkout" for r in api.get(f"{base}/model").json()["model"]["routes"])
    sid = api.post(f"{base}/simulations", json=body).json()["simulation"]["id"]
    md = api.get(f"{base}/simulations/{sid}/report").text
    assert "Predictions are analytical estimates" in md and "predicted (M/M/c" in md and "measured: not run" in md
    assert api.get("/api/reality/calibration").status_code == 200


def test_the_page_uses_the_real_api():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2] / "frontend" / "src"
    service = (root / "services" / "reality.js").read_text(encoding="utf-8")
    page = (root / "pages" / "RealitySimulatorPage.jsx").read_text(encoding="utf-8")
    for path in ("/model", "/simulations", "/cancel", "/report", "/api/reality/calibration"):
        assert path in service
    assert "approved: runLoad" in service and "consent" in page and "predicted" in page and "measured" in page
    for fake in ("Math.random", "mockData", "fakeScore"):
        assert fake not in page


# 5 genuine ------------------------------------------------------------------------------------------------------------------
def _docker_ok():
    try:
        from backend.execution.docker_test_sandbox import docker_available
        return docker_available()
    except Exception:
        return False


@pytest.mark.skipif(not _docker_ok(), reason="Docker is not available: the genuine simulation was NOT run")
def test_genuine_simulation_against_isolated_copies(tmp_path):
    """Baseline measured in a container -> a 20 rps scenario predicted for 1 CPU and 0.5 CPU and for a slowed
    payments dependency -> the workload runs against fresh containers with those limits, the dependency runs in the
    Chaos sandbox with its stub -> predictions and observations are compared and recorded -> the report explains."""
    project = write_sample(tmp_path / "app")
    sc = scenario(traffic={"rps": 20, "duration_seconds": 20, "mix": {"GET /api/compute": 1}},
                  alternatives=[Alternative(id="one_cpu", title="1 CPU"), Alternative(id="half_cpu", title="0.5 CPU", resources=Resources(cpus=0.5)),
                                Alternative(id="slow_payments", title="payments +200 ms", dependency_latency_ms=200)],
                  dependent_endpoints=["GET /api/checkout"],
                  dependency={"name": "payments", "env_var": "PAYMENTS_URL", "routes": {"/charge": {"ok": True}}})
    engine = sim(tmp_path)
    s = engine.start("p1", project, "u1", sc, run_load=True, approved=True)
    assert s.status == "completed", (s.error, s.stages)
    base = s.baseline["endpoints"]["GET /api/compute"]
    assert s.baseline["status"] == "measured" and base["median_ms"] >= 5 and len(base["rep_medians_ms"]) == 3
    for aid in ("one_cpu", "half_cpu"):
        m = s.measurements[aid]
        assert m["status"] == "measured" and m["sent"] > 300 and m["mean_ms"] and m["label"].startswith("measured")
        assert s.predictions[aid]["label"].startswith("analytical estimate")
    assert s.predictions["half_cpu"]["utilization"] > s.predictions["one_cpu"]["utilization"]
    dep = s.measurements["slow_payments"]
    assert dep["status"] == "measured", dep
    assert dep["slowed"]["mean_ms"] - dep["normal"]["mean_ms"] > 150                    # the added latency was observed
    assert any(c.get("comparable") for c in s.comparisons.values())
    assert engine.calibration()["groups"]
    print(json.dumps({aid: {"predicted_mean": s.predictions[aid].get("mean_ms"), "observed_mean": s.measurements[aid].get("mean_ms"),
                            "rows": s.comparisons[aid].get("rows")} for aid in ("one_cpu", "half_cpu")}, default=str))
    print(json.dumps({"dependency": s.comparisons["slow_payments"]}, default=str))
    assert not math.isnan(base["median_ms"])
