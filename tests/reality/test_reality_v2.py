"""
Reality Simulator v2: measurements with provenance, cgroup CPU accounting, the contention probe and model v2,
evidence-based bottleneck findings, leave-one-out validated calibration, confidence-aware predictions, approved
experiment plans and verified cleanup. Docker-bound steps are replaced by doubles only in the fast tests; the
genuine test at the end measures a real app in containers (cgroup counters, probe, load, cleanup).
"""

import http.server
import json
import subprocess
import threading
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.reality import analytical, bottlenecks, calibration, loadgen, probe
from backend.reality.models import Alternative, CalibrationRecord, Resources, Scenario, Traffic
from backend.reality.service import CALIBRATION_KEY, RealitySimulator, RealityStore, SimulationError
from tests.reality.sample import write_sample

BASELINE = {"status": "measured", "run_id": "b1", "peak_memory_mb": 80.0,
            "endpoints": {"GET /api/compute": {"median_ms": 20.0, "mean_ms": 20.4, "p95_ms": 23.0, "rep_medians_ms": [19.5, 20.0, 21.0]}}}
PROBE = {"label": "measured (double)", "workers": 1, "concurrency": 2,
         "endpoints": {"GET /api/compute": {"available": True, "s1_ms": 21.0, "s_eff_ms": 30.0, "x1_rps": 47.6, "xc_rps": 33.3,
                                            "efficiency": 0.7, "concurrency": 2}}}


def scenario(**kw):
    t = dict(pattern="constant", rps=20, duration_seconds=10, mix={"GET /api/compute": 1})
    t.update(kw.pop("traffic", {}))
    return Scenario(name="s", traffic=Traffic(**t), alternatives=kw.pop("alternatives", [Alternative(id="current", title="current")]), **kw)


def sim(tmp_path):
    return RealitySimulator(RealityStore(tmp_path / "reality"), background=False)


# local HTTP server for the generator ---------------------------------------------------------------------------------
class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/slow":
            time.sleep(0.6)
        else:
            time.sleep(0.005)
        code = 500 if self.path == "/broken" else 200
        self.send_response(code)
        self.end_headers()
        try:
            self.wfile.write(b'{"ok": true}')
        except OSError:
            pass

    def log_message(self, *a):
        pass


@pytest.fixture
def server():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


# 1 metric collection ------------------------------------------------------------------------------------------------------
def test_metrics_are_collected_with_provenance(server):
    t = scenario(traffic={"rps": 40, "duration_seconds": 5, "mix": {"GET /ok": 1}}).traffic.model_dump()
    r = loadgen.run(server, t, lambda: False)
    for k in ("throughput_rps", "completed_ok", "errors", "mean_ms", "median_ms", "p90_ms", "p95_ms", "p99_ms", "timeouts",
              "success_rate_pct", "elapsed_s"):
        assert r[k] is not None, k
    assert r["median_ms"] <= r["p90_ms"] <= r["p95_ms"] <= r["p99_ms"] and r["timeouts"] == 0 and r["success_rate_pct"] == 100.0
    g = r["generator"]
    assert g["sustained"] and g["scheduled_requests"] == r["planned_requests"] and g["achieved_send_rps"] > 0
    assert g["process_cpu_seconds"] >= 0 and g["process_cpu_pct_of_one_core"] is not None and g["lag_ms"]["p95"] is not None
    assert r["workload"]["arrivals"].startswith("Poisson") and r["workload"]["duration_seconds"] == 5
    assert r["provenance"]["p95_ms"].startswith("load generator") and "process_time" in r["provenance"]["generator"]


def test_the_contention_probe_measures_capacity_as_the_peak_throughput(server):
    r = probe.contention_probe(server, ["GET /ok"], 1, lambda: False, requests=20, max_seconds=2)
    e = r["endpoints"]["GET /ok"]
    assert e["available"] and [lv["concurrency"] for lv in e["levels"]] == [1, 2, 4, 8]
    assert e["xc_rps"] == max(lv["x_rps"] for lv in e["levels"]) and e["xc_rps"] >= e["x1_rps"]
    assert e["s_eff_ms"] == pytest.approx(1000 / e["xc_rps"], rel=0.01) and e["efficiency"] > 0
    assert all(lv["requests"] > 0 for lv in e["levels"]) and r["label"].startswith("measured")
    broken = probe.contention_probe(server, ["GET /broken"], 1, lambda: False, requests=5, max_seconds=1)
    assert broken["endpoints"]["GET /broken"]["available"] is False                # no successful request: unavailable


