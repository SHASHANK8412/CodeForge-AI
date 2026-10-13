"""
Analytical capacity model (an M/M/c queue per alternative). Every number it returns is a PREDICTION, derived
from measured service times and stated assumptions; the formulas and inputs are returned with it.

Inputs
  S_i       measured median service time of endpoint i at low load (one request at a time), from the baseline run
  S_i^lo/hi the fastest / slowest repetition median of that run (uncertainty)
  w_i       traffic weight of endpoint i (assumption);  lambda = arrival rate in requests/s (assumption)
  workers   uvicorn worker processes;  cpus = container CPU limit (alternative)
  D         added latency of an external dependency for the endpoints that call it (assumption)

Model (assumptions are listed in ASSUMPTIONS)
  speed     = min(1, cpus / workers)                       relative CPU speed per worker vs the baseline (1 CPU)
  S'_i      = S_i / speed                                  service time under the alternative's CPU limit
  E[S]      = sum_i w_i S'_i ;  c = workers ;  mu = 1/E[S] ;  a = lambda E[S] ;  rho = a / c
  Erlang C  C(c,a) = (a^c/c! * c/(c-a)) / (sum_{k<c} a^k/k! + a^c/c! * c/(c-a))      (rho < 1)
  wait      Wq = C / (c mu - lambda) ;  Wq95 = max(0, ln(C/0.05) / (c mu - lambda))  (M/M/c waiting tail)
  variability  Cs^2 = (sigma/E[S])^2 with sigma ~ (p95 - p50)/1.645 from the baseline (normal approximation);
            Allen-Cunneen M/G/c: Wq and Wq95 are multiplied by (1 + Cs^2)/2 (Poisson arrivals). Without the
            baseline's spread the factor is 1 (plain M/M/c, which overestimates waiting for steady service times)
  response  R_i = S'_i + Wq (+ D for dependent endpoints) ;  R95_i ~ 1.5 S'_i + Wq95 (+ D)
  saturated (rho >= 1): throughput = c / E[S] ; the queue grows by (lambda - c/E[S]) requests/s ; the mean latency
            over a run of T seconds ~ E[S] + (lambda - X) T / (2 X)  (linear queue growth, a rough bound)
  threads   sync handlers hold one of 40 threadpool slots per worker for S'_i + D:
            rho_threads = sum_dep lambda_i (S'_i + D) / (40 workers) ; >= 1 means the threadpool saturates first

Model v2 (MODEL_VERSION "reality-model/2", predict_v2) - the same M/G/c queue, but its service capacity is
MEASURED instead of assumed: the contention probe (probe.py) gives, in the alternative's own configuration,
  S1_i      median latency one request at a time (the response-time floor, network included)
  S_eff_i   workers / Xc_i, where Xc_i is the closed-loop throughput at concurrency 2 x workers
            (captures GIL hand-offs, thread scheduling and CFS throttling that v1 assumed away)
  E[S] = sum_i w_i S_eff_i ;  rho = lambda E[S] / workers ;  R_i = S1_i + Wq (+ D) ;  R95_i ~ 1.5 S1_i + Wq95 (+ D)
Endpoints the probe could not measure fall back to the v1 scaling, and the prediction lists them. The v1 ("raw")
prediction is always kept next to it, unchanged, so both can be compared with what a run measures.
"""

import math
from typing import Any, Dict, List, Optional

MODEL_VERSION_RAW = "reality-model/1"     # v1: service time scaled by the CPU limit (assumed perfect sharing)
MODEL_VERSION = "reality-model/2"         # v2: service capacity measured by the contention probe

ASSUMPTIONS = [
    "arrivals are Poisson and service times exponential (M/M/c); real traffic and code can differ",
    "request handling is CPU-bound Python: one worker uses at most one CPU, so c = workers",
    "a CPU limit below the number of workers slows every worker proportionally (speed = cpus / workers)",
    "service times measured one request at a time are the per-request CPU cost (no contention at low load)",
    "external dependency latency is waiting, not CPU work; synchronous handlers hold a threadpool slot "
    "(40 per worker) while they wait",
    "the database and other shared resources are not modelled separately; their cost is inside the measured service time",
    "network latency between the load generator and the app is included in the measured service time",
]
FORMULAS = [
    "speed = min(1, cpus / workers);  S'_i = S_i / speed",
    "E[S] = sum_i w_i S'_i;  a = lambda * E[S];  rho = a / workers",
    "C(c,a) = (a^c/c! * c/(c-a)) / (sum_{k<c} a^k/k! + a^c/c! * c/(c-a))",
    "Wq = C / (c/E[S] - lambda);  Wq95 = max(0, ln(C/0.05) / (c/E[S] - lambda))",
    "M/G/c (Allen-Cunneen): Wq and Wq95 x (1 + Cs^2)/2, Cs = ((p95 - p50)/1.645) / mean from the baseline",
    "R_i = S'_i + Wq (+ D);  R95_i ~ 1.5 S'_i + Wq95 (+ D)",
    "if rho >= 1: X = c / E[S]; queue growth = lambda - X; mean latency over T ~ E[S] + (lambda - X) T / (2 X)",
    "rho_threads = sum_dep lambda_i (S'_i + D) / (40 * workers)",
]


