"""
Static performance analysis: patterns in the source that often cost time. Nothing is executed.

A finding is a "static_warning" when the pattern is a performance problem by itself (time.sleep in
async code blocks the event loop; a fetch in a useEffect without dependencies runs on every
render) and a "hypothesis" when it only might matter (a query inside a loop is cheap for 3 rows and
slow for 3,000). Only a workload run turns either into a measured bottleneck.
"""

import ast
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.evolution.autopilot.codebase import iter_project_files, read_text
from backend.evolution.autopilot.redact import redact

_QUERY_CALLS = {"query", "execute", "scalars", "scalar", "get", "find", "find_one", "filter", "filter_by",
                "first", "all", "one", "count"}
_DB_OWNERS = {"db", "session", "Session", "conn", "connection", "cursor", "collection", "objects"}
_HTTP_OWNERS = {"requests", "httpx", "client", "session_http"}
_HTTP_METHODS = {"get", "post", "put", "patch", "delete", "request"}
_PAGE_PARAMS = {"limit", "skip", "offset", "page", "size", "per_page", "page_size", "cursor"}
_HEAVY_JS = {"moment": "a large date library (consider date-fns or Intl)",
             "lodash": "the full lodash bundle when imported as a whole"}


def _finding(rule, category, title, severity, evidence_kind, confidence, file, line, evidence, impact,
             recommendation, validation, endpoint=None) -> Dict[str, Any]:
    return {"rule_id": rule, "category": category, "title": title, "severity": severity,
            "evidence_kind": evidence_kind, "detection": "static analysis (Python ast)" if file.endswith(".py")
            else "static analysis (source patterns)", "confidence": confidence, "file": file, "line": line,
            "evidence": redact(evidence[:400]), "impact": impact, "recommendation": recommendation,
            "validation": validation, "endpoint": endpoint}


def _owner(call: ast.Call) -> str:
    """The name a call chain starts from: `db.query(X).filter(...).all()` -> 'db'."""
    v = call.func.value if isinstance(call.func, ast.Attribute) else None
    while v is not None and not isinstance(v, ast.Name):
        v = v.func if isinstance(v, ast.Call) else v.value if isinstance(v, ast.Attribute) else None
    return v.id if isinstance(v, ast.Name) else ""


def _is_db_call(node: ast.AST) -> bool:
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr in _QUERY_CALLS and _owner(node) in _DB_OWNERS)


def _is_http_call(node: ast.AST) -> bool:
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr in _HTTP_METHODS and _owner(node) in _HTTP_OWNERS)


def _routes(tree: ast.Module) -> Dict[str, str]:
    """handler function name -> 'METHOD /path' for decorated route handlers in this module."""
    prefixes = {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call) and getattr(n.value.func, "id", getattr(n.value.func, "attr", "")) == "APIRouter":
            prefix = next((k.value.value for k in n.value.keywords if k.arg == "prefix" and isinstance(k.value, ast.Constant)), "")
            for t in n.targets:
                if isinstance(t, ast.Name):
                    prefixes[t.id] = prefix
    out = {}
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for d in n.decorator_list:
                if (isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr in ("get", "post", "put", "patch", "delete")
                        and d.args and isinstance(d.args[0], ast.Constant) and isinstance(d.args[0].value, str)):
                    owner = d.func.value.id if isinstance(d.func.value, ast.Name) else ""
                    out[n.name] = f"{d.func.attr.upper()} {prefixes.get(owner, '')}{d.args[0].value}"
    return out


