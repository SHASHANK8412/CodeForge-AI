"""
Evidence-based bottleneck detection. Each rule looks only at what the runtime actually observed (or at a labelled
model prediction) and states its evidence strength; nothing is claimed as a cause without the measurement it
rests on, and nothing the runtime cannot observe (database, cache, background jobs) is reported.

  kind                          rule (thresholds)                                                  evidence
  cpu_saturation                cgroup CPU seconds / (wall x CPU limit) >= 0.85                    strong
                                (docker stats CPU% >= 85% of the limit, when cgroup is unavailable) moderate
  cpu_throttling                cgroup nr_throttled / nr_periods >= 0.25 (>= 0.10)                  strong (moderate)
  thread_contention             contention probe efficiency < 0.8 in this configuration            moderate
  insufficient_worker_capacity  served < 90% of offered, generator sustained, CPU < 60% of limit   moderate
                                model: threadpool saturation (dependency waits)                    weak (predicted)
  external_service_latency      dependency run: slowed - normal >= 0.8 x the added latency         strong
  memory_pressure               docker stats peak memory >= 90% of the limit                       strong
  load_generator                the generator did not sustain the rate (drops, lag, shortfall)     strong
                                generator process CPU >= 80% of one core                           moderate
  insufficient_evidence         a shortfall or error with no observed resource signal, missing     -
                                counters, or the model and the measurement disagreeing (contradiction)
"""

from typing import Any, Dict, List, Optional


def _f(i: int, alt: str, kind: str, evidence: str, measurements: Dict[str, Any], method: str, impact: str,
       experiment: str) -> Dict[str, Any]:
    return {"id": f"bn_{alt}_{i}_{kind}", "alternative": alt, "kind": kind, "evidence": evidence,
            "measurements": measurements, "method": method, "impact": impact, "recommended_experiment": experiment}


