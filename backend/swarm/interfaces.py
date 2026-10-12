"""
What each component actually exposes or calls, read from its code (not from what an agent says about it):

  routes(sources)        FastAPI routes: method, full path (APIRouter prefix in the same file), path params,
                         request fields from the Pydantic model the handler takes (required = no default)
  client_calls(sources)  fetch(...) calls in JS/TS: method, path (template / concatenated parts become {param}),
                         JSON body keys from JSON.stringify({...})
  match(calls, routes)   per call: the route it reaches, or why none does (path, method, fields)
  check_contract(...)    which contract operations each side implements / uses, and what it adds
"""

import ast
import re
from typing import Any, Dict, List, Optional, Tuple

HTTP = ("get", "post", "put", "patch", "delete")


def _norm(path: str) -> str:
    path = "/" + path.strip().lstrip("/")
    path = re.sub(r"\{[^}]*\}", "{}", path)
    return path.rstrip("/") or "/"


# --- backend ------------------------------------------------------------------------------------------------

def _model_fields(tree: ast.Module) -> Dict[str, Dict[str, Any]]:
    """Pydantic-style classes: {class: {field: (required, type name)}}."""
    out = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and any((isinstance(b, ast.Name) and b.id == "BaseModel") or
                                                   (isinstance(b, ast.Attribute) and b.attr == "BaseModel") for b in node.bases):
            fields = {}
            for st in node.body:
                if isinstance(st, ast.AnnAssign) and isinstance(st.target, ast.Name):
                    t = st.annotation
                    tname = t.id if isinstance(t, ast.Name) else (t.value.id if isinstance(t, ast.Subscript)
                                                                  and isinstance(t.value, ast.Name) else "str")
                    fields[st.target.id] = (st.value is None, tname)
            out[node.name] = fields
    return out


def routes(sources: Dict[str, str]) -> List[Dict[str, Any]]:
    found = []
    for rel, src in sources.items():
        if not rel.endswith(".py") or "/tests/" in f"/{rel}" or rel.split("/")[-1].startswith("test_"):
            continue
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        prefixes: Dict[str, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) and len(node.targets) == 1 \
                    and isinstance(node.targets[0], ast.Name):
                fn = node.value.func
                if (isinstance(fn, ast.Name) and fn.id in ("APIRouter", "FastAPI")) or (isinstance(fn, ast.Attribute) and fn.attr == "APIRouter"):
                    pre = next((k.value.value for k in node.value.keywords if k.arg == "prefix"
                                and isinstance(k.value, ast.Constant)), "")
                    prefixes[node.targets[0].id] = pre or ""
        models = _model_fields(tree)
        for fn in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
            for dec in fn.decorator_list:
                if not (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr in HTTP
                        and isinstance(dec.func.value, ast.Name) and dec.args and isinstance(dec.args[0], ast.Constant)):
                    continue
                owner = dec.func.value.id
                path = prefixes.get(owner, "") + str(dec.args[0].value)
                params = set(re.findall(r"\{(\w+)\}", path))
                body, required, types = [], [], {}
                for a in fn.args.args:
                    ann = a.annotation
                    name = ann.id if isinstance(ann, ast.Name) else None
                    if name in models:
                        body = sorted(models[name])
                        required = sorted(k for k, (req, _) in models[name].items() if req)
                        types = {k: t for k, (_, t) in models[name].items()}
                found.append({"method": dec.func.attr.upper(), "path": path, "file": rel, "line": fn.lineno,
                              "handler": fn.name, "path_params": sorted(params), "body_fields": body,
                              "required_fields": required, "field_types": types})
    return found


# --- frontend -------------------------------------------------------------------------------------------------

def _balanced(s: str, start: int) -> int:
    """Index just after the expression that starts at s[start] (stops at a top-level ',' or ')')."""
    depth, i, quote = 0, start, None
    while i < len(s):
        c = s[i]
        if quote:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = None
            elif quote == "`" and s.startswith("${", i):
                j = _balanced(s, i + 2)
                i = j + 1
                continue
        elif c in "'\"`":
            quote = c
        elif c in "([{":
            depth += 1
        elif c in ")]}":
            if depth == 0:
                return i
            depth -= 1
        elif c == "," and depth == 0:
            return i
        i += 1
    return i


def _url_path(expr: str) -> Optional[str]:
    expr = expr.strip()
    if expr.startswith("`"):
        body = expr[1:-1] if expr.endswith("`") else expr[1:]
        parts = re.split(r"\$\{[^}]*\}", body)
        url = "{}".join(parts)
    else:
        pieces = [p.strip() for p in re.split(r"\s*\+\s*", expr)]
        url = "".join(p[1:-1] if p[:1] in "'\"" and p[-1:] == p[:1] else "{}" for p in pieces)
    if "/" not in url:
        return None
    url = url[url.index("/"):] if not url.startswith("{}/") else url[2:]
    url = url.split("?")[0]
    return url if url.startswith("/") else None