# 2 missing metrics are unavailable, never zero --------------------------------------------------------------------------
def test_missing_metrics_are_reported_as_unavailable():
    t = scenario().traffic.model_dump()
    plan = [{"at": 0.1, "endpoint": "GET /api/compute"}]
    r = loadgen.summarize(t, plan, [{"at": 0.1, "endpoint": "GET /api/compute", "lag_ms": 1, "status": None, "error": "ConnectError", "ms": 3.0}], [], 1.0)
    assert r["mean_ms"] is None and r["p95_ms"] is None and r["provenance"]["p95_ms"].startswith("unavailable")
    assert r["success_rate_pct"] == 0.0 and r["failed_connection"] == 1
    from backend.performance.engineer.runner import cpu_stat_delta
    d = cpu_stat_delta(None, None, 1.0)
    assert d["available"] is False and "could not be read" in d["reason"] and "throttled_ratio" not in d
    f = bottlenecks.detect("a", {"cpus": 1.0, "memory_mb": 512, "workers": 1}, 20,
                           {"status": "measured", "throughput_rps": 20, "cpu_stat": d, "generator": {"sustained": True}, "resources": {}},
                           None, None, None)
    assert any(x["kind"] == "insufficient_evidence" and "kernel counters" in x["impact"] for x in f)
    assert not any(x["kind"] in ("cpu_saturation", "cpu_throttling") for x in f)


# 3 failed requests and timeouts ------------------------------------------------------------------------------------------
def test_failed_requests_and_timeouts_count_against_reliability(server):
    t = scenario(traffic={"rps": 12, "duration_seconds": 5, "mix": {"GET /ok": 2, "GET /broken": 1, "GET /slow": 1}}).traffic.model_dump()
    r = loadgen.run(server, t, lambda: False, timeout=0.3)
    assert r["timeouts"] > 0 and r["failed_http"] > 0                              # 500s and timeouts both counted
    assert r["errors"] == r["failed_http"] + r["failed_connection"] + r["timeouts"]
    assert r["success_rate_pct"] == pytest.approx(100 * r["completed_ok"] / r["sent"], abs=0.01) and r["success_rate_pct"] < 80
    assert r["error_rate_pct"] == pytest.approx(100 - r["success_rate_pct"], abs=0.02)
    assert r["all_requests_mean_ms"] > r["mean_ms"]                                 # failed requests are not silently dropped


# 4 percentiles ---------------------------------------------------------------------------------------------------------------
def test_percentiles_are_nearest_rank():
    from backend.performance.engineer.workload import percentile
    v = list(range(1, 11))
    assert [loadgen._pct(v, p) for p in (50, 90, 95, 99)] == [5, 9, 10, 10]
    assert all(loadgen._pct(v, p) == percentile(v, p) for p in (1, 25, 50, 75, 90, 95, 99, 100))
    assert loadgen._pct([], 95) is None and loadgen._pct([7.0], 99) == 7.0


# 5 load-generator saturation ---------------------------------------------------------------------------------------------
def test_a_generator_that_cannot_sustain_the_rate_makes_the_run_unsuitable(server, tmp_path, monkeypatch):
    t = scenario(traffic={"rps": 30, "duration_seconds": 5, "mix": {"GET /slow": 1}}).traffic.model_dump()
    r = loadgen.run(server, t, lambda: False, max_inflight=1)
    assert r["generator_limited"] and not r["generator"]["sustained"] and any("dropped" in x for x in r["generator"]["reasons"])
    f = bottlenecks.detect("a", {"cpus": 1.0, "memory_mb": 512, "workers": 1}, 30, {**r, "status": "measured"}, None, None, None)
    assert any(x["kind"] == "load_generator" and x["evidence"] == "strong" for x in f)
    c = sim(tmp_path)._compare("p", "s", "rev", scenario(traffic={"rps": 30}), "current",
                               analytical.predict(BASELINE, {"GET /api/compute": 1}, 30, 1, 1.0, None, [], 10), {**r, "status": "measured"}, BASELINE)
    assert c["comparable"] is False and "generator" in c["reason"] and c["generator_sustained"] is False
    assert sim(tmp_path).store.list(CALIBRATION_KEY, "calibration") == []        # never a calibration observation


# 6 CPU throttling ------------------------------------------------------------------------------------------------------------
class FakeDocker:
    def __init__(self, texts):
        self.texts, self.calls = list(texts), []

    def __call__(self, *args, timeout=60):
        self.calls.append(args)
        if args[:1] == ("exec",) and args[-1] == "/sys/fs/cgroup/cpu.stat" and self.texts:
            return subprocess.CompletedProcess(args, 0, self.texts.pop(0), "")
        return subprocess.CompletedProcess(args, 1, "", "No such file")


