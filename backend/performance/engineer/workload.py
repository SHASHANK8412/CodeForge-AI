"""
Load generation and statistics.

The load generator runs in AIForge's process and only sends HTTP requests to the app, which runs
in its sandbox container (published on 127.0.0.1); no project code runs here. Latency is wall-clock
time per request (time.perf_counter around the full request/response, connection reused per
worker), so it includes the local network stack.
"""

import math
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Dict, List, Optional, Tuple

from backend.performance.engineer.models import Endpoint, EndpointStats, Workload


def percentile(values: List[float], pct: float) -> Optional[float]:
    """Nearest-rank percentile (pct in 0-100); None for no data."""
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, math.ceil(pct / 100 * len(ordered)))
    return ordered[min(rank, len(ordered)) - 1]


def run_endpoint(base_url: str, endpoint: Endpoint, requests: int, concurrency: int, timeout: float,
                 should_stop: Optional[Callable[[], bool]] = None,
                 max_seconds: Optional[float] = None) -> Tuple[List[float], Dict[str, int], int, float]:
    """
    Send up to `requests` requests with `concurrency` workers, stopping new requests after
    `max_seconds`. Returns (latencies of successful requests in ms, status-code counts, error count,
    elapsed seconds). Errors are non-2xx/3xx answers and failed requests (timeouts, refused connections).
    """
    import httpx
    url = base_url.rstrip("/") + endpoint.path
    lock = threading.Lock()
    latencies: List[float] = []
    codes: Dict[str, int] = {}
    errors = [0]
    remaining = [requests]
    stop_at = time.perf_counter() + max_seconds if max_seconds else None

    def take() -> bool:
        with lock:
            if remaining[0] <= 0 or (should_stop is not None and should_stop()):
                return False
            if stop_at is not None and time.perf_counter() > stop_at:
                return False
            remaining[0] -= 1
            return True

    def worker():
        with httpx.Client(timeout=timeout) as client:
            while take():
                start = time.perf_counter()
                try:
                    resp = client.request(endpoint.method, url, json=endpoint.body)
                    elapsed = (time.perf_counter() - start) * 1000
                    key = str(resp.status_code)
                    ok = resp.status_code < 400
                except httpx.HTTPError as e:
                    elapsed, key, ok = None, type(e).__name__, False
                with lock:
                    codes[key] = codes.get(key, 0) + 1
                    if ok:
                        latencies.append(elapsed)
                    else:
                        errors[0] += 1

    began = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        for _ in range(concurrency):
            pool.submit(worker)
    return latencies, codes, errors[0], time.perf_counter() - began


def summarize(endpoint: Endpoint, reps: List[Tuple[List[float], Dict[str, int], int, float]]) -> EndpointStats:
    """Pool all repetitions for percentiles; keep each repetition's median for the run-to-run spread."""
    samples = [x for lat, _, _, _ in reps for x in lat]
    codes: Dict[str, int] = {}
    for _, c, _, _ in reps:
        for k, v in c.items():
            codes[k] = codes.get(k, 0) + v
    total = sum(sum(c.values()) for _, c, _, _ in reps)
    errors = sum(e for _, _, e, _ in reps)
    rep_medians = [round(statistics.median(lat), 3) for lat, _, _, _ in reps if lat]
    rep_rps = [round(len(lat) / el, 2) for lat, _, _, el in reps if el > 0]
    med = statistics.median(samples) if samples else None
    spread = None
    if len(rep_medians) >= 2 and med:
        spread = round((max(rep_medians) - min(rep_medians)) / med * 100, 2)
    r = lambda v: round(v, 3) if v is not None else None  # noqa: E731
    return EndpointStats(
        method=endpoint.method, path=endpoint.path, requests=total, errors=errors,
        error_rate_pct=round(errors / total * 100, 3) if total else 0.0, status_codes=codes,
        mean_ms=r(statistics.fmean(samples)) if samples else None, median_ms=r(med),
        p95_ms=r(percentile(samples, 95)), p99_ms=r(percentile(samples, 99)),
        min_ms=r(min(samples)) if samples else None, max_ms=r(max(samples)) if samples else None,
        throughput_rps=round(statistics.fmean(rep_rps), 2) if rep_rps else None,
        rep_medians_ms=rep_medians, rep_throughput_rps=rep_rps, spread_pct=spread,
    )


def warm_up(base_url: str, workload: Workload) -> None:
    """Unmeasured requests, so connection setup, caches and lazy imports settle before measuring."""
    if workload.warmup_requests <= 0:
        return
    for ep in workload.endpoints:
        run_endpoint(base_url, ep, workload.warmup_requests, min(2, workload.concurrency),
                     workload.request_timeout_seconds)
