"""
Scoring, findings and root-cause analysis for a chaos assessment.

  score       each category's score = passed / evaluated criteria of that category (x100); the overall
              score is the mean of the evaluated categories. Unevaluated criteria and scenarios are
              counted and shown, never scored as passes. Separate from performance and security scores.
  findings    every failed criterion of a scenario is a *reproduced* finding; patterns in the code
              (outbound call without a timeout, unhandled dependency errors, error text returned to
              clients, no health endpoint) are *static suspicions*
  root cause  "probable" when a static suspicion sits on the call path of an endpoint that showed the
              failure and matches its kind; "confirmed" only after a repair aimed at it made the failure
              disappear in the same experiment; otherwise an "unconfirmed hypothesis"
"""

import ast
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.chaos.models import Assessment, ChaosFinding, ScenarioResult
from backend.evolution.autopilot.codebase import iter_project_files, read_text

CATEGORIES = ["containment", "timeout", "recovery", "error_handling", "degradation", "data_integrity", "post_recovery"]
_SEVERITY = {"containment": "critical", "recovery": "high", "post_recovery": "high", "timeout": "high",
             "error_handling": "medium", "degradation": "medium", "data_integrity": "high"}
_MATCH = {"timeout": {"no-timeout"}, "error_handling": {"unhandled-dependency-error", "error-text-returned"},
          "degradation": {"unhandled-dependency-error"}, "containment": {"unhandled-dependency-error"}}


def score(results: List[ScenarioResult]) -> Dict[str, Any]:
    per_cat: Dict[str, Dict[str, int]] = {c: {"passed": 0, "failed": 0, "not_evaluated": 0} for c in CATEGORIES}
    for r in results:
        for c in r.criteria:
            per_cat.setdefault(c.category, {"passed": 0, "failed": 0, "not_evaluated": 0})[c.status] += 1
    categories = {}
    for cat, n in per_cat.items():
        evaluated = n["passed"] + n["failed"]
        categories[cat] = {**n, "score": round(n["passed"] / evaluated * 100, 1) if evaluated else None}
    evaluated_scores = [v["score"] for v in categories.values() if v["score"] is not None]
    recoveries = [r.recovery_seconds for r in results if r.recovery_seconds is not None]
    return {
        "overall": round(sum(evaluated_scores) / len(evaluated_scores), 1) if evaluated_scores else None,
        "categories": categories,
        "scenarios_passed": sum(1 for r in results if r.status == "passed"),
        "scenarios_failed": sum(1 for r in results if r.status == "failed"),
        "scenarios_not_evaluated": sum(1 for r in results if r.status in ("not_evaluated", "inconclusive", "aborted", "pending")),
        "max_recovery_seconds": max(recoveries) if recoveries else None,
        "method": "category score = passed / evaluated criteria; overall = mean of evaluated categories; "
                  "criteria that could not be evaluated are excluded and listed, never counted as passed",
    }


# --- static suspicions -------------------------------------------------------------------------------------

_OUTBOUND = {("urllib", "urlopen"), ("request", "urlopen"), ("requests", "get"), ("requests", "post"),
             ("requests", "put"), ("requests", "delete"), ("requests", "request"), ("httpx", "get"), ("httpx", "post")}


def _call_name(node: ast.Call) -> Tuple[str, str]:
    f = node.func
    if isinstance(f, ast.Attribute):
        v = f.value
        owner = v.attr if isinstance(v, ast.Attribute) else v.id if isinstance(v, ast.Name) else ""
        return owner, f.attr
    return "", getattr(f, "id", "")


def _inside_try(tree: ast.AST, target: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Try) and node.handlers:
            for stmt in node.body:
                if any(n is target for n in ast.walk(stmt)):
                    return True
    return False