def test_cgroup_throttling_is_measured_and_detected():
    from backend.performance.engineer.runner import cpu_stat_delta, read_cpu_stat
    before = "usage_usec 1000000\nuser_usec 900000\nsystem_usec 100000\nnr_periods 100\nnr_throttled 10\nthrottled_usec 50000\n"
    after = "usage_usec 6000000\nuser_usec 5500000\nsystem_usec 500000\nnr_periods 300\nnr_throttled 160\nthrottled_usec 4050000\n"
    fake = FakeDocker([before, after])
    a = read_cpu_stat("app", fake)
    b = read_cpu_stat("app", fake)
    b["read_at"] = a["read_at"] + 10.0                                              # 10 s of wall time
    d = cpu_stat_delta(a, b, 0.5)
    assert d["available"] and d["periods"] == 200 and d["throttled_periods"] == 150 and d["throttled_ratio"] == 0.75
    assert d["throttled_ms"] == 4000.0 and d["cpu_seconds"] == 5.0 and d["cpu_utilization_of_limit"] == 1.0
    assert fake.calls[0] == ("exec", "app", "cat", "/sys/fs/cgroup/cpu.stat")      # read-only, inside the container
    v1 = FakeDocker([])
    v1.__call__ = None
    legacy = read_cpu_stat("app", lambda *a, timeout=60: subprocess.CompletedProcess(a, 0, "nr_periods 10\nnr_throttled 5\nthrottled_time 2000000000\n", "")
                           if a[-1] == "/sys/fs/cgroup/cpu/cpu.stat" else subprocess.CompletedProcess(a, 1, "", ""))
    assert legacy["throttled_usec"] == 2_000_000 and legacy["source"].endswith("cpu/cpu.stat") and "usage_usec" not in legacy
    f = bottlenecks.detect("half", {"cpus": 0.5, "memory_mb": 512, "workers": 1}, 20,
                           {"status": "measured", "throughput_rps": 11.0, "cpu_stat": d, "generator": {"sustained": True},
                            "resources": {"mem_max_mb": 100}}, None, None, None)
    kinds = {x["kind"]: x for x in f}
    assert kinds["cpu_throttling"]["evidence"] == "strong" and kinds["cpu_throttling"]["measurements"]["throttled_ratio"] == 0.75
    assert kinds["cpu_saturation"]["evidence"] == "strong" and "cgroup" in kinds["cpu_saturation"]["method"]
    assert all(x["recommended_experiment"] and x["id"].startswith("bn_half_") for x in f)


# 7 calibration grouping --------------------------------------------------------------------------------------------------------
def _rec(key, pred, obs, i):
    return CalibrationRecord(id=f"c{key[-6:]}{i}", project_id="p", simulation_id="s", alternative="a", method="m", metric="mean_ms",
                             predicted=pred, observed=obs, error_pct=(obs - pred) / pred * 100, within_bounds=False,
                             comparable_key=key, calibration_method=calibration.CALIBRATION_METHOD)


def test_calibration_groups_separate_materially_different_scenarios():
    one = analytical.predict(BASELINE, {"GET /api/compute": 1}, 10, 1, 1.0, None, [], 10)
    keys = {calibration.group_key(one, "mean_ms"),
            calibration.group_key(analytical.predict(BASELINE, {"GET /api/compute": 1}, 10, 1, 0.5, None, [], 10), "mean_ms"),
            calibration.group_key(analytical.predict(BASELINE, {"GET /api/compute": 1}, 10, 2, 1.0, None, [], 10), "mean_ms"),
            calibration.group_key(analytical.predict(BASELINE, {"GET /api/compute": 1}, 40, 1, 1.0, None, [], 10), "mean_ms"),
            calibration.group_key(analytical.predict_v2(BASELINE, {"GET /api/compute": 1}, 10, 1, 1.0, None, [], 10, PROBE), "mean_ms"),
            calibration.group_key(one, "p95_ms")}
    assert len(keys) == 6                                                           # CPU, workers, load band, model, metric
    assert "util-low" in calibration.group_key(one, "mean_ms") and "util-high" in calibration.group_key(
        analytical.predict(BASELINE, {"GET /api/compute": 1}, 45, 1, 1.0, None, [], 10), "mean_ms")


