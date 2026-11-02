"""
What each component actually exposes or calls, read from its code (not from what an agent says about it):

  routes(sources)        FastAPI routes: method, full path (APIRouter prefix in the same file), path params,
                         request fields from the Pydantic model the handler takes (required = no default), and
                         (v2) the request/response JSON Schemas, status_code, response class, query params,
                         headers, auth dependencies and the HTTPException statuses the handler raises - all
                         labelled "static" (read from the AST; runtime checks decide)
  client_calls(sources)  fetch(...) calls in JS/TS: method, path (template / concatenated parts become {param}),
                         JSON body keys from JSON.stringify({...}), and (v2) which expressions fill the path and
                         body, the headers it sets and whether it sends an Authorization header
  client_exports(...)    the exported functions of a client module, their parameters and the calls inside them
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

def _ann(t) -> Dict[str, Any]:
    """A type annotation -> {"type": name, "nullable": bool, "items": name}."""
    if t is None:
        return {"type": None}
    if isinstance(t, ast.Name):
        return {"type": t.id}
    if isinstance(t, ast.Attribute):
        return {"type": t.attr}
    if isinstance(t, ast.Constant) and isinstance(t.value, str):
        return {"type": t.value}
    if isinstance(t, ast.BinOp) and isinstance(t.op, ast.BitOr):
        sides = [x for x in (t.left, t.right) if not (isinstance(x, ast.Constant) and x.value is None)]
        return {**_ann(sides[0]), "nullable": len(sides) == 1} if sides else {"type": None}
    if isinstance(t, ast.Subscript):
        outer = _ann(t.value)["type"]
        inner = t.slice
        if outer == "Optional":
            return {**_ann(inner), "nullable": True}
        if outer in ("List", "list", "Sequence"):
            return {"type": "list", "items": _ann(inner)["type"]}
        if outer in ("Dict", "dict"):
            return {"type": "dict"}
        if outer == "Annotated" and isinstance(inner, ast.Tuple) and inner.elts:
            return _ann(inner.elts[0])
        return {"type": outer}
    return {"type": None}


def _model_fields(tree: ast.Module) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Pydantic-style classes: {class: {field: {"required", "type", "nullable", "items"}}}."""
    out = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and any((isinstance(b, ast.Name) and b.id == "BaseModel") or
                                                   (isinstance(b, ast.Attribute) and b.attr == "BaseModel") for b in node.bases):
            fields = {}
            for st in node.body:
                if isinstance(st, ast.AnnAssign) and isinstance(st.target, ast.Name):
                    info = _ann(st.annotation)
                    required = st.value is None or (isinstance(st.value, ast.Call) and st.value.args and
                                                    isinstance(st.value.args[0], ast.Constant) and st.value.args[0].value is Ellipsis)
                    fields[st.target.id] = {"required": bool(required), "type": info.get("type") or "str",
                                            "nullable": bool(info.get("nullable")), "items": info.get("items")}
            out[node.name] = fields
    return out


def _status(node) -> Optional[int]:
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return node.value
    if isinstance(node, ast.Attribute):
        m = re.match(r"HTTP_(\d{3})", node.attr)
        return int(m.group(1)) if m else None
    return None


AUTH_HINT = re.compile(r"auth|user|token|current|security|bearer|oauth|login|jwt", re.I)


def _call_name(node) -> str:
    if isinstance(node, ast.Call):
        f = node.func
        return f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else ""
    return ""


def _depends_target(node) -> Optional[str]:
    """Depends(get_current_user) / Security(x) -> 'get_current_user'."""
    if _call_name(node) in ("Depends", "Security") and node.args:
        a = node.args[0]
        return a.id if isinstance(a, ast.Name) else a.attr if isinstance(a, ast.Attribute) else _call_name(a) or None
    return None


