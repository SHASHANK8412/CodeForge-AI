"""
Contention probe: the app's service capacity measured under concurrency, in the exact resource configuration
(workers, CPU limit) of an alternative, before its load run.

The v1 model scales the low-load service time by the CPU limit (speed = cpus / workers) and assumes requests
then share the CPU perfectly. Real Python services lose capacity under concurrency (GIL hand-offs, thread
scheduling, CFS quota throttling - which at a fractional CPU limit costs far more than the proportional
slowdown), so v1 predictions were optimistic under load. The probe measures capacity instead of assuming it:

  0. warm-up at the highest level (not measured), so every worker process has served requests
  1. one request at a time (closed loop): S1_i = median latency (the response-time floor), X1_i = requests / s
  2. closed loop at concurrency c in LEVELS x workers: X_c,i = requests / s.  One client at a time leaves the server
     idle while each request travels (client, port forwarding), so a low concurrency under-reads capacity; the
     levels go high enough for the server to be the bottleneck.
  3. measured capacity per endpoint = max_c X_c,i (the peak sustained throughput);
     effective service time per server  S_eff_i = workers / capacity_i
     contention efficiency e_i = capacity_i / (workers / S1_i)   (1 = perfect sharing; < 1 = capacity lost)

Every number is a measurement with its request counts; an endpoint without successful requests is reported as
unavailable (the model then falls back to the v1 scaling for it, and says so).
"""

import statistics
import time
from typing import Any, Callable, Dict, List, Optional

LEVELS = (2, 4, 8)                  # x workers, after the one-at-a-time level
SECONDS_PER_LEVEL = 8.0
WARMUP_PER_SLOT = 3                 # unmeasured warm-up requests per concurrent client at the highest level
WARMUP_SECONDS = 4.0


def contention_probe(url: str, endpoints: List[str], workers: int, stop: Callable[[], bool], requests: int = 40,
                     timeout: float = 10.0, max_seconds: float = SECONDS_PER_LEVEL) -> Dict[str, Any]:
    from backend.performance.engineer.models import Endpoint
    from backend.performance.engineer.workload import run_endpoint
    w = max(1, int(workers))
    started = time.perf_counter()
    per: Dict[str, Any] = {}
    for key in endpoints:
        if stop():
            break
        ep = Endpoint(method="GET", path=key.split(" ", 1)[1])
        # warm-up (not measured) at the highest level, so every worker process has handled requests (imports,
        # lazy initialisation) before anything is measured
        run_endpoint(url, ep, WARMUP_PER_SLOT * LEVELS[-1] * w, LEVELS[-1] * w, timeout, stop, WARMUP_SECONDS)
        lat1, codes1, err1, el1 = run_endpoint(url, ep, requests, 1, timeout, stop, max_seconds)
        levels = [{"concurrency": 1, "x_rps": round(len(lat1) / el1, 2) if el1 > 0 else None, "requests": len(lat1), "errors": err1,
                   "median_ms": round(statistics.median(lat1), 2) if lat1 else None}]
        for k in LEVELS:
            if stop():
                break
            c = k * w
            lat, codes, err, el = run_endpoint(url, ep, requests * c, c, timeout, stop, max_seconds)
            levels.append({"concurrency": c, "x_rps": round(len(lat) / el, 2) if el > 0 and lat else None, "requests": len(lat),
                           "errors": err, "median_ms": round(statistics.median(lat), 2) if lat else None})
        xs = [lv for lv in levels if lv["x_rps"]]
        if not lat1 or not xs:
            per[key] = {"available": False, "reason": "no successful request in the probe", "levels": levels}
            continue
        peak = max(xs, key=lambda lv: lv["x_rps"])
        s1 = statistics.median(lat1)
        per[key] = {"available": True, "s1_ms": round(s1, 3), "x1_rps": levels[0]["x_rps"], "xc_rps": peak["x_rps"],
                    "concurrency": peak["concurrency"], "s_eff_ms": round(1000 * w / peak["x_rps"], 3),
                    "efficiency": round(peak["x_rps"] / (w * 1000 / s1), 3), "levels": levels,
                    "errors": sum(lv["errors"] for lv in levels)}
    return {"label": "measured: closed-loop probe at concurrency 1 and " + ", ".join(f"{k}x" for k in LEVELS)
                     + " workers in this configuration; capacity = the peak throughput",
            "workers": w, "concurrency": [1] + [k * w for k in LEVELS], "endpoints": per,
            "seconds": round(time.perf_counter() - started, 2)}


def scaled_from_baseline(probe: Optional[Dict[str, Any]], workers: int, cpus: float) -> Optional[Dict[str, Any]]:
    """For a configuration that was not probed (predict-only): the baseline probe (1 worker, 1 CPU) scaled by the
    v1 CPU rule. Labelled as scaled, not measured - the probe shows fractional CPU limits cost more than this."""
    if not probe:
        return None
    speed = min(1.0, cpus / workers)
    per = {}
    for k, v in (probe.get("endpoints") or {}).items():
        if not v.get("available"):
            per[k] = v
            continue
        s_eff_one = v["s_eff_ms"]                          # 1 worker at 1 CPU
        per[k] = {**v, "s1_ms": round(v["s1_ms"] / speed, 3), "s_eff_ms": round(s_eff_one / speed, 3),
                  "xc_rps": round(workers * 1000 / (s_eff_one / speed), 2)}
    return {**probe, "label": "scaled from the baseline probe (1 worker, 1 CPU) by speed = cpus / workers - not measured "
                              "in this configuration", "scaled": True, "workers": workers, "endpoints": per}