# 8 minimum comparable runs -------------------------------------------------------------------------------------------------------
def test_a_group_needs_five_comparable_runs(tmp_path):
    engine = sim(tmp_path)
    pred = analytical.predict(BASELINE, {"GET /api/compute": 1}, 10, 1, 1.0, None, [], 10)
    key = calibration.group_key(pred, "mean_ms")
    for i, ratio in enumerate([1.5, 1.6, 1.55, 1.45]):
        engine.store.put(CALIBRATION_KEY, "calibration", _rec(key, 10.0, 10.0 * ratio, i))
    c = engine.calibrated(pred)["mean_ms"]
    assert c["value"] is None and c["records"] == 4 and not c["established"] and "4 of 5" in c["note"]
    engine.store.put(CALIBRATION_KEY, "calibration", _rec(key, 10.0, 15.2, 9))
    c = engine.calibrated(pred)["mean_ms"]
    assert c["established"] and c["value"] == pytest.approx(pred["mean_ms"] * 1.52, rel=0.01) and c["records"] == 5
    g = next(x for x in engine.calibration()["groups"] if x["key"] == key)
    assert g["established"] and g["correction_validated"] and g["bias_pct"] == pytest.approx(52.4, abs=0.1)   # mean of 1.5, 1.6, 1.55, 1.45, 1.52 = 1.524


# 9 prediction errors ----------------------------------------------------------------------------------------------------------------
def test_absolute_and_relative_errors_and_bias(tmp_path):
    engine = sim(tmp_path)
    sc = scenario()
    raw = analytical.predict(BASELINE, {"GET /api/compute": 1}, 20, 1, 1.0, None, [], 10)
    raw["predicted_at"] = "2026-10-13T00:00:00+00:00"
    meas = {"status": "measured", "throughput_rps": 19.9, "mean_ms": 2 * raw["mean_ms"], "p95_ms": raw["p95_ms"],
            "error_rate_pct": 0.0, "generator": {"sustained": True}, "generator_limited": False}
    c = engine._compare("p", "sim1", "rev", sc, "current", raw, meas, BASELINE)
    mean = next(r for r in c["rows"] if r["metric"] == "mean_ms")
    assert mean["error_pct"] == pytest.approx(100.0) and not mean["within_bounds"]
    rec = next(r for r in engine.store.list(CALIBRATION_KEY, "calibration") if r.metric == "mean_ms")
    assert rec.absolute_error == pytest.approx(raw["mean_ms"], abs=0.01) and rec.relative_error == pytest.approx(1.0)
    assert rec.predicted_at == raw["predicted_at"] and rec.kind == "raw" and rec.calibration_method == calibration.CALIBRATION_METHOD
    ev = calibration.evaluate([{"predicted": 10, "observed": 12}, {"predicted": 10, "observed": 8}])
    assert ev["bias_pct"] == 0.0 and ev["raw_mean_abs_error_pct"] == 20.0 and ev["raw_mean_abs_error"] == 2.0
    assert any("optimistic" in x and "Assumption at stake" in x for x in c["explanation"])


# 10 no data leakage in evaluation ----------------------------------------------------------------------------------------------------
def test_correction_accuracy_comes_only_from_held_out_runs():
    # one outlier: fitted on all runs the factor is 1.0 and the in-sample error of 4 runs would be 0; held out, the outlier
    # is predicted with the others' factor (1.0) and its error stays 200%
    ev = calibration.evaluate([{"predicted": 10, "observed": 10 * r} for r in (1.0, 1.0, 1.0, 1.0, 3.0)])
    assert ev["factor"] == 1.0 and ev["loo_error_range_pct"][1] == pytest.approx(200.0)
    assert ev["loo_mean_abs_error_pct"] == pytest.approx(40.0)
    # each held-out factor excludes the run it predicts: with ratios 1,2,3,4,5 the run with ratio 3 is corrected by
    # median(1,2,4,5) = 3.0 -> 0% error; the run with ratio 1 by median(2,3,4,5) = 3.5 -> -71.4%
    ev2 = calibration.evaluate([{"predicted": 10, "observed": 10 * r} for r in (1, 2, 3, 4, 5)])
    assert ev2["loo_error_range_pct"][0] == pytest.approx(-71.4, abs=0.1)
    # a correction that does not beat the raw model out of sample is not applied
    noisy = calibration.evaluate([{"predicted": 10, "observed": 10 * r} for r in (0.5, 2.0, 0.6, 1.8, 1.0)])
    assert noisy["established"] and not noisy["validated"] and not noisy["applied"] and "not applied" in noisy["note"]
    assert calibration.correct(12.0, noisy)["value"] is None