def python_findings(rel: str, source: str) -> List[Dict[str, Any]]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    lines = source.splitlines()
    text = lambda n: lines[n.lineno - 1].strip() if 0 < n.lineno <= len(lines) else ""  # noqa: E731
    routes = _routes(tree)
    found: List[Dict[str, Any]] = []
    for fn in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        endpoint = routes.get(fn.name)
        where = f"{fn.name}()" + (f" - {endpoint}" if endpoint else "")
        # N+1: a query inside a loop (stronger when the loop iterates over a query result)
        for loop in [n for n in ast.walk(fn) if isinstance(n, (ast.For, ast.AsyncFor, ast.While))]:
            inner = [n for stmt in loop.body for n in ast.walk(stmt) if _is_db_call(n)]
            if inner:
                over_query = isinstance(loop, (ast.For, ast.AsyncFor)) and any(_is_db_call(n) for n in ast.walk(loop.iter))
                found.append(_finding(
                    "PERF-N-PLUS-ONE", "n_plus_one", f"Database query inside a loop in {where}",
                    "high" if over_query else "medium", "hypothesis", "medium" if over_query else "low", rel,
                    inner[0].lineno, text(inner[0]),
                    "one query per item: time grows linearly with the number of rows (N+1 pattern)",
                    "Load the related rows in one query (a join, IN (...) or eager loading such as selectinload).",
                    f"measure {endpoint or 'the endpoint that calls it'} with realistic data before and after", endpoint))
            http = [n for stmt in loop.body for n in ast.walk(stmt) if _is_http_call(n)]
            if http:
                found.append(_finding(
                    "PERF-API-IN-LOOP", "repeated_api_call", f"HTTP call inside a loop in {where}", "medium",
                    "hypothesis", "medium", rel, http[0].lineno, text(http[0]),
                    "one network round trip per item", "Batch the requests or fetch the data once outside the loop.",
                    "measure the endpoint before and after", endpoint))
            # JSON (de)serialization per item
            ser = [n for stmt in loop.body for n in ast.walk(stmt) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                   and n.func.attr in ("dumps", "loads") and _owner(n) == "json"]
            if ser:
                found.append(_finding(
                    "PERF-SERIALIZE-IN-LOOP", "serialization", f"json.{ser[0].func.attr} inside a loop in {where}", "low",
                    "hypothesis", "low", rel, ser[0].lineno, text(ser[0]),
                    "repeated serialization; usually small unless the loop is large",
                    "Serialize the whole collection once, or return the objects and let the framework serialize them.",
                    "measure the endpoint before and after", endpoint))
            # nested loop over the same collection: O(n^2)
            if isinstance(loop, ast.For) and isinstance(loop.iter, ast.Name):
                for inner_loop in [n for stmt in loop.body for n in ast.walk(stmt) if isinstance(n, ast.For)]:
                    if isinstance(inner_loop.iter, ast.Name) and inner_loop.iter.id == loop.iter.id:
                        found.append(_finding(
                            "PERF-QUADRATIC-LOOP", "expensive_loop", f"Nested loop over `{loop.iter.id}` in {where}", "low",
                            "hypothesis", "low", rel, inner_loop.lineno, text(inner_loop),
                            "quadratic time in the size of the collection",
                            "Index the collection once (a dict or set) instead of scanning it for every item.",
                            "measure with a realistic collection size", endpoint))
                        break
        # blocking calls in async code
        if isinstance(fn, ast.AsyncFunctionDef):
            sync_db_reported = False
            for n in ast.walk(fn):
                if not isinstance(n, ast.Call) or not isinstance(n.func, ast.Attribute):
                    continue
                blocking = None
                if n.func.attr == "sleep" and _owner(n) == "time":
                    blocking = "time.sleep blocks the event loop: every other request waits"
                elif _owner(n) == "requests":
                    blocking = "requests is synchronous: the event loop is blocked for the whole HTTP call"
                elif _is_db_call(n) and not sync_db_reported:
                    sync_db_reported = True        # once per handler, not once per call in a query chain
                    blocking = "a synchronous database call inside async def blocks the event loop"
                if blocking:
                    definite = n.func.attr == "sleep" or _owner(n) == "requests"
                    found.append(_finding(
                        "PERF-BLOCKING-ASYNC", "blocking_async", f"Blocking call in async {where}",
                        "high" if definite else "medium", "static_warning" if definite else "hypothesis",
                        "high" if definite else "medium", rel, n.lineno, text(n), blocking,
                        "Use the async equivalent (asyncio.sleep, httpx.AsyncClient, an async DB driver) or make "
                        "the handler a plain `def` so FastAPI runs it in a thread pool.",
                        f"measure {endpoint or 'the endpoint'} with concurrency > 1 before and after", endpoint))
        # the same query expression evaluated more than once in one function
        seen: Dict[str, ast.Call] = {}
        for n in ast.walk(fn):
            if _is_db_call(n):
                key = hashlib.sha1(ast.dump(n).encode()).hexdigest()
                if key in seen:
                    found.append(_finding(
                        "PERF-REPEATED-QUERY", "repeated_query", f"The same query runs twice in {where}", "low",
                        "hypothesis", "medium", rel, n.lineno, text(n), "an extra database round trip",
                        "Run the query once and reuse the result.", "measure the endpoint before and after", endpoint))
                    break
                seen[key] = n
        # list endpoints without pagination
        if endpoint and endpoint.startswith("GET"):
            params = {a.arg for a in fn.args.args + fn.args.kwonlyargs}
            returns_all = [n for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                           and n.func.attr == "all" and _is_db_call(n)]
            limited = any(isinstance(n, ast.Attribute) and n.attr in ("limit", "offset", "slice") for n in ast.walk(fn))
            if returns_all and not (params & _PAGE_PARAMS) and not limited:
                found.append(_finding(
                    "PERF-NO-PAGINATION", "pagination", f"{endpoint} returns every row", "medium", "hypothesis", "medium",
                    rel, returns_all[0].lineno, text(returns_all[0]),
                    "response time and memory grow with the table; harmless while the table is small",
                    "Add limit/offset (or cursor) parameters with a sensible default and maximum.",
                    f"measure {endpoint} with a large table before and after", endpoint))
        # outbound HTTP from a request handler without any caching
        if endpoint and any(_is_http_call(n) for n in ast.walk(fn)):
            decorators = {getattr(d, "id", getattr(d, "attr", "")) for d in fn.decorator_list}
            if not decorators & {"lru_cache", "cache", "cached"}:
                call = next(n for n in ast.walk(fn) if _is_http_call(n))
                found.append(_finding(
                    "PERF-NO-CACHE", "caching", f"{endpoint} calls another service on every request", "low",
                    "hypothesis", "low", rel, call.lineno, text(call),
                    "the upstream latency is added to every request",
                    "Cache the upstream answer for a short time if it does not need to be fresh per request.",
                    f"measure {endpoint} before and after; check that stale data is acceptable", endpoint))
    # work done at import time (application startup)
    for n in tree.body:
        heavy = None
        if isinstance(n, (ast.For, ast.While)):
            heavy = "a loop runs at import time"
        elif any(_is_http_call(c) or (isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                                      and c.func.attr == "sleep" and _owner(c) == "time") for c in ast.walk(n)):
            heavy = "a network call or sleep runs at import time"
        if heavy:
            found.append(_finding(
                "PERF-STARTUP-WORK", "startup", f"Work at import time in {rel}", "low", "hypothesis", "low", rel,
                n.lineno, text(n), f"{heavy}, delaying startup and every worker process",
                "Move it into a startup/lifespan hook or do it lazily on first use.",
                "compare the measured startup time before and after"))
    return found


