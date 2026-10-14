"""
Evidence-based consensus and the Critical Reviewer (both deterministic; no model decides anything here).

  decide(proposals, priorities)   a proposal that violates a mandatory constraint is out, whatever else it
                                  offers; the rest are ranked by the weighted criterion scores their evidence
                                  supports (0..1 each). How many agents back a proposal is never counted. A tie
                                  within the margin, or a missing score for the leader, goes to a person.
  review(...)                     contract coverage, unsupported assumptions (calls or routes outside the
                                  contract), field drift, missing test evidence and new critical/high security
                                  findings - each finding names the artifact it is based on.
"""

from typing import Any, Dict, List, Optional

from backend.swarm.interfaces import check_contract
from backend.swarm.models import Proposal

DEFAULT_PRIORITIES = {"contract_conformance": 0.35, "correctness_evidence": 0.25, "security": 0.2,
                      "change_cost": 0.1, "maintainability": 0.1}
TIE_MARGIN = 0.05


def decide(proposals: List[Proposal], priorities: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    pr = {**DEFAULT_PRIORITIES, **(priorities or {})}
    total = sum(pr.values()) or 1.0
    eligible = [p for p in proposals if not p.violates]
    rows = []
    for p in proposals:
        missing = [k for k in pr if k not in p.scores]
        score = round(sum(p.scores.get(k, 0.0) * w for k, w in pr.items()) / total, 3)
        rows.append({"proposal": p.id, "title": p.title, "eligible": not p.violates, "violates": p.violates,
                     "score": score if not p.violates else None, "missing_evidence": missing,
                     "breakdown": {k: {"score": p.scores.get(k), "weight": round(w / total, 3)} for k, w in pr.items()}})
    ranked = sorted([r for r in rows if r["eligible"]], key=lambda r: -r["score"])
    out = {"method": "mandatory constraints first, then weighted evidence scores; votes are not counted",
           "priorities": pr, "rows": rows}
    if not eligible:
        return {**out, "outcome": "escalate", "reason": "every proposal violates a mandatory constraint"}
    leader = ranked[0]
    if leader["missing_evidence"]:
        return {**out, "outcome": "escalate", "reason": f"insufficient evidence for the leading proposal: {leader['missing_evidence']}"}
    if len(ranked) > 1 and leader["score"] - ranked[1]["score"] < TIE_MARGIN:
        return {**out, "outcome": "escalate",
                "reason": f"materially tied ({leader['score']} vs {ranked[1]['score']}, margin {TIE_MARGIN}): a person decides"}
    return {**out, "outcome": "selected", "selected": leader["proposal"],
            "reason": f"{leader['title']} scored {leader['score']}" + (f" vs {ranked[1]['score']}" if len(ranked) > 1 else "")}


def review(contract: List[Dict[str, Any]], routes: List[Dict[str, Any]], calls: List[Dict[str, Any]],
           backend_files: Dict[str, str], security_new: List[str], artifact_ids: Dict[str, str]) -> List[Dict[str, Any]]:
    findings = []
    cov = check_contract(contract, routes, calls)

    def add(severity, kind, detail, based_on):
        findings.append({"severity": severity, "kind": kind, "detail": detail,
                         "based_on": [artifact_ids[b] for b in based_on if b in artifact_ids]})
    for k in cov["not_implemented"]:
        add("high", "requirements_coverage", f"{k} is in the contract but the backend does not implement it", ["route_inventory", "contract"])
    for k in cov["not_in_contract_client"]:
        add("high", "unsupported_assumption", f"the client calls {k}, which is not in the contract", ["client_calls", "contract"])
    for k in cov["not_in_contract_backend"]:
        add("low", "unsupported_assumption", f"the backend adds {k}, which is not in the contract", ["route_inventory", "contract"])
    for k in cov["field_drift_backend"]:
        add("medium", "interface", f"{k}: the backend's request fields differ from the contract", ["route_inventory", "contract"])
    for k in cov["field_drift_client"]:
        add("medium", "interface", f"{k}: the client's request fields differ from the contract", ["client_calls", "contract"])
    for k in cov["not_used_by_client"]:
        add("low", "requirements_coverage", f"the client has no call for {k}", ["client_calls", "contract"])
    tested = " ".join(c for p, c in backend_files.items() if "test" in p.split("/")[-1])
    for e in contract:
        if e["path"].split("{")[0].rstrip("/") not in tested:
            add("medium", "missing_evidence", f"no backend test exercises {e['method']} {e['path']}", ["source_files"])
    for s in security_new:
        add("high", "security", f"new Security Guardian finding: {s}", ["source_files"])
    for c in calls:
        if not c["resolved"]:
            add("medium", "unverifiable", f"{c['file']}:{c['line']} builds its URL in a way that cannot be checked", ["client_calls"])
    return findings