# 11 raw and calibrated predictions are kept apart ------------------------------------------------------------------------------------
def test_raw_v2_and_calibrated_predictions_are_separate(tmp_path):
    engine = sim(tmp_path)
    raw = analytical.predict(BASELINE, {"GET /api/compute": 1}, 10, 1, 1.0, None, [], 10)
    v2 = analytical.predict_v2(BASELINE, {"GET /api/compute": 1}, 10, 1, 1.0, None, [], 10, PROBE)
    key = calibration.group_key(v2, "mean_ms")
    for i, ratio in enumerate([1.2, 1.25, 1.3, 1.22, 1.28]):
        engine.store.put(CALIBRATION_KEY, "calibration", _rec(key, 10.0, 10.0 * ratio, i))
    cal = engine.calibrated(v2)
    assert cal["mean_ms"]["value"] == pytest.approx(v2["mean_ms"] * 1.25, rel=0.01) and v2["mean_ms"] != cal["mean_ms"]["value"]
    assert engine.calibrated(raw)["mean_ms"]["value"] is None                      # v2 history never corrects the raw model
    for p in (raw, v2):
        assert p["label"] == "analytical estimate (not a measurement)" and "measured" not in p["label"].replace("not a measurement", "")
    assert raw["kind"] == "raw" and raw["model_version"] == analytical.MODEL_VERSION_RAW
    assert v2["kind"] == "v2" and v2["model_version"] == analytical.MODEL_VERSION and v2["unobserved"] and v2["assumptions"]
    assert v2["capacity_rps"] == pytest.approx(1000 / 30, rel=0.01) and raw["capacity_rps"] == pytest.approx(50)
    assert "not a statistical confidence interval" in cal["mean_ms"]["note"]


# 12 insufficient evidence -------------------------------------------------------------------------------------------------------------
def test_insufficient_evidence_is_reported_not_filled_in():
    nov2 = analytical.predict_v2(BASELINE, {"GET /api/compute": 1}, 10, 1, 1.0, None, [], 10, None)
    assert nov2["status"] == "insufficient_evidence" and "probe" in nov2["reason"]
    part = analytical.predict_v2(BASELINE, {"GET /api/compute": 1}, 10, 1, 1.0, None, [], 10,
                                 {"endpoints": {"GET /api/compute": {"available": False, "reason": "no success"}}})
    assert part["status"] == "predicted" and part["probe_fallback"] == ["GET /api/compute"]
    f = bottlenecks.detect("a", {"cpus": 1.0, "memory_mb": 512, "workers": 1}, 40,
                           {"status": "measured", "throughput_rps": 20.0, "error_rate_pct": 0.0, "generator": {"sustained": True},
                            "cpu_stat": {"available": True, "cpu_utilization_of_limit": 0.7, "throttled_ratio": 0.0, "periods": 100},
                            "resources": {}}, {"status": "predicted", "saturated": False}, None, None)
    ins = [x for x in f if x["kind"] == "insufficient_evidence"]
    assert any("not observable" in x["impact"] for x in ins)                      # a shortfall nothing observed explains
    assert any(x["evidence"] == "contradiction" for x in ins)                       # the model said stable, the run saturated
    assert not any(x["kind"] in ("cpu_saturation", "memory_pressure") for x in f)
    assert analytical.predict(BASELINE, {"GET /nope": 1}, 10, 1, 1.0, None, [], 10)["status"] == "insufficient_evidence"


# 13 safe experiment limits ----------------------------------------------------------------------------------------------------------------
def test_experiment_plans_show_the_unchanged_safety_limits():
    from backend.reality.models import MAX_DURATION, MAX_REQUESTS, MAX_RPS
    assert (MAX_RPS, MAX_DURATION, MAX_REQUESTS) == (200.0, 120, 20000)            # not raised by v2
    sc = scenario(alternatives=[Alternative(id="a", title="a", resources=Resources(workers=2, cpus=0.5, memory_mb=256))])
    plan = RealitySimulator.experiment_plan(sc, True)
    assert plan["limits"]["max_rps"] == 200.0 and plan["limits"]["request_timeout_s"] == 10 and plan["limits"]["max_inflight"] == 256
    run = next(s for s in plan["steps"] if s["step"] == "run a")
    assert run["container"] == "2 worker(s), 0.5 CPU, 256 MB" and "at most 200 requests" in run["workload"] and "concurrency 1, 4, 8, 16" in run["probe"]
    assert any("never to a deployed or live service" in x for x in plan["isolation"]) and "verified" in plan["cleanup"]
    assert plan["hash"] != RealitySimulator.experiment_plan(scenario(traffic={"rps": 21}), True)["hash"]
    assert plan["hash"] == RealitySimulator.experiment_plan(sc, True)["hash"]
    for bad in ({"rps": 500}, {"duration_seconds": 600}, {"rps": 190, "duration_seconds": 120}):
        with pytest.raises(ValidationError):
            scenario(traffic=bad)
    with pytest.raises(ValidationError):
        Resources(cpus=4)
    with pytest.raises(ValidationError):
        Resources(memory_mb=8192)