def erlang_c(c: int, a: float) -> float:
    if a >= c:
        return 1.0
    top = (a ** c / math.factorial(c)) * (c / (c - a))
    return top / (sum(a ** k / math.factorial(k) for k in range(c)) + top)


def _one(services_ms: Dict[str, float], mix: Dict[str, float], lam: float, workers: int, cpus: float,
         dep_ms: float, dependent: List[str], duration_s: float, variability: float = 1.0,
         response_ms: Optional[Dict[str, float]] = None, measured_capacity: bool = False) -> Dict[str, Any]:
    """services_ms: per-server service time for queueing; response_ms (v2): the response-time floor per endpoint.
    measured_capacity: services_ms already are per-server times in this configuration (no CPU scaling)."""
    speed = 1.0 if measured_capacity else min(1.0, cpus / workers)
    s = {k: v / 1000.0 / speed for k, v in services_ms.items()}               # seconds, under the alternative
    floor = {k: (response_ms[k] / 1000.0 if response_ms and k in response_ms else s[k]) for k in s}
    total_w = sum(mix.values())
    w = {k: mix[k] / total_w for k in mix}
    es = sum(w[k] * s[k] for k in w)
    c = workers
    a = lam * es
    rho = a / c
    x_cap = c / es
    d = dep_ms / 1000.0
    lam_dep = sum(lam * w[k] for k in w if k in dependent)
    rho_threads = sum(lam * w[k] * (s[k] + d) for k in w if k in dependent) / (40 * workers) if dependent else 0.0
    out: Dict[str, Any] = {"utilization": round(rho, 4), "capacity_rps": round(x_cap, 2), "offered_rps": lam,
                           "mean_service_ms": round(es * 1000, 3), "servers": c, "cpu_speed": round(speed, 3),
                           "threadpool_utilization": round(rho_threads, 4), "dependency_rps": round(lam_dep, 2)}
    if rho < 1:
        cw = erlang_c(c, a)
        gap = x_cap - lam
        wq = cw / gap * variability
        wq95 = (max(0.0, math.log(cw / 0.05) / gap) if cw > 0.05 else 0.0) * variability
        per = {k: {"mean_ms": round((floor[k] + wq + (d if k in dependent else 0)) * 1000, 2),
                   "p95_ms": round((1.5 * floor[k] + wq95 + (d if k in dependent else 0)) * 1000, 2)} for k in w}
        out.update(saturated=False, wait_probability=round(cw, 4), mean_wait_ms=round(wq * 1000, 3),
                   throughput_rps=round(lam, 2), per_endpoint=per,
                   mean_ms=round(sum(w[k] * per[k]["mean_ms"] for k in w), 2),
                   p95_ms=round(max(per[k]["p95_ms"] for k in w), 2), queue_growth_rps=0.0)
    else:
        growth = lam - x_cap
        mean_s = es + growth * duration_s / (2 * x_cap)
        out.update(saturated=True, wait_probability=1.0, throughput_rps=round(x_cap, 2), queue_growth_rps=round(growth, 2),
                   mean_ms=round(mean_s * 1000 + (d * 1000 if dependent else 0), 1),
                   p95_ms=None, per_endpoint={}, mean_wait_ms=None,
                   note=f"saturated: the queue grows by about {growth:.1f} requests/s; latency keeps rising for the "
                        f"whole run (the mean above is a rough bound for {duration_s:.0f} s)")
    if rho_threads >= 1:
        out["threadpool_saturated"] = True
        out["note"] = (out.get("note", "") + " " if out.get("note") else "") + (
            "the threadpool saturates first: dependent requests wait for a free thread")
    return out


