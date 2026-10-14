"""
Deterministic candidate selection. No model output is consulted here.

1. Mandatory constraints, per candidate (any failure makes it ineligible, whatever its speed):
     generated     a change exists and stays inside the plan's files
     correctness   Autopilot's comparison with the baseline: no regression and nothing unverified
     security      no new critical/high Security Guardian finding in the changed files
     performance   the measurement exists and nothing regressed (latency, errors, throughput, memory)
2. Ranking among eligible candidates with the plan's weights; every input and contribution is recorded.
3. Only a winner whose target endpoints were measured faster beyond the noise (decision "improved") is
   a validated improvement; otherwise the experiment's outcome says why not.
"""

from typing import Any, Dict, List, Optional, Tuple

from backend.evolution_engine.models import Candidate, Experiment, Weights


def _clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def constraints(c: Candidate) -> List[Dict[str, Any]]:
    out = []
    out.append({"name": "generated", "passed": bool(c.changes) and c.status not in ("failed", "duplicate"),
                "detail": c.generation_error or (f"{len(c.changes)} file(s) changed" if c.changes else "no change")})
    corr = c.correctness or {}
    out.append({"name": "correctness", "passed": bool(corr.get("accepted")),
                "detail": "; ".join(corr.get("regressions", []) + corr.get("unverified", [])) or
                          ("flaky test result" if corr.get("flaky") else
                           f"no regression (tests: {(corr.get('tests') or {}).get('counts') or 'not run'})" if corr.get("accepted")
                           else "not evaluated")})
    sec = c.security or {}
    out.append({"name": "security", "passed": sec.get("status") == "evaluated" and not sec.get("new_serious"),
                "detail": ("new: " + "; ".join(sec["new_serious"])) if sec.get("new_serious") else
                          (sec.get("detail") or "not evaluated")})
    perf = c.performance or {}
    measured = perf.get("decision") not in (None, "not_measured")
    out.append({"name": "performance", "passed": measured and perf.get("decision") != "regressed",
                "detail": "; ".join(perf.get("reasons", [])[:3]) or perf.get("decision") or "not measured"})
    return out


def score(c: Candidate, w: Weights) -> Tuple[float, Dict[str, Any]]:
    perf = c.performance or {}
    rows = perf.get("target_rows") or []
    change = sum((r.get("median_change_pct") or 0.0) for r in rows) / len(rows) if rows else 0.0
    err = max((r["after"].get("error_rate_pct") or 0.0 for r in rows), default=0.0)
    mem = (perf.get("resources") or {}).get("peak_memory_change_pct")
    sec_other = len((c.security or {}).get("new_other") or [])
    m = c.maintainability or {}
    inputs = {
        "performance": (f"target median {change:+.1f}%", _clamp(-change)),
        "security": (f"{sec_other} new lower-severity finding(s)", _clamp(100 - 20 * sec_other)),
        "reliability": (f"error rate {err}%", _clamp(100 - 10 * err)),
        "maintainability": (f"{m.get('changed_lines', 0)} changed lines, branches {m.get('branches_delta', 0):+d}",
                            _clamp(100 - m.get("changed_lines", 0) / 4 - 10 * max(0, m.get("branches_delta", 0)))),
        "resource_efficiency": (f"peak memory {mem:+.1f}%" if mem is not None else "peak memory not measured",
                                _clamp(100 - 2 * max(0.0, mem)) if mem is not None else 50.0),
    }
    weights = w.model_dump()
    total_w = sum(weights.values()) or 1.0
    breakdown, total = {}, 0.0
    for k, (value, s) in inputs.items():
        contrib = s * weights[k] / total_w
        total += contrib
        breakdown[k] = {"input": value, "score": round(s, 1), "weight": round(weights[k] / total_w, 3),
                        "contribution": round(contrib, 2)}
    return round(total, 2), breakdown


def select(exp: Experiment) -> Tuple[Optional[str], str, List[str]]:
    """(selected candidate id or None, outcome, reasons). Updates candidates in place."""
    for c in exp.candidates:
        c.constraints = constraints(c)
        failed = [x for x in c.constraints if not x["passed"]]
        c.eligible = not failed
        c.rejection_reasons = [f"{x['name']}: {x['detail']}" for x in failed]
        c.score, c.score_breakdown = (score(c, exp.plan.weights) if c.eligible else (None, {}))
        if not c.eligible and c.failure_kind is None:
            c.failure_kind = _failure_kind(c, failed)
    eligible = [c for c in exp.candidates if c.eligible]
    if eligible:
        def key(c: Candidate):
            rows = (c.performance or {}).get("target_rows") or [{}]
            return (-(c.score or 0.0), rows[0].get("median_change_pct") or 0.0,
                    (c.maintainability or {}).get("changed_lines", 0), c.id)
        best = sorted(eligible, key=key)[0]
        if best.performance.get("decision") == "improved":
            return best.id, "awaiting_approval", [f"{best.id} ({best.strategy}) passed every mandatory constraint and was "
                                                  f"measured faster: " + "; ".join(best.performance.get("reasons", [])[:2]),
                                                  f"ranked first with score {best.score} of {len(eligible)} eligible candidate(s)"]
        # a change beyond the threshold that the noise does not let us confirm is uncertain, not "no improvement"
        unconfirmed = any(c.performance.get("evidence") == "insufficient" or any(
            (r.get("median_change_pct") or 0) <= -exp.plan.thresholds.min_improvement_pct
            for r in c.performance.get("target_rows") or []) for c in eligible)
        return None, "inconclusive" if unconfirmed else "no_improvement", [
            f"{len(eligible)} candidate(s) passed the mandatory constraints but none was measured faster beyond the "
            "noise: " + "; ".join(r for c in eligible for r in c.performance.get("reasons", [])[:1])]
    kinds = {c.failure_kind for c in exp.candidates}
    if kinds & {"infrastructure", "flaky", "insufficient_evidence"}:
        return None, "inconclusive", ["no candidate could be judged reliably: " + "; ".join(
            f"{c.id}: {c.failure_kind}" for c in exp.candidates if c.failure_kind in ("infrastructure", "flaky", "insufficient_evidence"))]
    if any(c.failure_kind == "candidate_defect" for c in exp.candidates):
        return None, "regression", ["every candidate broke a mandatory constraint: " + "; ".join(
            f"{c.id}: {c.rejection_reasons[0]}" for c in exp.candidates if c.rejection_reasons)]
    return None, "failed", ["no candidate was produced: " + "; ".join(
        f"{c.id}: {c.generation_error or c.status}" for c in exp.candidates)]


def _failure_kind(c: Candidate, failed: List[Dict[str, Any]]) -> str:
    names = {x["name"] for x in failed}
    corr = c.correctness or {}
    if "generated" in names:
        return "generation_failed"
    if corr.get("flaky"):
        return "flaky"
    if "correctness" in names and corr.get("unverified") and not corr.get("regressions"):
        return "infrastructure"
    if "performance" in names and (c.performance or {}).get("decision") in (None, "not_measured") \
            and names == {"performance"}:
        return "insufficient_evidence" if (c.performance or {}).get("infrastructure") is False else "infrastructure"
    return "candidate_defect"