# 14 approval ------------------------------------------------------------------------------------------------------------------------------
@pytest.fixture
def doubles(monkeypatch):
    """Containers replaced. The baseline, the probes and the load runs return supplied measurements; pre_drive is
    called like the runner does, with probe.contention_probe returning PROBE."""
    from backend.performance.engineer import runner
    from backend.performance.engineer.models import EndpointStats, Environment, Measurement, Resources as R
    box = {"load": {}, "cpu_stat": {"available": True, "cpu_utilization_of_limit": 0.5, "throttled_ratio": 0.0, "periods": 50,
                                    "throttled_ms": 0.0, "source": "double"}}
    monkeypatch.setattr(probe, "contention_probe", lambda url, eps, workers, stop, requests=40: {**PROBE, "workers": workers})

    def measure(projects, workload, stop=None, on_stage=None, resources=None, drive=None, pre_drive=None):
        label = next(iter(projects))
        m = Measurement(label=label, status="measured", resources=R(samples=3, cpu_avg_pct=40.0, mem_max_mb=80.0))
        env = Environment(method="double (test)", cleanup={"verified": True, "leftover_containers": 0, "leftover_volumes": 0})
        if drive is None:
            m.endpoints = [EndpointStats(method="GET", path=e.path, requests=90, errors=0, error_rate_pct=0.0, median_ms=20.0,
                                         mean_ms=20.4, p95_ms=23.0, rep_medians_ms=[19.5, 20.0, 21.0]) for e in workload.endpoints]
        elif label == "probe":
            m.custom = drive("http://double", stop or (lambda: False))
        else:
            pre = pre_drive("http://double", stop or (lambda: False)) if pre_drive else None
            m.custom = dict(box["load"][label])
            if pre is not None:
                m.custom["pre_drive"] = pre
            m.cpu_stat = box["cpu_stat"]
        return {label: m}, env
    monkeypatch.setattr(runner, "measure", measure)
    return box


def _load(throughput, mean, p95, errors=0.0, sustained=True):
    return {"label": "measured (open-loop load against an isolated copy)", "planned_requests": 200, "sent": 200, "completed_ok": 200,
            "errors": 0, "dropped_by_generator": 0, "timeouts": 0, "error_rate_pct": errors, "throughput_rps": throughput, "mean_ms": mean,
            "p50_ms": mean, "median_ms": mean, "p90_ms": p95, "p95_ms": p95, "p99_ms": p95, "status_codes": {"200": 200},
            "per_endpoint": {}, "timeline": [], "generator_lag_ms": {}, "generator_limited": not sustained,
            "generator": {"sustained": sustained, "reasons": [] if sustained else ["lag"], "process_cpu_pct_of_one_core": 20.0},
            "cancelled": False}


def test_load_runs_need_approval_of_the_previewed_plan(tmp_path, doubles):
    project = write_sample(tmp_path / "app")
    engine = sim(tmp_path)
    sc = scenario()
    with pytest.raises(SimulationError, match="approve"):
        engine.start("p1", project, "u1", sc, run_load=True, approved=False)
    with pytest.raises(SimulationError, match="differs"):
        engine.start("p1", project, "u1", sc, run_load=True, approved=True, plan_hash="0" * 16)
    doubles["load"] = {"current": _load(19.9, 31.0, 60.0)}
    plan = engine.experiment_plan(sc, True)
    s = engine.start("p1", project, "u1", sc, run_load=True, approved=True, plan_hash=plan["hash"])
    assert s.status == "completed" and s.experiment_plan["approved"] and s.experiment_plan["approved_hash"] == plan["hash"]
    # the end-to-end v2 flow on doubles: probe-informed prediction before the load, comparison, calibration, findings
    p2 = s.predictions_v2["current"]
    assert p2["stage"].startswith("before the load") and p2["superseded"]["stage"].startswith("before any run")
    assert s.measurements["current"]["contention_probe"]["endpoints"] and "probe_prediction" not in s.measurements["current"]
    c = s.comparisons["current"]
    assert c["comparable"] and c["rows"] and c["rows_v2"] and set(c["groups"]) >= {"raw:mean_ms", "v2:mean_ms"}
    kinds = {r.kind for r in engine.store.list(CALIBRATION_KEY, "calibration")}
    assert kinds == {"raw", "v2"}
    assert any(f["kind"] == "thread_contention" and f["measurements"]["efficiency"] == {"GET /api/compute": 0.7} for f in s.findings)