def predict(baseline: Dict[str, Any], mix: Dict[str, float], lam: float, workers: int, cpus: float,
            dep_ms: Optional[float], dependent: List[str], duration_s: float) -> Dict[str, Any]:
    """Point prediction plus low/high bounds from the fastest/slowest measured repetition medians."""
    eps = baseline["endpoints"]
    missing = [k for k in mix if k not in eps or eps[k].get("median_ms") is None]
    if missing:
        return {"status": "insufficient_evidence", "reason": f"no measured service time for {missing}"}
    mid = {k: eps[k]["median_ms"] for k in mix}
    lo = {k: min(eps[k]["rep_medians_ms"] or [eps[k]["median_ms"]]) for k in mix}
    hi = {k: max(eps[k]["rep_medians_ms"] or [eps[k]["median_ms"]]) for k in mix}
    cs2 = service_variability(eps, mix)
    factor = (1 + cs2) / 2 if cs2 is not None else 1.0
    point = _one(mid, mix, lam, workers, cpus, dep_ms or 0.0, dependent, duration_s, factor)
    fast = _one(lo, mix, lam, workers, cpus, dep_ms or 0.0, dependent, duration_s, factor)
    slow = _one(hi, mix, lam, workers, cpus, dep_ms or 0.0, dependent, duration_s, factor)
    bounds = {}
    for metric in ("throughput_rps", "mean_ms", "p95_ms", "utilization"):
        vals = [v for v in (fast.get(metric), slow.get(metric)) if v is not None]
        if vals:
            bounds[metric] = [round(min(vals), 2), round(max(vals), 2)]
    method = "M/G/c (Allen-Cunneen)" if cs2 is not None else "M/M/c (Erlang C)"
    return {"status": "predicted", "label": "analytical estimate (not a measurement)", "method": method,
            "model_version": MODEL_VERSION_RAW, "kind": "raw",
            "service_cv2": round(cs2, 4) if cs2 is not None else None, "waiting_factor": round(factor, 4),
            **point, "bounds": bounds, "formulas": FORMULAS, "assumptions": ASSUMPTIONS,
            "inputs": {"service_ms": mid, "service_ms_range": {k: [lo[k], hi[k]] for k in mix}, "mix": mix,
                       "arrival_rps": lam, "workers": workers, "cpus": cpus, "dependency_latency_ms": dep_ms or 0.0,
                       "dependent_endpoints": dependent, "baseline_run": baseline.get("run_id")}}


def service_variability(eps: Dict[str, Dict[str, Any]], mix: Dict[str, float]) -> Optional[float]:
    """Traffic-weighted squared coefficient of variation of the service time, from the baseline's mean, median and
    p95 (sigma ~ (p95 - p50) / 1.645). None when the baseline lacks them (the model then stays M/M/c)."""
    total = sum(mix.values())
    acc = 0.0
    for k, w in mix.items():
        e = eps.get(k) or {}
        mean, p50, p95 = e.get("mean_ms"), e.get("median_ms"), e.get("p95_ms")
        if not mean or p50 is None or p95 is None:
            return None
        sigma = max(0.0, p95 - p50) / 1.645
        acc += w / total * min(4.0, (sigma / mean) ** 2)
    return acc


def rate_at(traffic: Dict[str, Any], t: float) -> float:
    """Requests/s at time t for a traffic pattern (constant, linear ramp, or a burst in the middle)."""
    pat, dur = traffic["pattern"], traffic["duration_seconds"]
    if pat == "constant":
        return traffic["rps"]
    if pat == "ramp":
        return traffic["start_rps"] + (traffic["rps"] - traffic["start_rps"]) * min(1.0, t / dur)
    start = (dur - traffic["burst_seconds"]) / 2
    return traffic["rps"] if start <= t < start + traffic["burst_seconds"] else traffic["start_rps"]


def saturation_onset(traffic: Dict[str, Any], capacity_rps: float) -> Optional[float]:
    """The first second at which the offered rate exceeds the predicted capacity (None if never)."""
    for t in range(traffic["duration_seconds"]):
        if rate_at(traffic, t) > capacity_rps:
            return float(t)
    return None


def cost(prediction: Dict[str, Any], baseline: Dict[str, Any], prices: Optional[Dict[str, Any]], target_util: float,
         lam: float) -> Dict[str, Any]:
    """Resource need for the offered load at the target utilisation; priced only with user-supplied prices."""
    es_s = prediction.get("mean_service_ms", 0) / 1000.0 * prediction.get("cpu_speed", 1.0)   # CPU-seconds per request
    vcpus = lam * es_s / target_util
    mem_mb = baseline.get("peak_memory_mb")
    out = {"label": "estimate from the model and your inputs", "vcpus_needed": round(vcpus, 3),
           "formula": "vCPUs = lambda * E[S at 1 CPU] / target utilisation", "target_utilization": target_util,
           "memory_per_instance_mb": mem_mb}
    if not prices:
        out["monthly_cost"] = None
        out["note"] = "not estimated: enter unit prices to estimate a cost"
        return out
    instances = max(1, math.ceil(vcpus))
    gb = (mem_mb or 0) / 1024 * instances
    monthly = (math.ceil(vcpus * 100) / 100 * prices["vcpu_hour"] + gb * prices.get("gb_hour", 0.0)) * 730
    out.update(monthly_cost=round(monthly, 2), currency=prices.get("currency", "USD"), instances=instances,
               cost_formula="(vCPUs * vcpu_hour + GB * gb_hour) * 730 hours")
    return out