def _useeffect_calls(source: str):
    """(start index, has dependency array, body text) for each useEffect(...) call."""
    for m in re.finditer(r"\buseEffect\s*\(", source):
        depth, i = 1, m.end()
        top_level_commas = 0
        while i < len(source) and depth:
            ch = source[i]
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
            elif ch == "," and depth == 1:
                top_level_commas += 1
            i += 1
        body = source[m.end(): i - 1]
        has_deps = top_level_commas >= 1 and re.search(r",\s*\[[^\]]*\]\s*$", body.strip()) is not None
        yield m.start(), has_deps, body


def js_findings(rel: str, source: str) -> List[Dict[str, Any]]:
    found = []
    for start, has_deps, body in _useeffect_calls(source):
        if not has_deps and re.search(r"\b(fetch|axios|api)\s*[.(]", body):
            line = source.count("\n", 0, start) + 1
            found.append(_finding(
                "PERF-EFFECT-NO-DEPS", "rerender", "useEffect without a dependency array fetches on every render",
                "high", "static_warning", "high", rel, line, source.splitlines()[line - 1],
                "the request is sent after every render, and a state update from its response renders again (a request loop)",
                "Pass a dependency array (e.g. [] to fetch once, or the values the request depends on).",
                "count the requests the page sends before and after (browser network panel)"))
    return found


