"""
Engineering Memory: what each experiment tried, in which context, and what was measured.

Records are written only from evaluated experiments (one per candidate strategy) and updated with the
final outcome after promotion. Retrieval labels how far a past result applies:

  direct     same project, same file, same kind of problem
  related    same kind of problem with the same data-access style in another place or project
  weak       same kind of problem, different data-access style (an analogy, not evidence)

Nothing is generalised into a rule: each record carries its scope. A strategy that failed with a
candidate defect for the same file is not proposed again unless the user gives a new justification;
failures caused by infrastructure or flaky tests are never held against a strategy.
"""

import uuid
from typing import Any, Dict, List, Optional, Tuple

from backend.evolution_engine.models import Experiment, MemoryRecord, Strategy

MEMORY_KEY = "_engineering_memory"


def _store():
    from backend.evolution_engine.service import global_evolution_engine
    return global_evolution_engine.store


def evidence_quality(perf: Dict[str, Any]) -> str:
    rows = perf.get("target_rows") or []
    if perf.get("decision") in (None, "not_measured") or not rows:
        return "insufficient"
    reps = min((len(r["after"].get("rep_medians_ms") or []) for r in rows), default=0)
    clear = all(r["verdict"] in ("faster", "slower") for r in rows)
    if reps >= 3 and clear:
        return "strong"
    if reps >= 2 and clear:
        return "moderate"
    return "weak"


def record_experiment(exp: Experiment, store=None) -> List[MemoryRecord]:
    store = store or _store()
    ctx = exp.plan.model_dump().get("context") or {}
    context = {"file": exp.opportunity.file, "endpoint": exp.opportunity.endpoint, **ctx}
    out = []
    for c in exp.candidates:
        if c.status in ("duplicate", "cancelled", "pending"):
            continue
        perf = c.performance or {}
        target = (perf.get("target_rows") or [{}])[0]
        if c.id == exp.selected:
            result = "won"
        elif c.eligible:
            result = "eligible"
        elif c.failure_kind in ("infrastructure", "flaky", "insufficient_evidence"):
            result = "inconclusive"
        elif c.status == "failed":
            result = "failed"
        else:
            result = "rejected"
        rec = MemoryRecord(
            id="mem_" + uuid.uuid4().hex[:12], experiment_id=exp.id, project_id=exp.project_id,
            category=exp.opportunity.category, context=context, strategy=c.strategy, selected=c.id == exp.selected,
            result=result, reasons=c.rejection_reasons[:6], failure_kind=c.failure_kind,
            measured={"decision": perf.get("decision"), "median_change_pct": target.get("median_change_pct"),
                      "noise_pct": target.get("noise_pct"),
                      "repetitions": len((target.get("after") or {}).get("rep_medians_ms") or []),
                      "endpoint": target.get("endpoint")},
            evidence_quality=evidence_quality(perf),
            scope=(f"measured on {exp.opportunity.endpoint} of project {exp.project_id} at revision "
                   f"{(exp.source_revision or '')[:12]} with the plan's workload; not a general rule"))
        store.put(MEMORY_KEY, "memory", rec)
        out.append(rec)
    return out


def set_final_outcome(experiment_id: str, outcome: str, store=None) -> None:
    store = store or _store()
    for r in store.list(MEMORY_KEY, "memory"):
        if r.experiment_id == experiment_id and r.selected:
            store.update(MEMORY_KEY, "memory", r.id, lambda x: setattr(x, "final_outcome", outcome))


def applicability(r: MemoryRecord, project_id: str, category: str, context: Dict[str, Any]) -> Optional[str]:
    if r.category != category:
        return None
    if r.project_id == project_id and r.context.get("file") == context.get("file"):
        return "direct"
    if r.context.get("data_access") and r.context.get("data_access") == context.get("data_access"):
        return "related"
    return "weak"


def related(project_id: str, category: str, context: Dict[str, Any], store=None, limit: int = 20) -> List[Dict[str, Any]]:
    try:
        records = (store or _store()).list(MEMORY_KEY, "memory")
    except Exception:  # noqa: BLE001 - memory is optional context
        return []
    out = []
    for r in records:
        level = applicability(r, project_id, category, context)
        if level:
            out.append({"applicability": level, **r.model_dump(mode="json")})
    order = {"direct": 0, "related": 1, "weak": 2}
    q = {"strong": 0, "moderate": 1, "weak": 2, "insufficient": 3}
    return sorted(out, key=lambda x: (order[x["applicability"]], q[x["evidence_quality"]], x["recorded_at"]))[:limit]


def guide(strategies: List[Strategy], history: List[Dict[str, Any]], overrides: Dict[str, str]
          ) -> Tuple[List[Strategy], List[Dict[str, Any]]]:
    """Order strategies by past measured wins and drop ones that failed here before (unless justified)."""
    kept, suppressed = [], []
    for s in strategies:
        direct_defects = [h for h in history if h["strategy"] == s.id and h["applicability"] == "direct"
                          and h["result"] in ("failed", "rejected") and h["failure_kind"] == "candidate_defect"]
        if direct_defects and s.id not in overrides:
            suppressed.append({"strategy": s.id, "experiments": sorted({h["experiment_id"] for h in direct_defects}),
                               "reasons": direct_defects[-1]["reasons"][:3],
                               "note": "failed here before with a candidate defect; give a new justification to try it again"})
            continue
        if s.id in overrides:
            s.memory_note = f"tried again despite earlier failures: {overrides[s.id]}"
        wins = [h for h in history if h["strategy"] == s.id and h["result"] == "won" and h["evidence_quality"] in ("strong", "moderate")]
        if wins:
            s.memory_note = (s.memory_note or "") + f" won {len(wins)} past experiment(s) " + \
                f"({', '.join(sorted({h['applicability'] for h in wins}))} evidence)"
        kept.append(s)
    won = lambda s: -sum(1 for h in history if h["strategy"] == s.id and h["result"] == "won")  # noqa: E731
    return sorted(kept, key=won), suppressed
