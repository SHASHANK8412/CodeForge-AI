"""
Normalization, de-duplication, architecture context and prioritization.

  de-duplication  results from different tools about the same thing (same file, line within 2,
                  same category or an explicit duplicate mapping such as Bandit B608 -> PY-SQLI)
                  become one finding listing every detecting source - three scanners are one finding
  context         the Digital Twin graph gives the route a line belongs to, whether that route sits
                  behind authentication, and how many files depend on the file
  priority        qualitative and explained (no CVSS is invented): P1..P4 from severity, confidence,
                  exposure, verification evidence and mitigations
"""

import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.evolution.autopilot.models import now_iso
from backend.evolution.autopilot.redact import redact
from backend.guardian.models import Evidence, Finding

_SEV = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
_CONF = {"high": 0, "medium": 1, "low": 2}


def finding_id(project_id: str, rule_id: str, file: Optional[str], anchor: str) -> str:
    return "sg_" + hashlib.sha1(f"{project_id}|{rule_id}|{file}|{' '.join(anchor.split())[:160]}".encode()).hexdigest()[:14]


def build(project_id: str, raws: List[Dict[str, Any]], lines_of: Dict[str, List[str]], context: "Context") -> List[Finding]:
    primary = [r for r in raws if not r.get("dup_of")] + [r for r in raws if r.get("dup_of")]
    findings: List[Finding] = []
    for raw in primary:
        match = _duplicate_of(raw, findings)
        source = raw.get("source", "guardian")
        ev = Evidence(source=raw["rule_id"], detail=redact(raw.get("evidence_text", "")[:400]), file=raw.get("file"),
                      line=raw.get("line"))
        if match is not None:
            if source not in match.detection:
                match.detection.append(source)
            match.evidence.append(ev)
            if _SEV[raw["severity"]] < _SEV[match.severity]:
                match.severity = raw["severity"]
            if _CONF[raw["confidence"]] < _CONF[match.confidence]:
                match.confidence = raw["confidence"]
            match.references = sorted(set(match.references) | set(raw.get("references", [])))
            continue
        anchor = _line(lines_of, raw.get("file"), raw.get("line")) or raw.get("evidence_text", "") or raw["title"]
        f = Finding(
            id=finding_id(project_id, raw["rule_id"], raw.get("file"), anchor), project_id=project_id,
            rule_id=raw["rule_id"], category=raw["category"], title=raw["title"], description=raw.get("description", ""),
            severity=raw["severity"], confidence=raw["confidence"], file=raw.get("file"), line=raw.get("line"),
            route=raw.get("route"), evidence=[ev], detection=[source], state=raw.get("state", "detected"),
            impact=_impact(raw["category"]), remediation=raw.get("remediation", ""),
            dependencies=raw.get("dependencies", []), references=raw.get("references", []),
            verifiable=raw.get("verifiable"),
            context={k: v for k, v in raw.items() if k in ("sensitive_keys", "verification_note", "params")})
        findings.append(f)
    for f in findings:
        context.annotate(f)
        f.priority, f.priority_reasons = prioritize(f)
    return findings


def _duplicate_of(raw, findings: List[Finding]) -> Optional[Finding]:
    for f in findings:
        if f.file != raw.get("file"):
            continue
        same_rule = raw.get("dup_of") == f.rule_id or raw["rule_id"] == f.rule_id
        near = f.line is not None and raw.get("line") is not None and abs(f.line - raw["line"]) <= 2
        if (same_rule and (near or f.line == raw.get("line"))) or (near and raw.get("dup_of") and f.category == raw["category"]):
            return f
        if raw["rule_id"] == f.rule_id and raw.get("line") is None and f.line is None:
            return f
        # a hardcoded credential/key on one line is one issue, whichever scanner names it
        if f.line is not None and f.line == raw.get("line") and {f.category, raw["category"]} <= {"secrets", "crypto"} \
                and (f.rule_id.startswith(("SECRET-", "PY-HARDCODED")) or raw["rule_id"].startswith(("SECRET-", "PY-HARDCODED", "BANDIT-B10"))):
            return f
    return None


def _line(lines_of, file, line) -> str:
    if not file or not line or file not in lines_of:
        return ""
    ls = lines_of[file]
    return ls[line - 1].strip() if 0 < line <= len(ls) else ""


def _impact(category: str) -> str:
    return {
        "injection": "an attacker can change queries or commands, read or modify data, or run code",
        "auth": "actions or data are available to callers who should not have them",
        "secrets": "credentials or sensitive data can be read by anyone with the code, an archive or the API",
        "web": "browsers can be abused against users (cross-site requests, scripts, redirects)",
        "dependencies": "a published vulnerability in a library may be exploitable through the app",
        "configuration": "the deployment gives an attacker more than it needs to",
        "crypto": "protected values (passwords, tokens) can be guessed, forged or cracked",
    }.get(category, "")


