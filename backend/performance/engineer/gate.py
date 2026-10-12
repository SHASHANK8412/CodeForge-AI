"""
Performance regression gate: decides whether a candidate is faster than the baseline.

Per endpoint, the median latency of all requests is compared. A difference counts only if
  * it is at least the threshold (min_improvement_pct / max_regression_pct), and
  * it is larger than noise_factor x the run-to-run spread of either version (max - min of the
    per-repetition medians in ms; with 5+ repetitions the highest and lowest are left out), and
  * the per-repetition medians do not overlap (every candidate repetition is faster than every
    baseline repetition, or the reverse),
otherwise the endpoint is "no clear change". The decision:
  regressed     - any endpoint slower, error rate up, throughput down or memory up beyond the limits
  improved      - every target endpoint clearly faster and nothing regressed
  inconclusive  - neither (including: a target endpoint changed less than the noise)
  not_measured  - either version could not be measured
"""

from typing import Any, Dict, List, Optional

from backend.performance.engineer.models import Comparison, EndpointStats, Measurement, Thresholds


def _pct(after: Optional[float], before: Optional[float]) -> Optional[float]:
    if after is None or not before:
        return None
    return round((after - before) / before * 100, 2)


def _spread_ms(e: EndpointStats) -> float:
    """Run-to-run spread of the per-repetition medians. With 5 or more repetitions the single highest and
    lowest are left out, so one disturbed repetition (seen on Docker Desktop) does not mask a real change;
    every repetition still has to be separated from the other version's (no overlap), see endpoint_change."""
    reps = sorted(e.rep_medians_ms)
    if len(reps) >= 5:
        reps = reps[1:-1]
    return (reps[-1] - reps[0]) if len(reps) > 1 else 0.0


def endpoint_change(b: EndpointStats, a: EndpointStats, t: Thresholds) -> Dict[str, Any]:
    delta = _pct(a.median_ms, b.median_ms)
    # Run-to-run noise in milliseconds (the larger of the two versions' spreads), expressed relative to the
    # baseline median. A spread taken relative to each version's own median would make large improvements
    # unprovable: a candidate 8x faster has a tiny median, so its spread looks huge in percent.
    noise = round(max(_spread_ms(b), _spread_ms(a)) / b.median_ms * 100, 2) if b.median_ms else 0.0
    no_overlap_faster = bool(a.rep_medians_ms and b.rep_medians_ms and max(a.rep_medians_ms) < min(b.rep_medians_ms))
    no_overlap_slower = bool(a.rep_medians_ms and b.rep_medians_ms and min(a.rep_medians_ms) > max(b.rep_medians_ms))
    single_rep = len(a.rep_medians_ms) < 2 or len(b.rep_medians_ms) < 2
    if delta is None:
        verdict, why = "not_measured", "no successful requests to compare"
    elif single_rep:
        # without two repetitions per version the run-to-run variation is unknown: no verdict either way
        verdict, why = "no_clear_change", (f"median {b.median_ms} -> {a.median_ms} ms ({delta}%): only one repetition, "
                                           "so run-to-run variation is unknown")
    elif delta <= -t.min_improvement_pct and abs(delta) > t.noise_factor * noise and no_overlap_faster:
        verdict, why = "faster", f"median {b.median_ms} -> {a.median_ms} ms ({delta}%), beyond {t.noise_factor}x the run-to-run spread ({noise}%)"
    elif delta >= t.max_regression_pct and delta > t.noise_factor * noise and no_overlap_slower:
        verdict, why = "slower", f"median {b.median_ms} -> {a.median_ms} ms (+{delta}%), beyond the run-to-run spread ({noise}%)"
    else:
        reasons = []
        if abs(delta) < (t.min_improvement_pct if delta < 0 else t.max_regression_pct):
            reasons.append(f"{delta}% is below the {t.min_improvement_pct if delta < 0 else t.max_regression_pct}% threshold")
        if abs(delta) <= t.noise_factor * noise:
            reasons.append(f"within {t.noise_factor}x the run-to-run spread ({noise}%)")
        if not (no_overlap_faster or no_overlap_slower):
            reasons.append("the repetitions of the two versions overlap")
        if single_rep:
            reasons.append("only one repetition, so run-to-run variation is unknown")
        verdict, why = "no_clear_change", f"median {b.median_ms} -> {a.median_ms} ms ({delta}%): " + "; ".join(reasons)
    err_delta = round(a.error_rate_pct - b.error_rate_pct, 3)
    rps_delta = _pct(a.throughput_rps, b.throughput_rps)
    return {"endpoint": f"{b.method} {b.path}", "verdict": verdict, "reason": why, "median_change_pct": delta,
            "before": b.model_dump(), "after": a.model_dump(), "error_rate_change_pp": err_delta,
            "throughput_change_pct": rps_delta, "noise_pct": noise}


def compare(baseline: Measurement, candidate: Measurement, thresholds: Thresholds,
            targets: Optional[List[str]] = None) -> Comparison:
    if baseline.status != "measured" or candidate.status != "measured":
        missing = [m for m in (baseline, candidate) if m.status != "measured"]
        return Comparison(decision="not_measured", baseline=baseline, candidate=candidate, thresholds=thresholds,
                          reasons=[f"{m.label}: {m.status} - {m.error or 'no data'}" for m in missing])
    before = {f"{e.method} {e.path}": e for e in baseline.endpoints}
    after = {f"{e.method} {e.path}": e for e in candidate.endpoints}
    rows = [endpoint_change(before[k], after[k], thresholds) for k in before if k in after]
    targets = [t for t in (targets or []) if t in before] or list(before)
    reasons: List[str] = []
    regressed = False
    for r in rows:
        if r["verdict"] == "slower":
            regressed = True
            reasons.append(f"{r['endpoint']} is slower: {r['reason']}")
        if r["error_rate_change_pp"] > thresholds.max_error_rate_increase_pp:
            regressed = True
            reasons.append(f"{r['endpoint']} error rate +{r['error_rate_change_pp']} percentage points")
        if r["throughput_change_pct"] is not None and r["throughput_change_pct"] < -thresholds.max_throughput_drop_pct \
                and r["verdict"] != "faster":
            regressed = True
            reasons.append(f"{r['endpoint']} throughput {r['throughput_change_pct']}%")
    mem_change = _pct(candidate.resources.mem_max_mb, baseline.resources.mem_max_mb)
    cpu_change = _pct(candidate.resources.cpu_avg_pct, baseline.resources.cpu_avg_pct)
    if mem_change is not None and mem_change > thresholds.max_memory_increase_pct:
        regressed = True
        reasons.append(f"peak memory +{mem_change}% ({baseline.resources.mem_max_mb} -> {candidate.resources.mem_max_mb} MB)")
    target_rows = [r for r in rows if r["endpoint"] in targets]
    if regressed:
        decision = "regressed"
    elif target_rows and all(r["verdict"] == "faster" for r in target_rows):
        decision = "improved"
        reasons += [f"{r['endpoint']}: {r['reason']}" for r in target_rows]
    else:
        decision = "inconclusive"
        reasons += [f"{r['endpoint']}: {r['reason']}" for r in target_rows if r["verdict"] != "faster"]
    return Comparison(decision=decision, reasons=reasons, per_endpoint=rows, baseline=baseline, candidate=candidate,
                      thresholds=thresholds,
                      resources={"peak_memory_change_pct": mem_change, "avg_cpu_change_pct": cpu_change,
                                 "before": baseline.resources.model_dump(), "after": candidate.resources.model_dump()})
