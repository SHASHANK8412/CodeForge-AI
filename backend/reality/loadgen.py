"""
Open-loop load generator (requests arrive on a schedule whether or not earlier ones finished - unlike the
Performance Engineer's closed-loop workers, so queues can actually build up).

Arrivals are Poisson with the pattern's rate at each moment (seeded, so a scenario sends the same schedule
every time), each one picks an endpoint by the traffic weights. Bounded by the scenario limits (Traffic) and
`max_inflight`; requests the generator could not send because too many were in flight are counted as
"dropped by the generator" - a limit of the test rig, reported separately from the app's errors. The
generator's own scheduling lag is reported too: a large lag means the generator, not the app, fell behind.

v2 measurements (summarize): request counts by outcome (succeeded, failed by status, failed by connection error,
timed out) - failed requests always count against reliability; latency mean / median / p90 / p95 / p99 (nearest
rank, successful requests) and the mean over all completed requests; and the generator measured on its own:
the AIForge process CPU time during the run, the achieved send rate against the scheduled rate, scheduling-lag
percentiles and drops. A generator that did not sustain the requested rate makes the run unsuitable for comparing
with the model. `provenance` names the source of every metric; a metric that could not be observed is None with
the reason, never 0.
"""

import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List, Optional

from backend.reality.analytical import rate_at

MAX_INFLIGHT = 256
SUSTAIN_RATIO = 0.95            # the generator must send at least 95% of the scheduled requests on time
MAX_LAG_P95_MS = 200.0          # ... with a p95 scheduling lag below this


def schedule(traffic: Dict[str, Any], seed: int = 7) -> List[Dict[str, Any]]:
    rng = random.Random(seed)
    mix = traffic["mix"]
    keys, weights = list(mix), list(mix.values())
    out, t = [], 0.0
    while True:
        rate = rate_at(traffic, t)
        t += rng.expovariate(rate)
        if t >= traffic["duration_seconds"]:
            return out
        out.append({"at": t, "endpoint": rng.choices(keys, weights)[0]})


def _pct(values: List[float], p: float) -> Optional[float]:
    """Nearest-rank percentile (the same definition as the Performance Engineer's workload statistics)."""
    from backend.performance.engineer.workload import percentile
    v = percentile(values, p)
    return round(v, 2) if v is not None else None