def static_suspicions(project: Path) -> List[Dict[str, Any]]:
    """Resilience-relevant patterns per Python file, with the function they are in."""
    out: List[Dict[str, Any]] = []
    has_health = False
    for rel, path, size in iter_project_files(Path(project)):
        if not rel.endswith(".py") or "/tests/" in f"/{rel}" or Path(rel).name.startswith("test_"):
            continue
        source = read_text(path, size)
        if source is None:
            continue
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        if "/health" in source:
            has_health = True
        lines = source.splitlines()
        for fn in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
            for node in ast.walk(fn):
                if not isinstance(node, ast.Call):
                    continue
                owner, name = _call_name(node)
                if (owner, name) in _OUTBOUND or name == "urlopen":
                    text = lines[node.lineno - 1].strip()
                    if not any(k.arg == "timeout" for k in node.keywords) and not (name == "urlopen" and len(node.args) >= 3):
                        if owner != "httpx":                       # httpx has a 5 s default timeout
                            out.append(_s("no-timeout", rel, node.lineno, fn.name, text,
                                          "outbound call without a timeout: a slow dependency holds the request "
                                          "(and a worker) for as long as it takes"))
                    if not _inside_try(fn, node):
                        out.append(_s("unhandled-dependency-error", rel, node.lineno, fn.name, text,
                                      "dependency errors (refused connection, HTTP error, bad data) are not handled "
                                      "here and surface as 500s"))
            for node in ast.walk(fn):
                if isinstance(node, ast.ExceptHandler) and node.name:
                    for ret in [n for n in ast.walk(node) if isinstance(n, (ast.Return, ast.Raise))]:
                        if any(isinstance(n, ast.Name) and n.id == node.name for n in ast.walk(ret)) and \
                                any(isinstance(n, ast.Call) and getattr(n.func, "id", "") == "str" for n in ast.walk(ret)):
                            out.append(_s("error-text-returned", rel, ret.lineno, fn.name, lines[ret.lineno - 1].strip(),
                                          "exception text is returned to the client and can expose internals"))
    if not has_health:
        out.append(_s("no-health-endpoint", None, None, None, "", "no /health endpoint: orchestrators cannot tell "
                      "whether the app is alive"))
    return out


def _s(rule, file, line, function, evidence, why) -> Dict[str, Any]:
    return {"rule": rule, "file": file, "line": line, "function": function, "evidence": evidence, "why": why}


