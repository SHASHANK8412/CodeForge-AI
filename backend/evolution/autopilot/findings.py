"""
Findings: stable identities, de-duplication, history across analyses, prioritization, filtering.

A finding's id depends on its rule, file and the text of the flagged line (plus an occurrence
number), not on its line number, so it survives unrelated edits above it.
"""

import hashlib
from typing import Any, Dict, Iterable, List, Optional, Tuple

from backend.evolution.autopilot.models import Finding, FindingStatus, now_iso

_SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
_CONFIDENCE_RANK = {"confirmed": 0, "likely": 1, "suspected": 2}


def build_findings(project_id: str, raws: Iterable[Dict[str, Any]], sources) -> List[Finding]:
    seen: Dict[str, int] = {}
    out: List[Finding] = []
    raws = _merge_same_location(raws)
    for raw in raws:
        anchor = sources.line(raw.get("file"), raw.get("line_start")) or raw.get("title", "")
        base = f"{raw['rule_id']}|{raw.get('file') or ''}|{' '.join(anchor.split())}"
        n = seen.get(base, 0)
        seen[base] = n + 1
        if n and raw.get("file") is None:
            continue                          # project-level duplicates
        fid = "fnd_" + hashlib.sha1(f"{project_id}|{base}|{n}".encode()).hexdigest()[:16]
        finding = Finding(id=fid, project_id=project_id, **raw)
        priority, reasons = prioritize(finding, sources)
        finding.priority, finding.priority_reasons = priority, reasons
        out.append(finding)
    return out


def _merge_same_location(raws: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """One finding per rule and location: e.g. two secret patterns matching the same line."""
    merged: Dict[Tuple[str, str, int], Dict[str, Any]] = {}
    out: List[Dict[str, Any]] = []
    for raw in raws:
        if raw.get("file") and raw.get("line_start"):
            key = (raw["rule_id"], raw["file"], raw["line_start"])
            if key in merged:
                if raw.get("evidence") and raw["evidence"] not in merged[key]["evidence"]:
                    merged[key]["evidence"] += "\n" + raw["evidence"]
                continue
            raw = dict(raw)
            merged[key] = raw
        out.append(raw)
    return out


def prioritize(f: Finding, sources=None) -> Tuple[str, List[str]]:
    """
    P1: critical, or high and confirmed            - fix first
    P2: high, or confirmed medium security/tests/syntax
    P3: other medium, or confirmed low
    P4: everything else (suspected low/info)
    Findings in entry points or route handlers are raised one level (not above P1).
    """
    sev, conf, cat = f.severity.value, f.confidence.value, f.category.value
    reasons = [f"severity {sev}", f"confidence {conf}", f"category {cat}"]
    if sev == "critical" or (sev == "high" and conf == "confirmed"):
        level = 1
    elif sev == "high" or (sev == "medium" and conf == "confirmed" and cat in ("security", "tests", "syntax")):
        level = 2
    elif sev == "medium" or (sev == "low" and conf == "confirmed"):
        level = 3
    else:
        level = 4
    if sources is not None and f.file and 1 < level < 4 and sev in ("critical", "high", "medium"):
        hot = f.file in getattr(sources, "entry_points", set()) or f.file in getattr(sources, "route_files", set())
        if hot:
            level -= 1
            reasons.append("in an entry point or route handler")
    if f.fix_strategy in ("ruff_fix", "add_requirements", "import_repair"):
        reasons.append("deterministic fix available")
    elif f.fix_strategy == "manual":
        reasons.append("needs a person to fix")
    return f"P{level}", reasons


def merge_history(previous: Dict[str, Finding], current: List[Finding]) -> Dict[str, Finding]:
    """
    Combine a new analysis with the stored findings:
      * still detected: keeps first_seen; dismissed/planned stay so; fixed/resolved reopen
      * no longer detected: open/planned/fix_failed become resolved
    """
    now = now_iso()
    merged: Dict[str, Finding] = {}
    for f in current:
        old = previous.get(f.id)
        if old is not None:
            f.first_seen = old.first_seen
            if old.status in (FindingStatus.DISMISSED, FindingStatus.PLANNED):
                f.status = old.status
            elif old.status in (FindingStatus.FIXED_VERIFIED, FindingStatus.RESOLVED):
                f.status = FindingStatus.OPEN
                f.priority_reasons = f.priority_reasons + ["detected again after it was resolved"]
        f.last_seen = now
        merged[f.id] = f
    for fid, old in previous.items():
        if fid in merged:
            continue
        old = old.model_copy()                    # the caller's previous records stay as they were
        if old.status in (FindingStatus.OPEN, FindingStatus.PLANNED, FindingStatus.FIX_FAILED):
            old.status = FindingStatus.RESOLVED
        merged[fid] = old
    return merged


def sort_key(f: Finding):
    return (f.priority, _SEVERITY_RANK.get(f.severity.value, 9), _CONFIDENCE_RANK.get(f.confidence.value, 9),
            f.file or "", f.line_start or 0)


def filter_findings(findings: Iterable[Finding], *, severity: Optional[str] = None, category: Optional[str] = None,
                    status: Optional[str] = None, confidence: Optional[str] = None, priority: Optional[str] = None,
                    file: Optional[str] = None, q: Optional[str] = None, offset: int = 0, limit: int = 50
                    ) -> Dict[str, Any]:
    def ok(f: Finding) -> bool:
        if severity and f.severity.value not in severity.split(","):
            return False
        if category and f.category.value not in category.split(","):
            return False
        if status and f.status.value not in status.split(","):
            return False
        if confidence and f.confidence.value not in confidence.split(","):
            return False
        if priority and f.priority not in priority.split(","):
            return False
        if file and (f.file or "") != file and not (f.file or "").startswith(file.rstrip("/") + "/"):
            return False
        if q and q.lower() not in f"{f.title} {f.description} {f.file or ''} {f.rule_id}".lower():
            return False
        return True

    items = sorted((f for f in findings if ok(f)), key=sort_key)
    limit = max(1, min(int(limit), 200))
    offset = max(0, int(offset))
    return {"total": len(items), "offset": offset, "limit": limit, "items": items[offset:offset + limit]}


def summarize(findings: Iterable[Finding]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {"by_severity": {}, "by_category": {}, "by_priority": {}, "by_status": {}, "open": 0}
    for f in findings:
        for key, value in (("by_severity", f.severity.value), ("by_category", f.category.value),
                           ("by_priority", f.priority), ("by_status", f.status.value)):
            summary[key][value] = summary[key].get(value, 0) + 1
        if f.status in (FindingStatus.OPEN, FindingStatus.PLANNED, FindingStatus.FIX_FAILED):
            summary["open"] += 1
    return summary