def routes(sources: Dict[str, str]) -> List[Dict[str, Any]]:
    from backend.swarm.schemas import PY_TYPES, model_schema
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
        bearer_schemes = {n.targets[0].id for n in ast.walk(tree) if isinstance(n, ast.Assign) and len(n.targets) == 1
                          and isinstance(n.targets[0], ast.Name) and _call_name(n.value) in ("HTTPBearer", "OAuth2PasswordBearer",
                                                                                            "APIKeyHeader")}
        auth_funcs = {f.name for f in ast.walk(tree) if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))
                      and any(_depends_target(d) in bearer_schemes for d in f.args.defaults + f.args.kw_defaults if d is not None)}

        def schema_of(ann) -> Optional[Dict[str, Any]]:
            info = _ann(ann)
            if info.get("type") in models:
                return model_schema(models[info["type"]])
            if info.get("type") == "list" and info.get("items") in models:
                return {"type": "array", "items": model_schema(models[info["items"]])}
            if PY_TYPES.get(info.get("type") or ""):
                return {"type": PY_TYPES[info["type"]]}
            return None
        for fn in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
            for dec in fn.decorator_list:
                if not (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr in HTTP
                        and isinstance(dec.func.value, ast.Name) and dec.args and isinstance(dec.args[0], ast.Constant)):
                    continue
                owner = dec.func.value.id
                path = prefixes.get(owner, "") + str(dec.args[0].value)
                params = set(re.findall(r"\{(\w+)\}", path))
                kw = {k.arg: k.value for k in dec.keywords if k.arg}
                body, required, types, request_schema = [], [], {}, None
                query, headers, path_types, auth_deps = {}, {}, {}, []
                args = fn.args.args
                defaults = [None] * (len(args) - len(fn.args.defaults)) + list(fn.args.defaults)
                for a, default in list(zip(args, defaults)) + list(zip(fn.args.kwonlyargs, fn.args.kw_defaults)):
                    ann = a.annotation
                    info = _ann(ann)
                    name = info.get("type")
                    dep = _depends_target(default) if default is not None else None
                    if dep:
                        if dep in bearer_schemes or dep in auth_funcs or AUTH_HINT.search(dep):
                            auth_deps.append(dep)
                        continue
                    if name in models:
                        body = sorted(models[name])
                        required = sorted(k for k, f in models[name].items() if f["required"])
                        types = {k: f["type"] for k, f in models[name].items()}
                        request_schema = model_schema(models[name])
                        continue
                    if a.arg in params:
                        path_types[a.arg] = {"type": PY_TYPES[name]} if PY_TYPES.get(name or "") else {}
                        continue
                    if a.arg in ("request", "response", "background_tasks", "db", "session"):
                        continue
                    if _call_name(default) == "Header":
                        hreq = bool(default.args and isinstance(default.args[0], ast.Constant) and default.args[0].value is Ellipsis)
                        headers[a.arg.replace("_", "-")] = {"required": hreq}
                        if a.arg.lower() == "authorization":
                            auth_deps.append("Authorization header")
                        continue
                    qreq = default is None or (_call_name(default) == "Query" and default.args and isinstance(default.args[0], ast.Constant)
                                               and default.args[0].value is Ellipsis)
                    query[a.arg] = {"schema": {"type": PY_TYPES[name]} if PY_TYPES.get(name or "") else {}, "required": bool(qreq)}
                for d in (kw.get("dependencies").elts if isinstance(kw.get("dependencies"), ast.List) else []):
                    dep = _depends_target(d)
                    if dep and (dep in bearer_schemes or dep in auth_funcs or AUTH_HINT.search(dep)):
                        auth_deps.append(dep)
                status_code = _status(kw["status_code"]) if "status_code" in kw else None
                response_schema = schema_of(kw["response_model"]) if "response_model" in kw else schema_of(fn.returns)
                rclass = kw.get("response_class")
                rclass_name = rclass.id if isinstance(rclass, ast.Name) else rclass.attr if isinstance(rclass, ast.Attribute) else ""
                content_type = {"PlainTextResponse": "text/plain", "HTMLResponse": "text/html"}.get(rclass_name, "application/json")
                raises = sorted({c for n in ast.walk(fn) if isinstance(n, ast.Call) and _call_name(n) == "HTTPException"
                                 for c in [(_status(n.args[0]) if n.args else None) or
                                           next((_status(k.value) for k in n.keywords if k.arg == "status_code"), None)] if c})
                found.append({"method": dec.func.attr.upper(), "path": path, "file": rel, "line": fn.lineno,
                              "handler": fn.name, "path_params": sorted(params), "body_fields": body,
                              "required_fields": required, "field_types": types,
                              "request_schema": request_schema, "path_param_schemas": path_types, "query_params": query,
                              "headers": headers, "auth": "bearer" if auth_deps else "none", "auth_dependencies": sorted(set(auth_deps)),
                              "status_code": status_code or 200,
                              "status_code_explicit": status_code is not None, "response_schema": response_schema,
                              "response_content_type": content_type, "raises": raises, "basis": "static"})
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