def project_findings(project: Path) -> Tuple[List[Dict[str, Any]], List[str]]:
    """All static findings of a project, plus notes on what was not analyzed."""
    project = Path(project).resolve()
    found, notes = [], []
    urls: Dict[str, List[str]] = {}
    stopped: list = []
    for rel, path, size in iter_project_files(project, stopped):
        source = read_text(path, size)
        if source is None:
            continue
        if rel.endswith(".py") and not re.search(r"(^|/)(tests?/|test_)", rel):
            found += python_findings(rel, source)
        elif rel.endswith((".js", ".jsx", ".ts", ".tsx")):
            found += js_findings(rel, source)
            for m in re.finditer(r"\bfetch\(\s*[`'\"]([^`'\"]+)", source):
                urls.setdefault(re.sub(r"\$\{[^}]*\}", "*", m.group(1)), []).append(rel)
        elif path.name == "package.json":
            try:
                deps = set((json.loads(source).get("dependencies") or {}))
            except ValueError:
                continue
            for dep in sorted(deps & set(_HEAVY_JS)):
                found.append(_finding(
                    "PERF-HEAVY-DEPENDENCY", "dependency", f"Heavy frontend dependency: {dep}", "low", "hypothesis", "low",
                    rel, None, f'"{dep}" in dependencies', f"{_HEAVY_JS[dep]} increases the bundle the browser downloads",
                    "Use a lighter alternative or import only the functions you need.",
                    "compare the production bundle size before and after"))
    for url, files in urls.items():
        files = sorted(set(files))
        if len(files) >= 2:
            found.append(_finding(
                "PERF-REPEATED-FETCH", "caching", f"{url} is fetched from {len(files)} components", "low", "hypothesis", "low",
                files[0], None, ", ".join(files), "the same data may be downloaded several times per page",
                "Fetch it once (a shared hook, context or a client-side cache) and pass it down.",
                "count the requests per page load before and after"))
    notes += stopped
    unique, seen = [], set()
    for f in found:                    # one finding per rule and location (a call chain has several call nodes)
        key = (f["rule_id"], f["file"], f["line"], f.get("evidence") if f["line"] is None else None)
        if key not in seen:
            seen.add(key)
            unique.append(f)
    return unique, notes


def finding_id(project_id: str, f: Dict[str, Any]) -> str:
    base = f"{project_id}|{f['rule_id']}|{f.get('file')}|{f.get('endpoint')}|{f.get('evidence', '')[:120]}"
    return "pf_" + hashlib.sha1(base.encode()).hexdigest()[:14]


def suggested_endpoints(project: Path, limit: int = 5) -> List[Dict[str, str]]:
    """GET routes without path parameters, from the Digital Twin graph (routes with a prefix set in
    another file may be missing it; the runner checks each one answers before measuring)."""
    from backend.twin.graph import build_graph
    b = build_graph(project, deadline_seconds=20)
    out = []
    for n in sorted(b.nodes.values(), key=lambda n: n.id):
        path = n.meta.get("route", "") if n.type == "route" else ""
        if n.meta.get("method") == "GET" and path and "{" not in path and ":" not in path and n.language == "python":
            out.append({"method": "GET", "path": path, "handler": f"{n.path}:{n.meta.get('handler')}"})
    return out[:limit]


def endpoint_owner(project: Path) -> Dict[str, Tuple[str, Optional[int]]]:
    """'METHOD /path' -> (handler file, line) from the graph."""
    from backend.twin.graph import build_graph
    b = build_graph(project, deadline_seconds=20)
    return {f"{n.meta.get('method')} {n.meta.get('route')}": (n.path, n.meta.get("line"))
            for n in b.nodes.values() if n.type == "route"}