@pytest.fixture
def api(tmp_path, doubles, monkeypatch):
    import backend.reality.routes as routes
    import backend.routes.export as export
    from backend.auth.dependencies import get_current_user
    from backend.generation.store import global_generation_store
    project = write_sample(tmp_path / "app")
    monkeypatch.setattr(routes, "global_reality_simulator", sim(tmp_path))
    monkeypatch.setattr(global_generation_store, "get", lambda gid, default=None: {"generation_id": "g", "user_id": "alice",
                        "status": "completed", "project_path": str(project)} if gid == "g" else default)
    monkeypatch.setattr(export, "_safe_project_dir", lambda p: project if p == str(project) else None)
    app = FastAPI()
    app.include_router(routes.reality_router)
    app.dependency_overrides[get_current_user] = lambda: {"id": "alice"}
    return TestClient(app), doubles


def test_api_requires_the_plan_hash_for_load_runs_and_reports_v2(api):
    client, box = api
    base = "/api/projects/g/reality"
    body = {"scenario": json.loads(scenario().model_dump_json())}
    assert client.post(f"{base}/simulations", json={**body, "run_load": True, "approved": True}).status_code == 400   # no plan hash
    plan = client.post(f"{base}/plan", json={**body, "run_load": True}).json()["plan"]
    assert plan["steps"] and plan["hash"]
    box["load"] = {"current": _load(19.9, 31.0, 60.0)}
    r = client.post(f"{base}/simulations", json={**body, "run_load": True, "approved": True, "plan_hash": plan["hash"]})
    assert r.status_code == 202
    sid = r.json()["simulation"]["id"]
    md = client.get(f"{base}/simulations/{sid}/report").text
    for text in ("Model v2 (measured capacity)", "Bottleneck findings (v2)", "Measurements (v2)", "calibration groups"):
        assert text in md, text
    cal = client.get("/api/reality/calibration").json()
    assert cal["method"] == calibration.CALIBRATION_METHOD and all(g["established"] is False for g in cal["groups"])


# 15 Docker cleanup ---------------------------------------------------------------------------------------------------------------------------
def test_containers_and_volumes_are_removed_and_verified_even_when_the_run_fails(tmp_path, monkeypatch):
    import backend.execution.docker_test_sandbox as dts
    import backend.execution.preview_manager as pm
    from backend.performance.engineer import runner
    from backend.performance.engineer.models import Workload
    calls, state = [], {"removed": False}

    def fake(*args, timeout=60):
        calls.append(args)
        out = ""
        if args[:2] == ("rm", "-f"):
            state["removed"] = True
        if args[:2] == ("ps", "-a") and not state["removed"]:
            out = "c1\n"
        return subprocess.CompletedProcess(args, 0, out, "")
    monkeypatch.setattr(pm, "_docker", fake)
    monkeypatch.setattr(pm, "_host_port", lambda c, port: 12345)
    monkeypatch.setattr(pm, "_logs", lambda c: "")
    monkeypatch.setattr(dts, "docker_available", lambda: True)
    monkeypatch.setattr(runner, "wait_ready", lambda *a, **k: "/health")
    project = write_sample(tmp_path / "app")
    res, env = runner.measure({"x": project}, Workload(), lambda: False, drive=lambda url, stop: {"ok": True})
    assert res["x"].status == "measured" and env.cleanup["verified"] and env.cleanup["leftover_containers"] == 0
    assert any(a[:2] == ("rm", "-f") for a in calls) and any(a[:3] == ("volume", "rm", "-f") for a in calls)
    assert res["x"].cpu_stat == {"available": False, "reason": "the container's cgroup cpu.stat could not be read"} or res["x"].cpu_stat["available"]
    calls.clear()
    state["removed"] = False

    def boom(url, stop):
        raise RuntimeError("the drive failed")
    with pytest.raises(RuntimeError):
        runner.measure({"x": project}, Workload(), lambda: False, drive=boom)
    assert any(a[:2] == ("rm", "-f") for a in calls) and any(a[:3] == ("volume", "rm", "-f") for a in calls)   # cleaned up anyway