def _url_parts(expr: str) -> Tuple[Optional[str], List[str]]:
    """The path a URL expression reaches and the expressions that fill its {} placeholders (the base URL
    placeholder in front of the path is dropped)."""
    expr = expr.strip()
    if expr.startswith("`"):
        body = expr[1:-1] if expr.endswith("`") else expr[1:]
        exprs = [x.strip() for x in re.findall(r"\$\{([^}]*)\}", body)]
        parts = re.split(r"\$\{[^}]*\}", body)
        url = "{}".join(parts)
    else:
        pieces = [p.strip() for p in re.split(r"\s*\+\s*", expr)]
        exprs = [p for p in pieces if not (p[:1] in "'\"" and p[-1:] == p[:1])]
        url = "".join(p[1:-1] if p[:1] in "'\"" and p[-1:] == p[:1] else "{}" for p in pieces)
    if "/" not in url:
        return None, []
    if url.startswith("{}/") or (url.startswith("{}") and not url.startswith("{}{}")):
        url, exprs = url[2:], exprs[1:]
    elif not url.startswith("/"):
        cut = url.index("/")
        while cut < len(url) and url.startswith("//", cut):          # absolute URL: skip the scheme and host
            cut = url.index("/", cut + 2) if "/" in url[cut + 2:] else len(url)
        dropped = url[:cut].count("{}")
        url, exprs = url[cut:], exprs[dropped:]
    url = url.split("?")[0]
    return (url, exprs[:url.count("{}")]) if url.startswith("/") else (None, [])


def _url_path(expr: str) -> Optional[str]:
    return _url_parts(expr)[0]


def _body_map(opts: str) -> Tuple[Optional[Dict[str, str]], Optional[str]]:
    """JSON.stringify({a, b: expr}) -> ({"a": "a", "b": "expr"}, None); JSON.stringify(x) -> (None, "x")."""
    m = re.search(r"JSON\.stringify\(\s*", opts)
    if not m:
        return None, None
    if not opts[m.end():].startswith("{"):
        end = _balanced(opts, m.end())
        return None, opts[m.end():end].strip()
    start, end, depth = m.end() + 1, m.end() + 1, 1
    while end < len(opts) and depth:
        depth += {"{": 1, "}": -1}.get(opts[end], 0)
        end += 1
    inner = opts[start:end - 1]
    out, part, d = {}, "", 0
    for c in inner + ",":
        if c in "([{":
            d += 1
        elif c in ")]}":
            d -= 1
        if c == "," and d == 0:
            k = part.strip()
            if k and not k.startswith("..."):
                kv = re.split(r"\s*:\s*", k, maxsplit=1)
                key = kv[0].strip("'\" ")
                if re.fullmatch(r"\w+", key):
                    out[key] = (kv[1] if len(kv) > 1 else key).strip()
            part = ""
        else:
            part += c
    return out, None


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
            url, exprs = _url_parts(src[m.end():a_end])
            opts = ""
            if a_end < len(src) and src[a_end] == ",":
                o_end = _balanced(src, a_end + 1)
                opts = src[a_end + 1:o_end]
            meth = re.search(r"method\s*:\s*['\"](\w+)['\"]", opts)
            body_map, body_expr = _body_map(opts)
            hdr = re.search(r"headers\s*:\s*\{([^}]*)\}", opts)
            header_names = sorted({h.strip("'\" ").lower() for h in re.findall(r"(['\"]?[\w-]+['\"]?)\s*:", hdr.group(1))}) if hdr else []
            calls.append({"file": rel, "line": src[:m.start()].count("\n") + 1, "path": url,
                          "method": (meth.group(1) if meth else "GET").upper(), "body_fields": _body_keys(opts),
                          "resolved": url is not None, "path_exprs": exprs, "body_map": body_map, "body_expr": body_expr,
                          "headers": header_names, "auth_header": bool(re.search(r"authorization", opts, re.I)),
                          "basis": "static"})
    return calls


EXPORT_RE = re.compile(r"export\s+(?:default\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)"
                       r"|export\s+const\s+(\w+)\s*=\s*(?:async\s*)?(?:\(([^)]*)\)|(\w+))\s*=>")


def client_exports(sources: Dict[str, str]) -> List[Dict[str, Any]]:
    """Exported functions: name, parameter names, line range and the fetch calls inside them."""
    out = []
    for rel, src in sources.items():
        if not rel.endswith((".js", ".mjs")):
            continue
        calls = client_calls({rel: src})
        found = list(EXPORT_RE.finditer(src))
        for i, m in enumerate(found):
            name = m.group(1) or m.group(3)
            raw = m.group(2) if m.group(1) else (m.group(4) if m.group(4) is not None else m.group(5) or "")
            params = [re.split(r"\s*=\s*", p.strip())[0] for p in raw.split(",") if p.strip()]
            start = src[:m.start()].count("\n") + 1
            end = src[:found[i + 1].start()].count("\n") + 1 if i + 1 < len(found) else src.count("\n") + 2
            out.append({"module": rel, "export": name, "params": params, "line": start,
                        "calls": [c for c in calls if start <= c["line"] < end]})
    return out


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