UNOBSERVED = [
    "database query plans and data volume (their cost is only inside the measured service time)",
    "caches warming up or being evicted under load",
    "background jobs, garbage-collection pauses and other tenants of the machine",
    "network variance between real clients and the app (the generator runs on the AIForge host)",
]
ASSUMPTIONS_V2 = [
    "arrivals are Poisson (open loop); service-time variability comes from the baseline (Allen-Cunneen M/G/c)",
    "the capacity under concurrency measured by the contention probe (closed loop, 2 x workers) holds at the "
    "scenario's load; contention that only appears at higher concurrency is not captured",
    "the response-time floor is the probe's one-at-a-time latency in this configuration (network included)",
    "external dependency latency is waiting, not CPU work (threadpool of 40 slots per worker)",
]


def predict_v2(baseline: Dict[str, Any], mix: Dict[str, float], lam: float, workers: int, cpus: float,
               dep_ms: Optional[float], dependent: List[str], duration_s: float,
               probe: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Model v2: M/G/c with the probe's measured capacity. Without a usable probe there is no v2 prediction (the
    raw v1 prediction still exists); nothing is invented to fill the gap."""
    if not probe or not probe.get("endpoints"):
        return {"status": "insufficient_evidence", "model_version": MODEL_VERSION, "kind": "v2",
                "reason": "no contention probe for this configuration"}
    raw = predict(baseline, mix, lam, workers, cpus, dep_ms, dependent, duration_s)
    if raw.get("status") != "predicted":
        return {**raw, "model_version": MODEL_VERSION, "kind": "v2"}
    eps = baseline["endpoints"]
    speed = min(1.0, cpus / workers)
    s_eff, floor, fallback = {}, {}, []
    for k in mix:
        pr = (probe["endpoints"] or {}).get(k) or {}
        if pr.get("available"):
            s_eff[k], floor[k] = pr["s_eff_ms"], pr["s1_ms"]
        else:
            s_eff[k], floor[k] = eps[k]["median_ms"] / speed, eps[k]["median_ms"] / speed
            fallback.append(k)
    cs2 = service_variability(eps, mix)
    factor = (1 + cs2) / 2 if cs2 is not None else 1.0
    point = _one(s_eff, mix, lam, workers, cpus, dep_ms or 0.0, dependent, duration_s, factor, floor, measured_capacity=True)
    # bounds: the baseline's repetition spread applied to the measured service times
    bounds = {}
    for metric in ("throughput_rps", "mean_ms", "p95_ms", "utilization"):
        lo_hi, mid = raw["bounds"].get(metric), raw.get(metric)
        if lo_hi and mid and point.get(metric) is not None:
            bounds[metric] = [round(point[metric] * lo_hi[0] / mid, 2), round(point[metric] * lo_hi[1] / mid, 2)]
    return {"status": "predicted", "label": "analytical estimate (not a measurement)", "kind": "v2",
            "method": ("M/G/c (Allen-Cunneen)" if cs2 is not None else "M/M/c (Erlang C)") + " + measured capacity",
            "model_version": MODEL_VERSION, "service_cv2": round(cs2, 4) if cs2 is not None else None,
            "waiting_factor": round(factor, 4), **point, "bounds": bounds, "assumptions": ASSUMPTIONS_V2,
            "unobserved": UNOBSERVED, "probe_fallback": fallback,
            "probe": {"label": probe.get("label"), "scaled": bool(probe.get("scaled")), "concurrency": probe.get("concurrency")},
            "formulas": ["S_eff_i = workers / Xc_i (probe, concurrency 2 x workers);  E[S] = sum_i w_i S_eff_i",
                         "rho = lambda E[S] / workers;  Wq, Wq95 as M/G/c (Allen-Cunneen)",
                         "R_i = S1_i + Wq (+ D);  R95_i ~ 1.5 S1_i + Wq95 (+ D)"],
            "inputs": {"s_eff_ms": s_eff, "s1_ms": floor, "mix": mix, "arrival_rps": lam, "workers": workers, "cpus": cpus,
                       "dependency_latency_ms": dep_ms or 0.0, "dependent_endpoints": dependent,
                       "baseline_run": baseline.get("run_id")}}