# 16 regression: v1 behaviour kept ------------------------------------------------------------------------------------------------------------
def test_v1_predictions_and_bottleneck_labels_are_unchanged(tmp_path, doubles):
    p = analytical.predict(BASELINE, {"GET /api/compute": 1}, 25, 1, 1.0, None, [], 10)
    assert p["method"].startswith("M/G/c") and p["utilization"] == pytest.approx(0.5) and p["capacity_rps"] == pytest.approx(50)
    assert p["formulas"] == analytical.FORMULAS and p["assumptions"] == analytical.ASSUMPTIONS
    project = write_sample(tmp_path / "app")
    doubles["load"] = {"current": _load(12.0, 900.0, 2000.0, errors=5.0)}
    s = sim(tmp_path).start("p1", project, "u1", scenario(traffic={"rps": 45}), run_load=True, approved=True)
    assert {"measured bottleneck", "model-predicted bottleneck"} <= {b["label"] for b in s.bottlenecks}       # v1 list kept
    assert s.findings and s.comparisons["current"]["comparable"] is False and "5.0% of requests failed" in s.comparisons["current"]["reason"]
    assert s.predictions["current"]["model_version"] == analytical.MODEL_VERSION_RAW


def test_the_page_shows_v2_results():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2] / "frontend" / "src"
    page = (root / "pages" / "RealitySimulatorPage.jsx").read_text(encoding="utf-8")
    service = (root / "services" / "reality.js").read_text(encoding="utf-8")
    assert "/plan" in service and "plan_hash" in service and "approved: runLoad" in service
    for text in ("Experiment plan", "Bottleneck findings", "model v2", "calibrated", "held-out", "throttl", "generator"):
        assert text in page, text


# genuine ----------------------------------------------------------------------------------------------------------------------------------------
def _docker_ok():
    try:
        from backend.execution.docker_test_sandbox import docker_available
        return docker_available()
    except Exception:
        return False


@pytest.mark.skipif(not _docker_ok(), reason="Docker is not available: the genuine v2 simulation was NOT run")
def test_genuine_v2_measurements_in_containers(tmp_path):
    """Baseline + baseline probe, then 1 CPU and 0.5 CPU alternatives at 20 rps: each container is probed before
    its load (model v2 prediction recorded before the load), the load is measured with cgroup CPU counters and the
    generator measured on its own, and every container and volume is removed and verified."""
    project = write_sample(tmp_path / "app")
    sc = scenario(traffic={"rps": 20, "duration_seconds": 15, "mix": {"GET /api/compute": 1}},
                  alternatives=[Alternative(id="one_cpu", title="1 CPU"), Alternative(id="half_cpu", title="0.5 CPU", resources=Resources(cpus=0.5))])
    engine = sim(tmp_path)
    plan = engine.experiment_plan(sc, True)
    s = engine.start("p1", project, "u1", sc, run_load=True, approved=True, plan_hash=plan["hash"])
    assert s.status == "completed", (s.error, s.stages)
    assert s.baseline["contention_probe"]["status"] == "measured" and s.baseline["contention_probe"]["cleanup"]["verified"]
    for aid in ("one_cpu", "half_cpu"):
        m, p2 = s.measurements[aid], s.predictions_v2[aid]
        assert m["status"] == "measured" and m["cleanup"]["verified"], m.get("cleanup")
        assert m["contention_probe"]["endpoints"]["GET /api/compute"]["available"]
        assert p2["status"] == "predicted" and p2["stage"].startswith("before the load") and p2["predicted_at"] < s.finished_at
        assert m["generator"]["process_cpu_seconds"] is not None and m["p99_ms"] is not None
        cs = m["cpu_stat"]
        assert cs["available"] and cs["cpu_seconds"] > 0 and cs["periods"] is not None, cs
    assert s.measurements["half_cpu"]["cpu_stat"]["periods"] > 0                   # a CPU quota is enforced at 0.5 CPU
    print(json.dumps({aid: {"raw_mean": s.predictions[aid].get("mean_ms"), "v2_mean": s.predictions_v2[aid].get("mean_ms"),
                            "observed_mean": s.measurements[aid].get("mean_ms"), "observed_tput": s.measurements[aid].get("throughput_rps"),
                            "cpu": s.measurements[aid]["cpu_stat"], "comparison": s.comparisons[aid].get("reason") or s.comparisons[aid].get("rows_v2"),
                            "findings": [f["kind"] for f in s.findings if f["alternative"] == aid]} for aid in ("one_cpu", "half_cpu")}, default=str))