def prioritize(f: Finding) -> Tuple[str, List[str]]:
    score = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}[f.severity]
    reasons = [f"severity {f.severity}", f"confidence {f.confidence}"]
    if f.state == "verified":
        score += 2
        reasons.append("verified by a safe test")
    elif f.state in ("not_reproduced",):
        score -= 1
        reasons.append("the safe test did not reproduce it")
    if f.confidence == "low":
        score -= 1
    exposure = f.context.get("exposure")
    if exposure == "public":
        score += 1
        reasons.append(f"reachable without authentication ({f.route})")
    elif exposure == "authenticated":
        score -= 1
        reasons.append("only reachable after authentication (mitigation)")
    if len(f.detection) > 1:
        reasons.append(f"reported by {len(f.detection)} independent sources: {', '.join(f.detection)}")
    if f.state == "requires_review":
        reasons.append("needs a person to judge the context")
    level = "P1" if score >= 5 else "P2" if score >= 4 else "P3" if score >= 2 else "P4"
    return level, reasons


class Context:
    """Digital Twin facts for findings: owning route, its authentication boundary, dependents."""

    def __init__(self, project: Path):
        from backend.twin.graph import build_graph
        from backend.twin.index import GraphIndex
        from backend.twin.models import GraphAnalysis
        self.builder = build_graph(project, deadline_seconds=30)
        self.index = GraphIndex(GraphAnalysis(id="tmp", project_id="tmp", user_id="tmp", nodes=list(self.builder.nodes.values()),
                                              edges=list(self.builder.edges.values())))
        # handler line ranges per file: [(start, end, "METHOD /path")]
        self.handlers: Dict[str, List[Tuple[int, int, str]]] = {}
        for n in self.builder.nodes.values():
            if n.type == "route" and n.meta.get("handler"):
                fn = self.builder.nodes.get(f"function:{n.path}#{n.meta['handler']}")
                if fn is not None:
                    self.handlers.setdefault(n.path, []).append(
                        (fn.meta.get("line", 0), fn.meta.get("end_line", 0), f"{n.meta.get('method')} {n.meta.get('route')}"))
        self.protected_routes: set = set()
        self.all_protected = False

    def annotate(self, f: Finding) -> None:
        if f.file and f.line and not f.route:
            for start, end, key in self.handlers.get(f.file, []):
                if start <= f.line <= (end or start):
                    f.route = key
        if f.file:
            deps = self.index.dependents(f.file)
            f.context["dependents"] = [p for p, _ in deps][:20]
            f.component = f.route or f.file
        if f.route:
            # set by the service: routes behind an auth dependency, or every route when auth middleware is installed
            f.context["exposure"] = "authenticated" if (self.all_protected or f.route in self.protected_routes) else "public"


def protected_routes(sources: Dict[str, str]) -> set:
    """Routes whose handler takes an auth dependency (the same rule as PY-MISSING-AUTH, positively)."""
    import ast
    from backend.guardian.rules_py import AUTH_WORDS, _routes, _full, _name
    out = set()
    for rel, src in sources.items():
        if not rel.endswith(".py"):
            continue
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        routes, owners = _routes(tree)
        for r in routes:
            fn = r.fn
            deps = fn.args.defaults + [x for x in fn.args.kw_defaults if x is not None]
            if any(isinstance(d, ast.Call) and _name(d.func) in ("Depends", "Security") and d.args and AUTH_WORDS.search(_full(d.args[0]))
                   for d in deps) or owners.get(r.owner, {}).get("auth") or getattr(r, "decorator_auth", False):
                out.add(r.key)
    return out


def merge_history(previous: Dict[str, Finding], current: List[Finding]) -> Dict[str, Finding]:
    """Keep first_seen, accepted risks and verification results whose evidence is unchanged."""
    now = now_iso()
    merged: Dict[str, Finding] = {}
    for f in current:
        old = previous.get(f.id)
        if old is not None:
            f.first_seen = old.first_seen
            if old.state == "accepted_risk":
                f.state, f.accepted_by, f.accepted_note = old.state, old.accepted_by, old.accepted_note
            elif old.state in ("verified", "not_reproduced", "verification_unavailable") and old.verification:
                f.state, f.verification, f.last_verified = old.state, old.verification, old.last_verified
            elif old.state in ("fixed", "fix_verified"):
                f.state = "detected"                     # detected again after a fix: it is back
                f.priority_reasons.append("detected again after it was marked fixed")
        f.last_seen = now
        merged[f.id] = f
    for fid, old in previous.items():
        if fid not in merged:
            old = old.model_copy()
            if old.state not in ("fix_verified", "accepted_risk"):
                old.context["resolved_at"] = now     # no longer detected by the latest scan
            merged[fid] = old
    return merged


def summarize(findings: List[Finding]) -> Dict[str, Any]:
    by = lambda attr: {k: sum(1 for f in findings if getattr(f, attr) == k) for k in sorted({getattr(f, attr) for f in findings})}  # noqa: E731
    open_ = [f for f in findings if f.state not in ("fix_verified", "accepted_risk") and "resolved_at" not in f.context]
    return {"total": len(findings), "open": len(open_), "by_severity": by("severity"), "by_state": by("state"),
            "by_category": by("category"), "by_priority": by("priority"),
            "critical_high_open": sum(1 for f in open_ if f.severity in ("critical", "high")),
            "verified_open": sum(1 for f in open_ if f.state == "verified"),
            "awaiting_verification": sum(1 for f in open_ if f.state == "fixed"),
            "accepted_risks": sum(1 for f in findings if f.state == "accepted_risk")}