def call_path_functions(project: Path, handler_file: str, handler: str) -> List[str]:
    """The handler and the functions it calls in the same file (transitively), by name."""
    try:
        tree = ast.parse((Path(project) / handler_file).read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return [handler]
    defs = {n.name: n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    seen, todo = set(), [handler]
    while todo:
        name = todo.pop()
        if name in seen or name not in defs:
            continue
        seen.add(name)
        todo += [getattr(c.func, "id", "") for c in ast.walk(defs[name]) if isinstance(c, ast.Call)]
    return sorted(seen)


def handlers(project: Path) -> Dict[str, Tuple[str, Optional[str]]]:
    """'METHOD /path' -> (file, handler function) from the Digital Twin graph."""
    from backend.twin.graph import build_graph
    b = build_graph(project, deadline_seconds=20)
    return {f"{n.meta.get('method')} {n.meta.get('route')}": (n.path, n.meta.get("handler"))
            for n in b.nodes.values() if n.type == "route"}


def build_findings(project_id: str, project: Path, assessment: Assessment) -> List[ChaosFinding]:
    from backend.twin.graph import routes_match
    suspicions = static_suspicions(project)
    routes = handlers(project)
    findings: Dict[str, ChaosFinding] = {}

    def owner_of(endpoint: str):
        method, path = endpoint.split(" ", 1)
        for key, (file, fn) in routes.items():
            k_method, k_path = key.split(" ", 1)
            if k_method == method and (k_path == path or routes_match(k_path, path)):
                return file, fn
        return None, None

    for r in assessment.results:
        for c in r.criteria:
            if c.status != "failed":
                continue
            eps = [ep for ep in r.affected_endpoints if not ep.endswith(" /health")] or ["(application)"]
            component = ", ".join(eps)
            file, fn = owner_of(eps[0]) if eps[0] != "(application)" else (None, None)
            path_fns = call_path_functions(project, file, fn) if file and fn else []
            causes = [s for s in suspicions if s["file"] == file and s["function"] in path_fns
                      and s["rule"] in _MATCH.get(c.category, set())]
            fid = "cf_" + hashlib.sha1(f"{project_id}|{r.scenario}|{c.id}|{component}".encode()).hexdigest()[:12]
            findings[fid] = ChaosFinding(
                id=fid, project_id=project_id, category=c.category, component=component,
                severity=_SEVERITY.get(c.category, "medium"), kind="reproduced",
                title=f"{c.description.split(';')[0]} - failed under '{r.scenario}'",
                evidence=c.evidence, reproduction=f"scenario '{r.scenario}' in an isolated sandbox: " + " -> ".join(
                    p.split(" ", 1)[1] for p in r.procedure),
                expected=c.description, observed=c.evidence, confidence="high",
                root_cause="; ".join(f"{s['why']} ({s['file']}:{s['line']} in {s['function']}: {s['evidence']})" for s in causes)
                or "no matching pattern found on the endpoint's code path",
                root_cause_level="probable" if causes else "unconfirmed_hypothesis",
                file=causes[0]["file"] if causes else file, line=causes[0]["line"] if causes else None,
                remediation=_remedy(c.category), scenario=r.scenario, criterion=c.id)
    linked = {(f.file, f.line) for f in findings.values()}
    for s in suspicions:
        if (s["file"], s["line"]) in linked:
            continue
        fid = "cf_" + hashlib.sha1(f"{project_id}|static|{s['rule']}|{s['file']}|{s['line']}".encode()).hexdigest()[:12]
        findings[fid] = ChaosFinding(
            id=fid, project_id=project_id, category={"no-timeout": "timeout", "no-health-endpoint": "recovery"}.get(
                s["rule"], "error_handling"), component=f"{s['file']}:{s['function']}" if s["file"] else "application",
            severity="low", kind="static_suspicion", title=s["why"].split(":")[0], evidence=s["evidence"] or s["why"],
            expected="", observed="not reproduced by an experiment", confidence="low", root_cause=s["why"],
            root_cause_level="unconfirmed_hypothesis", file=s["file"], line=s["line"], remediation=_remedy_rule(s["rule"]))
    return list(findings.values())


def _remedy(category: str) -> str:
    return {
        "timeout": "Give the outbound call an explicit timeout below the request budget and handle the timeout.",
        "error_handling": "Catch dependency errors (connection, HTTP status, invalid data) and answer with a degraded "
                          "result or a deliberate 503 that does not include exception details.",
        "degradation": "Serve the part of the response that does not need the dependency (e.g. the field set to null) "
                       "instead of failing the whole request.",
        "containment": "Keep the dependency failure inside the endpoint that needs it; never let it stop the process.",
        "recovery": "Make sure the app reconnects / retries after the dependency returns (no cached broken client).",
        "post_recovery": "Do not keep error state after the dependency recovers.",
        "data_integrity": "Persist data outside the container or make writes idempotent.",
    }.get(category, "")


def _remedy_rule(rule: str) -> str:
    return {"no-timeout": _remedy("timeout"), "unhandled-dependency-error": _remedy("error_handling"),
            "error-text-returned": "Log the exception and return a generic message to the client.",
            "no-health-endpoint": "Add a lightweight GET /health endpoint."}.get(rule, "")


def impact(project: Path, assessment: Assessment) -> Dict[str, Any]:
    """Digital Twin view: where each dependency is used and what it may affect, next to what was observed."""
    from backend.twin.graph import build_graph
    from backend.twin.index import GraphIndex
    from backend.twin.models import GraphAnalysis
    b = build_graph(project, deadline_seconds=20)
    index = GraphIndex(GraphAnalysis(id="tmp", project_id="tmp", user_id="tmp", nodes=list(b.nodes.values()),
                                     edges=list(b.edges.values())))
    out = []
    observed_affected = sorted({ep for r in assessment.results for ep in r.affected_endpoints})
    recovered = sorted({ep for r in assessment.results if r.recovery_seconds is not None for ep in r.affected_endpoints})
    unhealthy = sorted(set(observed_affected) - set(recovered))
    for dep in assessment.config.dependencies:
        origin = sorted(rel for rel, src in b.sources.items() if dep.env_var in src and not Path(rel).name.startswith("test_"))
        closure = index.reverse_closure(origin) if origin else {}
        potential_routes = sorted({n.symbol for f in origin + list(closure) for n in index.defined_in(f, ("route",))})
        out.append({
            "dependency": dep.name, "env_var": dep.env_var, "origin_files": origin,
            "direct_dependents": sorted(p for p, v in closure.items() if v["depth"] == 1),
            "potentially_affected_routes": potential_routes,
            "observed_affected": observed_affected, "recovered": recovered, "remained_unhealthy": unhealthy,
            "not_observed": sorted(set(potential_routes) - {ep for ep in observed_affected}),
            "note": "Potential impact comes from the dependency graph; only 'observed_affected' was seen in experiments.",
        })
    return {"dependencies": out}