def run(base_url: str, traffic: Dict[str, Any], should_stop: Callable[[], bool], timeout: float = 10.0,
        seed: int = 7, max_inflight: int = MAX_INFLIGHT, warmup: int = 10) -> Dict[str, Any]:
    import httpx
    plan = schedule(traffic, seed)
    client = httpx.Client(timeout=timeout, limits=httpx.Limits(max_connections=max_inflight, max_keepalive_connections=32))
    lock = threading.Lock()
    inflight = [0]
    results: List[Dict[str, Any]] = []
    dropped: List[float] = []
    try:
        for ep in list(traffic["mix"])[:3]:                       # warm-up, not recorded
            for _ in range(max(1, warmup // 3)):
                try:
                    client.get(base_url.rstrip("/") + ep.split(" ", 1)[1])
                except httpx.HTTPError:
                    pass

        def send(item, start_wall):
            path = item["endpoint"].split(" ", 1)[1]
            began = time.perf_counter()
            rec = {"at": item["at"], "endpoint": item["endpoint"], "lag_ms": round((began - start_wall - item["at"]) * 1000, 2)}
            try:
                r = client.get(base_url.rstrip("/") + path)
                rec.update(status=r.status_code, ms=round((time.perf_counter() - began) * 1000, 2))
            except httpx.HTTPError as e:
                rec.update(status=None, error=type(e).__name__, timeout=isinstance(e, httpx.TimeoutException),
                           ms=round((time.perf_counter() - began) * 1000, 2))
            with lock:
                inflight[0] -= 1
                results.append(rec)

        pool = ThreadPoolExecutor(max_workers=max_inflight, thread_name_prefix="reality-load")
        cpu0 = time.process_time()
        start = time.perf_counter()
        for item in plan:
            if should_stop():
                break
            delay = start + item["at"] - time.perf_counter()
            if delay > 0:
                time.sleep(delay)
            with lock:
                if inflight[0] >= max_inflight:
                    dropped.append(item["at"])
                    continue
                inflight[0] += 1
            pool.submit(send, item, start)
        send_window = time.perf_counter() - start               # until the last request was handed to a thread
        pool.shutdown(wait=True)
        elapsed = time.perf_counter() - start
        cpu_s = time.process_time() - cpu0
    finally:
        client.close()
    gen = {"process_cpu_seconds": round(cpu_s, 3), "send_window_s": round(send_window, 3), "max_inflight": max_inflight,
           "request_timeout_s": timeout, "seed": seed, "warmup_requests": warmup}
    return summarize(traffic, plan, results, dropped, elapsed, cancelled=should_stop(), generator=gen)


def summarize(traffic: Dict[str, Any], plan: List[Dict[str, Any]], results: List[Dict[str, Any]], dropped: List[float],
              elapsed: float, cancelled: bool = False, generator: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    import os
    ok = [r for r in results if r.get("status") is not None and 200 <= r["status"] < 400]
    errors = [r for r in results if r not in ok]
    timeouts = [r for r in results if r.get("timeout")]
    http_failed = [r for r in errors if r.get("status") is not None]
    conn_failed = [r for r in errors if r.get("status") is None and not r.get("timeout")]
    lat = [r["ms"] for r in ok]
    all_lat = [r["ms"] for r in results if r.get("ms") is not None]
    duration = traffic["duration_seconds"]
    timeline = []
    for sec in range(duration):
        in_sec = [r for r in results if sec <= r["at"] < sec + 1]
        good = [r["ms"] for r in in_sec if r in ok]
        timeline.append({"second": sec, "offered_rps": round(rate_at(traffic, sec), 2), "sent": len(in_sec),
                         "errors": sum(1 for r in in_sec if r not in ok), "p50_ms": _pct(good, 50),
                         "dropped": sum(1 for d in dropped if sec <= d < sec + 1)})
    per = {}
    for ep in traffic["mix"]:
        e_ok = [r["ms"] for r in ok if r["endpoint"] == ep]
        per[ep] = {"requests": sum(1 for r in results if r["endpoint"] == ep), "mean_ms": round(sum(e_ok) / len(e_ok), 2) if e_ok else None,
                   "p95_ms": _pct(e_ok, 95)}
    lags = [r["lag_ms"] for r in results]
    codes: Dict[str, int] = {}
    for r in results:
        k = str(r.get("status") or r.get("error"))
        codes[k] = codes.get(k, 0) + 1
    # the generator, measured on its own
    gen = dict(generator or {})
    scheduled_rps = len(plan) / duration if duration else None
    window = gen.get("send_window_s") or elapsed
    achieved = len(results) / window if window else None
    lag95 = _pct(lags, 95)
    send_ratio = (len(results) / len(plan)) if plan else None
    reasons = []
    if dropped:
        reasons.append(f"{len(dropped)} request(s) dropped: {gen.get('max_inflight', MAX_INFLIGHT)} already in flight")
    if lag95 is not None and lag95 > MAX_LAG_P95_MS:
        reasons.append(f"p95 scheduling lag {lag95} ms > {MAX_LAG_P95_MS:.0f} ms")
    if send_ratio is not None and send_ratio < SUSTAIN_RATIO and not cancelled:
        reasons.append(f"sent {len(results)} of {len(plan)} scheduled requests ({send_ratio:.0%})")
    cpu_s = gen.get("process_cpu_seconds")
    gen.update({"label": "measured: the load generator itself (host side, separate from the app container)",
                "scheduled_requests": len(plan), "scheduled_rps": round(scheduled_rps, 2) if scheduled_rps else None,
                "sent": len(results), "achieved_send_rps": round(achieved, 2) if achieved else None,
                "send_ratio": round(send_ratio, 4) if send_ratio is not None else None,
                "lag_ms": {"p50": _pct(lags, 50), "p95": lag95, "p99": _pct(lags, 99)},
                "process_cpu_pct_of_one_core": round(100 * cpu_s / elapsed, 1) if cpu_s is not None and elapsed else None,
                "host_cpu_count": os.cpu_count(), "sustained": not reasons, "reasons": reasons,
                "note": "process CPU covers the whole AIForge process (the generator's threads and anything else it did)"})
    n = len(results)
    out = {
        "label": "measured (open-loop load against an isolated copy)", "planned_requests": len(plan),
        "sent": n, "completed_ok": len(ok), "errors": len(errors), "dropped_by_generator": len(dropped),
        "failed_http": len(http_failed), "failed_connection": len(conn_failed), "timeouts": len(timeouts),
        "success_rate_pct": round(100 * len(ok) / n, 2) if n else None,
        "error_rate_pct": round(100 * len(errors) / n, 2) if n else None,
        "throughput_rps": round(len(ok) / elapsed, 2) if elapsed else None, "elapsed_s": round(elapsed, 2),
        "mean_ms": round(sum(lat) / len(lat), 2) if lat else None, "median_ms": _pct(lat, 50), "p50_ms": _pct(lat, 50),
        "p90_ms": _pct(lat, 90), "p95_ms": _pct(lat, 95), "p99_ms": _pct(lat, 99),
        "all_requests_mean_ms": round(sum(all_lat) / len(all_lat), 2) if all_lat else None,
        "status_codes": codes, "per_endpoint": per, "timeline": timeline,
        "generator_lag_ms": {"mean": round(sum(lags) / len(lags), 2) if lags else None, "p95": lag95},
        "generator_limited": bool(reasons), "generator": gen,
        "workload": {"pattern": traffic["pattern"], "rps": traffic["rps"], "start_rps": traffic.get("start_rps"),
                     "duration_seconds": duration, "mix": traffic["mix"], "arrivals": "Poisson (open loop, seeded)"},
        "cancelled": cancelled,
    }
    src = "load generator (wall-clock per request, AIForge host)"
    out["provenance"] = {
        **{k: src for k in ("sent", "completed_ok", "errors", "timeouts", "failed_http", "failed_connection",
                            "success_rate_pct", "error_rate_pct", "throughput_rps")},
        **{k: (src + ", successful requests, nearest-rank percentile") if out[k] is not None else
           "unavailable: no successful request" for k in ("mean_ms", "median_ms", "p90_ms", "p95_ms", "p99_ms")},
        "generator": "AIForge process (time.process_time) and the generator's own schedule",
    }
    return out
