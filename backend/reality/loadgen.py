"""
Open-loop load generator (requests arrive on a schedule whether or not earlier ones finished - unlike the
Performance Engineer's closed-loop workers, so queues can actually build up).

Arrivals are Poisson with the pattern's rate at each moment (seeded, so a scenario sends the same schedule
every time), each one picks an endpoint by the traffic weights. Bounded by the scenario limits (Traffic) and
`max_inflight`; requests the generator could not send because too many were in flight are counted as
"dropped by the generator" - a limit of the test rig, reported separately from the app's errors. The
generator's own scheduling lag is reported too: a large lag means the generator, not the app, fell behind.
"""

import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List, Optional

from backend.reality.analytical import rate_at

MAX_INFLIGHT = 256


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
    if not values:
        return None
    v = sorted(values)
    return round(v[min(len(v) - 1, int(round(p / 100 * (len(v) - 1))))], 2)


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
                rec.update(status=None, error=type(e).__name__, ms=round((time.perf_counter() - began) * 1000, 2))
            with lock:
                inflight[0] -= 1
                results.append(rec)

        pool = ThreadPoolExecutor(max_workers=max_inflight, thread_name_prefix="reality-load")
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
        pool.shutdown(wait=True)
        elapsed = time.perf_counter() - start
    finally:
        client.close()
    return summarize(traffic, plan, results, dropped, elapsed, cancelled=should_stop())


def summarize(traffic: Dict[str, Any], plan: List[Dict[str, Any]], results: List[Dict[str, Any]], dropped: List[float],
              elapsed: float, cancelled: bool = False) -> Dict[str, Any]:
    ok = [r for r in results if r.get("status") is not None and 200 <= r["status"] < 400]
    errors = [r for r in results if r not in ok]
    lat = [r["ms"] for r in ok]
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
    return {
        "label": "measured (open-loop load against an isolated copy)", "planned_requests": len(plan),
        "sent": len(results), "completed_ok": len(ok), "errors": len(errors), "dropped_by_generator": len(dropped),
        "error_rate_pct": round(100 * len(errors) / len(results), 2) if results else None,
        "throughput_rps": round(len(ok) / elapsed, 2) if elapsed else None, "elapsed_s": round(elapsed, 2),
        "mean_ms": round(sum(lat) / len(lat), 2) if lat else None, "p50_ms": _pct(lat, 50), "p95_ms": _pct(lat, 95),
        "p99_ms": _pct(lat, 99), "status_codes": codes, "per_endpoint": per, "timeline": timeline,
        "generator_lag_ms": {"mean": round(sum(lags) / len(lags), 2) if lags else None, "p95": _pct(lags, 95)},
        "generator_limited": bool(dropped) or ((_pct(lags, 95) or 0) > 200),
        "cancelled": cancelled,
    }