def _body_keys(opts: str) -> Optional[List[str]]:
    m = re.search(r"JSON\.stringify\(\s*\{", opts)
    if not m:
        return None
    start = m.end()
    end = start
    depth = 1
    while end < len(opts) and depth:
        depth += {"{": 1, "}": -1}.get(opts[end], 0)
        end += 1
    inner = opts[start:end - 1]
    keys, part, d = [], "", 0
    for c in inner + ",":
        if c in "([{":
            d += 1
        elif c in ")]}":
            d -= 1
        if c == "," and d == 0:
            k = part.strip()
            if k and not k.startswith("..."):
                keys.append(re.split(r"\s*:\s*", k, maxsplit=1)[0].strip("'\" "))
            part = ""
        else:
            part += c
    return sorted(k for k in keys if re.fullmatch(r"\w+", k))


def client_calls(sources: Dict[str, str]) -> List[Dict[str, Any]]:
    calls = []
    for rel, src in sources.items():
        if not rel.endswith((".js", ".jsx", ".ts", ".tsx", ".mjs")):
            continue
        for m in re.finditer(r"\bfetch\s*\(", src):
            a_end = _balanced(src, m.end())
            url = _url_path(src[m.end():a_end])
            opts = ""
            if a_end < len(src) and src[a_end] == ",":
                o_end = _balanced(src, a_end + 1)
                opts = src[a_end + 1:o_end]
            meth = re.search(r"method\s*:\s*['\"](\w+)['\"]", opts)
            calls.append({"file": rel, "line": src[:m.start()].count("\n") + 1, "path": url,
                          "method": (meth.group(1) if meth else "GET").upper(), "body_fields": _body_keys(opts),
                          "resolved": url is not None})
    return calls


# --- matching -------------------------------------------------------------------------------------------------

def match(calls: List[Dict[str, Any]], available: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for c in calls:
        if not c["resolved"]:
            out.append({**c, "status": "unresolved", "reason": "the URL is built in a way that cannot be read statically"})
            continue
        same_path = [r for r in available if _norm(r["path"]) == _norm(c["path"])]
        route = next((r for r in same_path if r["method"] == c["method"]), None)
        if route is None:
            reason = (f"no {c['method']} route for this path (the backend has {', '.join(r['method'] for r in same_path)})"
                      if same_path else "no backend route has this path")
            out.append({**c, "status": "mismatch", "reason": reason})
            continue
        problems = []
        if c["body_fields"] is not None and route["body_fields"]:
            unknown = sorted(set(c["body_fields"]) - set(route["body_fields"]))
            missing = sorted(set(route["required_fields"]) - set(c["body_fields"]))
            if unknown:
                problems.append(f"sends fields the backend does not accept: {unknown}")
            if missing:
                problems.append(f"omits required fields: {missing}")
        elif c["method"] in ("POST", "PUT", "PATCH") and route["required_fields"] and not c["body_fields"]:
            problems.append(f"sends no JSON body; the backend requires {route['required_fields']}")
        out.append({**c, "status": "mismatch" if problems else "ok", "reason": "; ".join(problems),
                    "route": {k: route[k] for k in ("method", "path", "file", "line", "handler", "body_fields", "required_fields",
                                                    "field_types")}})
    return out


def check_contract(contract_endpoints: List[Dict[str, Any]], implemented: List[Dict[str, Any]],
                   used: List[Dict[str, Any]]) -> Dict[str, Any]:
    def key(m, p):
        return f"{m.upper()} {_norm(p)}"
    contract = {key(e["method"], e["path"]): e for e in contract_endpoints}
    impl = {key(r["method"], r["path"]): r for r in implemented}
    use = {key(c["method"], c["path"]): c for c in used if c["resolved"]}
    return {
        "not_implemented": sorted(k for k in contract if k not in impl),
        "not_in_contract_backend": sorted(k for k in impl if k not in contract),
        "not_used_by_client": sorted(k for k in contract if k not in use),
        "not_in_contract_client": sorted(k for k in use if k not in contract),
        "field_drift_backend": sorted(
            k for k, e in contract.items() if k in impl and e.get("request_fields") and impl[k]["body_fields"]
            and set(e["request_fields"]) != set(impl[k]["body_fields"])),
        "field_drift_client": sorted(
            k for k, e in contract.items() if k in use and e.get("request_fields") and use[k]["body_fields"] is not None
            and set(e["request_fields"]) != set(use[k]["body_fields"])),
    }


def sides(contract_endpoints, implemented, used) -> Tuple[List[str], List[str]]:
    """Which side departs from the contract: (backend deviations, client deviations). Extra backend routes the
    contract does not mention (for example an existing /health) are not deviations from it."""
    c = check_contract(contract_endpoints, implemented, used)
    return (c["not_implemented"] + c["field_drift_backend"], c["not_in_contract_client"] + c["field_drift_client"])