def detect(alt: str, resources: Dict[str, Any], offered_rps: Optional[float], meas: Dict[str, Any],
           raw: Optional[Dict[str, Any]], v2: Optional[Dict[str, Any]], dependency_ms: Optional[float]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    add = lambda *a: out.append(_f(len(out) + 1, alt, *a))  # noqa: E731
    if meas.get("status") != "measured":
        add("insufficient_evidence", "-", {"status": meas.get("status"), "error": meas.get("error")}, "run status",
            "nothing was measured for this alternative", "fix the run's error and run it again")
        return out
    cpus, mem_limit = float(resources.get("cpus") or 1.0), resources.get("memory_mb")
    # dependency-latency alternatives (Chaos sandbox, low load)
    if dependency_ms is not None:
        normal, slowed = (meas.get("normal") or {}).get("mean_ms"), (meas.get("slowed") or {}).get("mean_ms")
        if normal is not None and slowed is not None and slowed - normal >= 0.8 * dependency_ms:
            add("external_service_latency", "strong", {"normal_mean_ms": normal, "slowed_mean_ms": slowed, "added_ms": dependency_ms},
                "the same endpoints measured with the dependency stub at normal speed and slowed (Chaos sandbox)",
                f"each dependent request takes about {slowed - normal:.0f} ms longer",
                "add a timeout / cache in front of the dependency and measure again (Chaos Engineer)")
        else:
            add("insufficient_evidence", "-", {"normal": meas.get("normal"), "slowed": meas.get("slowed")},
                "dependency run", "the added latency was not observed as expected", "check the stub routes and env var")
        return out
    cs = meas.get("cpu_stat") or {}
    gen = meas.get("generator") or {}
    served = meas.get("throughput_rps")
    sustained = gen.get("sustained", not meas.get("generator_limited"))
    shortfall = bool(offered_rps and served is not None and sustained and served < 0.9 * offered_rps)
    signals = 0
    if not sustained:
        add("load_generator", "strong", {"reasons": gen.get("reasons"), "send_ratio": gen.get("send_ratio"),
                                         "lag_ms": gen.get("lag_ms"), "dropped": meas.get("dropped_by_generator")},
            "the generator's own schedule against what it sent", "the run shows the test rig's limit, not the app's",
            "lower the rate or the duration, or run the generator on a less loaded machine")
    if (gen.get("process_cpu_pct_of_one_core") or 0) >= 80:
        add("load_generator", "moderate", {"process_cpu_pct_of_one_core": gen["process_cpu_pct_of_one_core"]},
            "AIForge process CPU time during the run", "the generator may compete with the app for the host's CPU",
            "repeat at a lower rate and compare latencies")
    util = cs.get("cpu_utilization_of_limit") if cs.get("available") else None
    if util is not None and util >= 0.85:
        signals += 1
        add("cpu_saturation", "strong", {"cpu_utilization_of_limit": util, "cpu_seconds": cs.get("cpu_seconds"),
                                         "wall_seconds": cs.get("wall_seconds"), "cpu_limit": cpus},
            cs.get("source", "cgroup cpu.stat"), "the CPU limit is (nearly) fully used: more load only queues",
            "repeat with a higher CPU limit or more workers (an alternative) and compare throughput")
    elif util is None:
        dstat = (meas.get("resources") or {}).get("cpu_avg_pct")
        if dstat is not None and dstat >= 0.85 * cpus * 100:
            signals += 1
            add("cpu_saturation", "moderate", {"docker_stats_cpu_avg_pct": dstat, "cpu_limit_pct": cpus * 100},
                "docker stats samples (cgroup counters unavailable)", "the CPU limit is probably fully used",
                "repeat with a higher CPU limit and compare")
    ratio = cs.get("throttled_ratio") if cs.get("available") else None
    if ratio is not None and ratio >= 0.10:
        signals += 1
        add("cpu_throttling", "strong" if ratio >= 0.25 else "moderate",
            {"throttled_ratio": ratio, "throttled_ms": cs.get("throttled_ms"), "periods": cs.get("periods")},
            cs.get("source", "cgroup cpu.stat"),
            f"the kernel paused the app in {ratio:.0%} of its CPU periods ({cs.get('throttled_ms')} ms in total): "
            "latency includes these pauses", "repeat with a whole-CPU limit (cpus >= 1) and compare the tail latency")
    probe = meas.get("contention_probe") or {}
    effs = {k: v["efficiency"] for k, v in (probe.get("endpoints") or {}).items() if v.get("available")}
    if effs and min(effs.values()) < 0.8:
        signals += 1
        add("thread_contention", "moderate", {"efficiency": effs, "concurrency": probe.get("concurrency")},
            "contention probe (closed loop, concurrency 2 x workers vs 1, in this configuration)",
            "concurrent requests lose capacity (GIL hand-offs, scheduling or throttling); the probe cannot tell these apart",
            "compare with more worker processes (a process per CPU) at the same CPU limit")
    if shortfall and util is not None and util < 0.6:
        signals += 1
        add("insufficient_worker_capacity", "moderate", {"served_rps": served, "offered_rps": offered_rps,
                                                         "cpu_utilization_of_limit": util, "workers": resources.get("workers")},
            "served rate vs offered rate with the CPU counters", "requests queued while CPU capacity was left unused",
            "repeat with more workers at the same CPU limit")
    for p, label in ((raw, "raw"), (v2, "v2")):
        if p and p.get("threadpool_saturated"):
            add("insufficient_worker_capacity", "weak", {"threadpool_utilization": p.get("threadpool_utilization"), "model": label},
                f"model prediction ({p.get('model_version')}), not a measurement", "dependency waits may exhaust the threadpool",
                "run the dependency-latency alternative to measure it")
    peak = (meas.get("resources") or {}).get("mem_max_mb")
    if peak is not None and mem_limit and peak >= 0.9 * mem_limit:
        signals += 1
        add("memory_pressure", "strong", {"mem_max_mb": peak, "memory_limit_mb": mem_limit}, "docker stats samples",
            "the container is close to its memory limit (risk of OOM kills)", "repeat with a higher memory limit")
    if (shortfall or (meas.get("error_rate_pct") or 0) > 1) and not signals and sustained:
        add("insufficient_evidence", "-", {"served_rps": served, "offered_rps": offered_rps, "error_rate_pct": meas.get("error_rate_pct"),
                                           "cpu_counters": "available" if cs.get("available") else cs.get("reason")},
            "no observed resource signal explains the shortfall or the errors",
            "the cause is not observable with the current runtime (it could be in the app's code or data access)",
            "profile the endpoint (Performance Engineer) or examine the app's logs")
    if not cs.get("available"):
        add("insufficient_evidence", "-", {"cpu_counters": cs.get("reason", "not collected")}, "cgroup cpu.stat",
            "CPU saturation and throttling cannot be assessed from kernel counters for this run",
            "run on a Docker host that exposes cgroup cpu.stat in containers")
    for p, label in ((raw, "raw"), (v2, "v2")):
        if p and p.get("status") == "predicted" and served is not None and offered_rps and sustained:
            measured_saturated = served < 0.9 * offered_rps
            if bool(p.get("saturated")) != measured_saturated:
                add("insufficient_evidence", "contradiction", {"model": label, "predicted_saturated": bool(p.get("saturated")),
                                                               "served_rps": served, "offered_rps": offered_rps},
                    f"{label} model prediction vs measurement",
                    f"the {label} model {'predicted' if p.get('saturated') else 'did not predict'} saturation but the run "
                    f"{'was' if measured_saturated else 'was not'} saturated",
                    "treat this prediction as unreliable for this configuration until calibration covers it")
    return out
