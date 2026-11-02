"""
What a generated project actually implements, read from its files (nothing is executed):

  backend      FastAPI routes - Swarm's extraction (swarm/interfaces.routes: method, full path, request / response
               JSON Schemas, status codes, auth dependencies, raised statuses) - plus error bodies built with
               JSONResponse(status_code>=400, content={...}) and exception handlers
  frontend     HTTP calls: fetch() and axios (axios.get(...), axios instances from axios.create, imported ones too),
               with the URL resolved through string constants (const API = "http://host/api"), axios baseURL and the
               Vite dev-proxy rewrite; JSON body keys; whether an Authorization header is sent; and - a heuristic,
               labelled as such - which response fields the code reads and whether it treats the body as a list
  database     SQL DDL (CREATE TABLE in *.sql), SQLAlchemy / SQLModel models, migrations (Alembic op.create_table /
               op.add_column, SQL migration files) and whether the app creates tables itself (metadata.create_all)
  environment  variables read: os.getenv / os.environ (backend), import.meta.env / process.env (frontend)

snapshot(project) returns all of it plus `fingerprint`, the per-operation / per-table summary drift detection compares.
"""

import ast
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.swarm import interfaces as itf

JS = (".js", ".jsx", ".ts", ".tsx", ".mjs")
MAX_FILE = 400_000
NOT_FIELDS = {"length", "map", "filter", "forEach", "find", "findIndex", "some", "every", "reduce", "slice", "concat",
              "includes", "join", "sort", "push", "then", "catch", "finally", "json", "status", "ok", "headers", "toString",
              "keys", "values", "entries", "statusText", "text", "blob", "message", "response", "config", "request",
              "indexOf", "trim", "toLowerCase", "toUpperCase", "split", "replace", "startsWith", "endsWith"}
SQL_TYPES = {"int": "integer", "integer": "integer", "bigint": "integer", "smallint": "integer", "serial": "integer",
             "bigserial": "integer", "varchar": "string", "text": "string", "char": "string", "character": "string",
             "uuid": "string", "citext": "string", "boolean": "boolean", "bool": "boolean", "real": "number",
             "float": "number", "double": "number", "numeric": "number", "decimal": "number", "timestamp": "string",
             "timestamptz": "string", "datetime": "string", "date": "string", "time": "string", "json": "object",
             "jsonb": "object", "blob": "string", "bytea": "string"}
SQL_FORMATS = {"timestamp": "date-time", "timestamptz": "date-time", "datetime": "date-time", "date": "date", "uuid": "uuid"}
ORM_TYPES = {"Integer": "integer", "BigInteger": "integer", "SmallInteger": "integer", "String": "string", "Text": "string",
             "Unicode": "string", "UnicodeText": "string", "Boolean": "boolean", "Float": "number", "Numeric": "number",
             "DateTime": "string", "Date": "string", "Time": "string", "JSON": "object", "Uuid": "string", "UUID": "string",
             "Enum": "string", "LargeBinary": "string", "int": "integer", "str": "string", "float": "number",
             "bool": "boolean", "datetime": "string", "date": "string", "dict": "object", "uuid.UUID": "string"}
ORM_FORMATS = {"DateTime": "date-time", "datetime": "date-time", "Date": "date", "date": "date", "Uuid": "uuid", "UUID": "uuid"}


def read_sources(project: Path) -> Dict[str, str]:
    """The project's text sources (the export reader: dependency folders, caches and secret files are left out)."""
    from backend.routes.export import _read_project_dir
    return {k: v for k, v in _read_project_dir(Path(project)).items() if len(v) <= MAX_FILE}


def _is_test(rel: str) -> bool:
    name = rel.rsplit("/", 1)[-1]
    return ("/tests/" in f"/{rel}" or "/__tests__/" in f"/{rel}" or name.startswith("test_") or name == "conftest.py"
            or name.endswith(("_test.py", ".test.js", ".test.jsx", ".test.ts", ".spec.js", ".spec.ts")))


# --- backend ---------------------------------------------------------------------------------------------------------

def _status_of(node) -> Optional[int]:
    return itf._status(node)


def error_bodies(sources: Dict[str, str]) -> List[Dict[str, Any]]:
    """JSONResponse(status_code>=400 | inside an exception handler, content={...}): the keys of each error body."""
    out = []
    for rel, src in sources.items():
        if not rel.endswith(".py") or _is_test(rel):
            continue
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        handlers = {f.name for f in ast.walk(tree) if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and any(isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr == "exception_handler"
                            for d in f.decorator_list)}
        for fn in [f for f in ast.walk(tree) if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))]:
            for n in ast.walk(fn):
                if not (isinstance(n, ast.Call) and itf._call_name(n) == "JSONResponse"):
                    continue
                kw = {k.arg: k.value for k in n.keywords if k.arg}
                status = _status_of(kw["status_code"]) if "status_code" in kw else None
                content = kw.get("content") or (n.args[0] if n.args else None)
                if not isinstance(content, ast.Dict):
                    continue
                keys = sorted(k.value for k in content.keys if isinstance(k, ast.Constant) and isinstance(k.value, str))
                if (status and status >= 400) or fn.name in handlers:
                    out.append({"file": rel, "line": n.lineno, "status": status, "keys": keys, "handler": fn.name in handlers})
    return out


def backend(sources: Dict[str, str]) -> Dict[str, Any]:
    py = {k: v for k, v in sources.items() if k.endswith(".py") and not _is_test(k)}
    routes = itf.routes(py)
    return {"routes": routes, "error_bodies": error_bodies(py),
            "files": sorted({r["file"] for r in routes}), "python_files": len(py)}


# --- frontend --------------------------------------------------------------------------------------------------------

_CONST = re.compile(r"(?:^|\n)\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*([^;\n]+)")
_IMPORT = re.compile(r"import\s+(?:(\w+)\s*,?\s*)?(?:\{([^}]*)\})?\s*from\s*['\"]([^'\"]+)['\"]")
_STR = re.compile(r"'([^'\\]*(?:\\.[^'\\]*)*)'|\"([^\"\\]*(?:\\.[^\"\\]*)*)\"|`([^`$]*)`")


def _path_part(value: str) -> Optional[str]:
    """The path a base-URL string contributes ('http://localhost:8000/api' -> '/api', '/api/' -> '/api')."""
    v = value.strip()
    m = re.match(r"^[a-z]+://[^/]+(/.*)?$", v, re.I)
    if m:
        p = m.group(1) or ""
    elif v.startswith("/"):
        p = v
    else:
        return None
    p = p.split("?")[0].rstrip("/")
    return p


def _literal_base(expr: str) -> Optional[str]:
    """`import.meta.env.VITE_API || "http://x/api"` -> '/api' (the literal fallback); None when no literal is a URL."""
    for m in _STR.finditer(expr):
        s = next(g for g in m.groups() if g is not None)
        p = _path_part(s)
        if p is not None:
            return p
    return None


def _resolve(rel: str, spec: str, files: Dict[str, str]) -> Optional[str]:
    if not spec.startswith("."):
        return None
    base = rel.rsplit("/", 1)[0] if "/" in rel else ""
    parts = [p for p in (base + "/" + spec).split("/") if p not in ("", ".")]
    out: List[str] = []
    for p in parts:
        if p == "..":
            if out:
                out.pop()
        else:
            out.append(p)
    stem = "/".join(out)
    for cand in (stem, *(stem + e for e in JS), *(f"{stem}/index{e}" for e in JS)):
        if cand in files:
            return cand
    return None


def _module_info(files: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
    """Per JS module: string constants (name -> base path), axios instances (name -> baseURL path) and its default export."""
    info: Dict[str, Dict[str, Any]] = {}
    for rel, src in files.items():
        consts, instances = {}, {}
        for m in _CONST.finditer(src):
            name, expr = m.group(1), m.group(2)
            if "axios.create" in expr:
                start = src.find("axios.create", m.start())
                body = src[start:itf._balanced(src, src.find("(", start) + 1) + 1] if start >= 0 else ""
                bm = re.search(r"baseURL\s*:\s*([^,}\n]+)", body)
                base = None
                if bm:
                    base = _literal_base(bm.group(1))
                    ident = re.match(r"\s*(\w+)\s*$", bm.group(1))
                    if base is None and ident and ident.group(1) in consts:
                        base = consts[ident.group(1)]
                instances[name] = {"base": base or "", "auth": bool(re.search(r"authorization", body, re.I))}
            else:
                base = _literal_base(expr)
                if base is not None and re.match(r"\s*(['\"`]|import\.meta|process\.env)", expr):
                    consts[name] = base
        default = re.search(r"export\s+default\s+(\w+)", src)
        interceptor_auth = bool(re.search(r"interceptors\.request\.use[\s\S]{0,600}?authorization", src, re.I))
        for inst in instances.values():
            inst["auth"] = inst["auth"] or interceptor_auth
        info[rel] = {"consts": consts, "instances": instances, "default": default.group(1) if default else None,
                     "exports": set(re.findall(r"export\s+(?:const|let|var|function)\s+(\w+)", src))}
    # names imported from other modules
    for rel, src in files.items():
        for m in _IMPORT.finditer(src):
            target = _resolve(rel, m.group(3), files)
            if not target or target not in info:
                continue
            t = info[target]
            names = [(m.group(1), t["default"])] if m.group(1) else []
            names += [(n.split(" as ")[-1].strip(), n.split(" as ")[0].strip()) for n in (m.group(2) or "").split(",") if n.strip()]
            for local, remote in names:
                if not remote:
                    continue
                if remote in t["instances"]:
                    info[rel]["instances"].setdefault(local, t["instances"][remote])
                elif remote in t["consts"]:
                    info[rel]["consts"].setdefault(local, t["consts"][remote])
    return info


def proxy_rewrites(sources: Dict[str, str]) -> List[Tuple[str, str]]:
    """Vite dev-server proxy rules that strip a prefix: [('/api', '')]. The browser calls /api/x, the backend gets /x."""
    out = []
    for rel, src in sources.items():
        if not re.search(r"(^|/)vite\.config\.(js|ts|mjs)$", rel):
            continue
        for m in re.finditer(r"['\"](/[\w\-/]+)['\"]\s*:\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", src):
            rw = re.search(r"rewrite\s*:[^\n]*replace\(\s*/\^\\?(/[\w\-/\\]+)/\s*,\s*['\"]([^'\"]*)['\"]", m.group(2))
            if rw:
                out.append((rw.group(1).replace("\\", ""), rw.group(2)))
    return out


_CALL = re.compile(r"\b(fetch|axios(?:\.(get|post|put|patch|delete))?|(\w+)\.(get|post|put|patch|delete))\s*\(")


def _args(src: str, open_paren: int, limit: int = 3) -> Tuple[List[str], int]:
    """The top-level arguments of a call whose '(' ends at open_paren, and the index just after its ')'."""
    args, i = [], open_paren
    while len(args) < limit:
        end = itf._balanced(src, i)
        args.append(src[i:end])
        if end < len(src) and src[end] == ",":
            i = end + 1
            continue
        i = end
        break
    close = src.find(")", i)
    return [a.strip() for a in args if a.strip()], (close if close >= 0 else i) + 1


def _resolved_url(expr: str, consts: Dict[str, str], base: str) -> Tuple[Optional[str], List[str]]:
    url, exprs = itf._url_parts(expr)
    e = expr.strip()
    lead = re.match(r"^`\$\{\s*(\w+)\s*\}|^(\w+)\s*\+", e)
    prefix = base or ""
    if lead and (lead.group(1) or lead.group(2)) in consts:
        prefix = consts[lead.group(1) or lead.group(2)] + prefix
    if url is None:
        return None, []
    return (prefix + url if not url.startswith(prefix + "/") or not prefix else url), exprs


def _receiver(src: str, call_start: int) -> Optional[str]:
    """The variable (or destructuring pattern) an awaited call is assigned to."""
    line_start = src.rfind("\n", 0, call_start) + 1
    before = src[line_start:call_start]
    m = re.search(r"(?:const|let|var)\s+(\{[^}]*\}|\w+)\s*=\s*(?:await\s*\(?\s*await\s*\(?|await\s*)?\s*$", before) \
        or re.search(r"(?:^|[;\s])(\w+)\s*=\s*(?:await\s*)?\s*$", before)
    return m.group(1).strip() if m else None


def _destructured(pattern: str) -> List[str]:
    out = []
    for part in pattern.strip("{} ").split(","):
        name = part.split(":")[0].split("=")[0].strip()
        if re.fullmatch(r"\w+", name or ""):
            out.append(name)
    return out


def _alias(pattern: str, key: str) -> Optional[str]:
    """`{ data: tasks }` -> 'tasks' for key 'data'; `{ data }` -> 'data'."""
    for part in pattern.strip("{} ").split(","):
        bits = [b.strip() for b in part.split(":")]
        if bits[0] == key:
            return (bits[1] if len(bits) > 1 else bits[0]).split("=")[0].strip()
    return None


def _reads(src: str, start: int, end: int, kind: str) -> Dict[str, Any]:
    """Heuristic: the response fields the code reads after this call. Returns {"array", "item_fields", "top_fields",
    "envelope", "found"}; found=False when the response could not be followed (nothing is concluded then)."""
    tail = src[end:end + 2500]
    datas: List[str] = []
    fields: List[str] = []
    rec = _receiver(src, start)
    is_json_inline = bool(re.match(r"\s*\)\s*\.json\(\)", tail)) and kind == "fetch"
    if kind == "fetch":
        if rec and is_json_inline:
            (fields.extend(_destructured(rec)) if rec.startswith("{") else datas.append(rec))
        elif rec and not rec.startswith("{"):
            for m in re.finditer(rf"(?:const|let|var)\s+(\{{[^}}]*\}}|\w+)\s*=\s*await\s+{re.escape(rec)}\.json\(\)", tail):
                (fields.extend(_destructured(m.group(1))) if m.group(1).startswith("{") else datas.append(m.group(1)))
        th = re.match(r"\s*(?:\)\s*)?\.then\(\s*\(?\s*(\w+)\s*\)?\s*=>\s*\1\.json\(\)\s*\)\s*\.then\(\s*\(?\s*(\{[^}]*\}|\w+)\s*\)?\s*=>", tail)
        if th:
            (fields.extend(_destructured(th.group(2))) if th.group(2).startswith("{") else datas.append(th.group(2)))
    else:
        if rec:
            if rec.startswith("{"):
                alias = _alias(rec, "data")
                if alias:
                    datas.append(alias)
            else:
                datas.append(f"{rec}.data")
        th = re.match(r"\s*\.then\(\s*\(?\s*(\{[^}]*\}|\w+)\s*\)?\s*=>", tail)
        if th:
            datas.append(_alias(th.group(1), "data") if th.group(1).startswith("{") else f"{th.group(1)}.data")
    datas = [d for d in datas if d]
    array, items, top, envelope = None, set(), set(fields), set()
    region = tail[:1500]

    def item_reads(arr_expr: str, text: str) -> None:
        nonlocal array
        for m in re.finditer(rf"{re.escape(arr_expr)}\s*\.\s*(?:map|forEach|filter|find|some|every)\s*\(\s*\(?\s*(\w+)", text):
            array = True if array is None or array else array
            var = m.group(1)
            seg = text[m.end():m.end() + 600]
            items.update(f for f in re.findall(rf"\b{re.escape(var)}\.(\w+)", seg) if f not in NOT_FIELDS)
    for d in datas:
        item_reads(d, region)
        for f in re.findall(rf"{re.escape(d)}\.(\w+)", region):
            if f in NOT_FIELDS:
                continue
            if re.search(rf"{re.escape(d)}\.{f}\s*\.\s*(?:map|forEach|filter)\s*\(", region):
                envelope.add(f)
                item_reads(f"{d}.{f}", region)
                if array is None:
                    array = False
            else:
                top.add(f)
        for m in re.finditer(rf"(?:const|let|var)\s+(\{{[^}}]*\}})\s*=\s*{re.escape(d)}\b", region):
            top.update(_destructured(m.group(1)))
        for m in re.finditer(rf"\bset([A-Z]\w*)\(\s*{re.escape(d)}(?:\.(\w+))?\s*\)", region):
            state = m.group(1)[0].lower() + m.group(1)[1:]
            if m.group(2):
                envelope.add(m.group(2))
                if array is None:
                    array = False
            item_reads(state, src)
            if not m.group(2) and re.search(rf"\b{state}\s*\.\s*(?:map|forEach|filter)\s*\(", src) and array is None:
                array = True
    found = bool(datas or fields)
    if array is True and envelope:
        array = False
    return {"found": found, "array": array, "item_fields": sorted(items), "top_fields": sorted(top - envelope),
            "envelope": sorted(envelope), "basis": "static_heuristic"}


def frontend(sources: Dict[str, str]) -> Dict[str, Any]:
    files = {k: v for k, v in sources.items() if k.endswith(JS) and not _is_test(k) and "node_modules/" not in k
             and not re.search(r"(^|/)(vite|webpack|tailwind|postcss|eslint)\.config\.", k)}
    info = _module_info(files)
    rewrites = proxy_rewrites(sources)
    calls = []
    for rel, src in files.items():
        mi = info.get(rel) or {"consts": {}, "instances": {}}
        for m in _CALL.finditer(src):
            name = m.group(1)
            if name.startswith("axios.") or name == "axios":
                kind, method, base, inst_auth = "axios", (m.group(2) or "").upper(), "", False
                if name == "axios":
                    continue                                   # axios({...}) config calls: not read statically
            elif name == "fetch":
                kind, method, base, inst_auth = "fetch", "", "", False
            elif m.group(3) in mi["instances"]:
                inst = mi["instances"][m.group(3)]
                kind, method, base, inst_auth = "axios", m.group(4).upper(), inst["base"], inst["auth"]
            else:
                continue
            if name == "fetch" and src[max(0, m.start() - 1):m.start()] == "." and src[max(0, m.start() - 7):m.start()] != "window.":
                continue                                       # obj.fetch(...) is not the global fetch
            args, end = _args(src, m.end())
            if not args:
                continue
            first, rest = args[0], ",".join(args[1:])
            url, exprs = _resolved_url(first, mi["consts"], base)
            if kind == "fetch":
                meth = re.search(r"method\s*:\s*['\"](\w+)['\"]", rest)
                method = (meth.group(1) if meth else "GET").upper()
                body_map, body_expr = itf._body_map(rest)
                body = sorted(body_map) if body_map is not None else None
                auth = bool(re.search(r"authorization", rest, re.I)) or (
                    bool(re.search(r"headers\s*:\s*\w+\s*\(", rest)) and bool(re.search(r"authorization", src, re.I)))
            else:
                data_arg = args[1] if method in ("POST", "PUT", "PATCH") and len(args) > 1 else ""
                config = args[2] if method in ("POST", "PUT", "PATCH") and len(args) > 2 else (args[1] if len(args) > 1 and not data_arg else "")
                body_map, body_expr = (itf._body_map(f"JSON.stringify({data_arg})") if data_arg else (None, None))
                body = sorted(body_map) if body_map is not None else ([] if method in ("POST", "PUT", "PATCH") and not data_arg else None)
                auth = inst_auth or bool(re.search(r"authorization", config, re.I))
            rewritten = None
            if url:
                for pre, repl in rewrites:
                    if url == pre or url.startswith(pre + "/"):
                        rewritten, url = url, repl + url[len(pre):] or "/"
                        break
            calls.append({"file": rel, "line": src[:m.start()].count("\n") + 1, "start": m.start(), "end": end,
                          "client": kind, "method": method or "GET", "path": url, "url_expr": first.strip()[:300],
                          "browser_path": rewritten, "resolved": url is not None, "path_exprs": exprs,
                          "body_fields": body, "body_expr": body_expr, "auth_header": auth,
                          "reads": _reads(src, m.start(), end, kind), "basis": "static"})
    return {"calls": calls, "files": sorted({c["file"] for c in calls}), "js_files": len(files), "proxy_rewrites": rewrites}


# --- database --------------------------------------------------------------------------------------------------------

def _sql_type(t: str) -> Tuple[str, Optional[str]]:
    base = re.match(r"[A-Za-z]+", t or "")
    word = base.group(0).lower() if base else ""
    if word == "character" and "varying" in t.lower():
        word = "varchar"
    return SQL_TYPES.get(word, "unknown"), SQL_FORMATS.get(word)


def parse_sql(src: str, rel: str) -> Dict[str, Dict[str, Any]]:
    """CREATE TABLE / ALTER TABLE ... ADD COLUMN -> {table: {"columns": {name: {...}}, "file": rel}}."""
    tables: Dict[str, Dict[str, Any]] = {}
    text = re.sub(r"--[^\n]*", "", src)
    for m in re.finditer(r"create\s+table\s+(?:if\s+not\s+exists\s+)?[`\"\[]?(\w+)[`\"\]]?\s*\(", text, re.I):
        start = m.end()
        depth, i = 1, start
        while i < len(text) and depth:
            depth += {"(": 1, ")": -1}.get(text[i], 0)
            i += 1
        body = text[start:i - 1]
        cols: Dict[str, Dict[str, Any]] = {}
        table_pk: List[str] = []
        fks: Dict[str, str] = {}
        parts, depth, cur = [], 0, ""
        for ch in body:
            depth += {"(": 1, ")": -1}.get(ch, 0)
            if ch == "," and depth == 0:
                parts.append(cur)
                cur = ""
            else:
                cur += ch
        parts.append(cur)
        for p in (x.strip() for x in parts if x.strip()):
            low = p.lower()
            if low.startswith("primary key"):
                table_pk += [c.strip(' `"[]') for c in re.search(r"\(([^)]*)\)", p).group(1).split(",")] if "(" in p else []
                continue
            if low.startswith(("foreign key", "constraint")):
                fk = re.search(r"foreign\s+key\s*\(\s*[`\"]?(\w+)[`\"]?\s*\)\s*references\s+[`\"]?(\w+)[`\"]?\s*\(\s*[`\"]?(\w+)", p, re.I)
                if fk:
                    fks[fk.group(1)] = f"{fk.group(2)}.{fk.group(3)}"
                continue
            if low.startswith(("unique", "check", "index", "key ")):
                continue
            cm = re.match(r"[`\"\[]?(\w+)[`\"\]]?\s+([A-Za-z]+(?:\s+varying)?(?:\s*\([^)]*\))?)(.*)$", p, re.S)
            if not cm:
                continue
            ftype, fmt = _sql_type(cm.group(2))
            rest = cm.group(3).lower()
            ref = re.search(r"references\s+[`\"]?(\w+)[`\"]?\s*(?:\(\s*[`\"]?(\w+))?", rest)
            pk = "primary key" in rest
            cols[cm.group(1)] = {"type": ftype, "format": fmt, "sql_type": cm.group(2).strip(),
                                 "nullable": not pk and "not null" not in rest, "primary_key": pk,
                                 "references": f"{ref.group(1)}.{ref.group(2) or 'id'}" if ref else None,
                                 "default": "default" in rest or "autoincrement" in rest or "serial" in cm.group(2).lower()}
        for c in table_pk:
            if c in cols:
                cols[c].update(primary_key=True, nullable=False)
        for c, ref in fks.items():
            if c in cols:
                cols[c]["references"] = ref
        tables[m.group(1)] = {"columns": cols, "file": rel, "line": text[:m.start()].count("\n") + 1}
    for m in re.finditer(r"alter\s+table\s+[`\"]?(\w+)[`\"]?\s+add\s+(?:column\s+)?[`\"]?(\w+)[`\"]?\s+([A-Za-z]+(?:\s*\([^)]*\))?)([^;]*)",
                         text, re.I):
        ftype, fmt = _sql_type(m.group(3))
        rest = m.group(4).lower()
        tables.setdefault(m.group(1), {"columns": {}, "file": rel, "line": text[:m.start()].count("\n") + 1})
        tables[m.group(1)]["columns"][m.group(2)] = {"type": ftype, "format": fmt, "sql_type": m.group(3), "nullable": "not null" not in rest,
                                                     "primary_key": False, "references": None, "default": "default" in rest}
    return tables


def _const(node) -> Any:
    return node.value if isinstance(node, ast.Constant) else None


def _orm_type(node) -> Tuple[str, Optional[str]]:
    name = node.id if isinstance(node, ast.Name) else node.attr if isinstance(node, ast.Attribute) else \
        itf._call_name(node) if isinstance(node, ast.Call) else ""
    return ORM_TYPES.get(name, "unknown"), ORM_FORMATS.get(name)


def parse_orm(src: str, rel: str) -> Dict[str, Dict[str, Any]]:
    """SQLAlchemy (Column / mapped_column, Mapped[...]) and SQLModel (table=True) models -> {table: {...}}."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return {}
    out = {}
    for cls in [n for n in tree.body if isinstance(n, ast.ClassDef)]:
        tablename = None
        sqlmodel_table = any(k.arg == "table" and _const(k.value) is True for k in cls.keywords)
        for st in cls.body:
            if isinstance(st, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__tablename__" for t in st.targets):
                tablename = _const(st.value)
        if not tablename and not sqlmodel_table:
            continue
        cols: Dict[str, Dict[str, Any]] = {}
        for st in cls.body:
            target, value, ann = None, None, None
            if isinstance(st, ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], ast.Name):
                target, value = st.targets[0].id, st.value
            elif isinstance(st, ast.AnnAssign) and isinstance(st.target, ast.Name):
                target, value, ann = st.target.id, st.value, st.annotation
            if not target or target.startswith("__"):
                continue
            call = value if isinstance(value, ast.Call) else None
            cname = itf._call_name(call) if call else ""
            if cname in ("relationship", "Relationship", "association_proxy"):
                continue
            ann_info = itf._ann(ann.slice if isinstance(ann, ast.Subscript) and itf._ann(ann.value)["type"] == "Mapped" else ann) if ann is not None else {}
            if cname not in ("Column", "mapped_column", "Field") and not (sqlmodel_table and ann is not None) and not \
                    (ann is not None and isinstance(ann, ast.Subscript) and itf._ann(ann.value)["type"] == "Mapped"):
                continue
            kw = {k.arg: k.value for k in (call.keywords if call else []) if k.arg}
            ftype, fmt = "unknown", None
            ref = None
            for a in (call.args if call else []):
                if isinstance(a, ast.Constant) and isinstance(a.value, str) and cname == "Column":
                    continue
                if itf._call_name(a) == "ForeignKey" and a.args:
                    ref = _const(a.args[0])
                elif ftype == "unknown":
                    ftype, fmt = _orm_type(a)
            if ftype == "unknown" and ann_info.get("type"):
                ftype = ORM_TYPES.get(ann_info["type"], "unknown")
                fmt = ORM_FORMATS.get(ann_info["type"])
            if "foreign_key" in kw:
                ref = _const(kw["foreign_key"])
            pk = _const(kw.get("primary_key")) is True if "primary_key" in kw else False
            if "nullable" in kw:
                nullable = _const(kw["nullable"]) is not False
            elif cname == "Column":
                nullable = not pk
            else:
                nullable = bool(ann_info.get("nullable")) and not pk
            cols[target] = {"type": ftype, "format": fmt, "nullable": nullable, "primary_key": pk,
                            "references": ref, "default": "default" in kw or "server_default" in kw}
        out[tablename or cls.name.lower()] = {"columns": cols, "file": rel, "line": cls.lineno, "class": cls.name}
    return out


def parse_alembic(src: str) -> Dict[str, List[str]]:
    tables: Dict[str, List[str]] = {}
    for m in re.finditer(r"op\.create_table\(\s*['\"](\w+)['\"]", src):
        end = itf._balanced(src, src.find("(", m.start()) + 1)
        tables.setdefault(m.group(1), []).extend(re.findall(r"Column\(\s*['\"](\w+)['\"]", src[m.start():end]))
    for m in re.finditer(r"op\.add_column\(\s*['\"](\w+)['\"]\s*,\s*sa\.Column\(\s*['\"](\w+)['\"]", src):
        tables.setdefault(m.group(1), []).append(m.group(2))
    return tables


def database(sources: Dict[str, str]) -> Dict[str, Any]:
    sql: Dict[str, Dict[str, Any]] = {}
    orm: Dict[str, Dict[str, Any]] = {}
    migrations: Dict[str, Any] = {"tool": None, "files": [], "tables": {}}
    creates_tables = False
    for rel, src in sorted(sources.items()):
        low = rel.lower()
        in_migrations = bool(re.search(r"(^|/)(migrations|alembic)(/|$)", low))
        if rel.endswith(".sql"):
            parsed = parse_sql(src, rel)
            if in_migrations:
                migrations["tool"] = migrations["tool"] or "sql"
                migrations["files"].append(rel)
                for t, d in parsed.items():
                    migrations["tables"].setdefault(t, []).extend(d["columns"])
            for t, d in parsed.items():
                if t in sql:
                    sql[t]["columns"].update(d["columns"])
                else:
                    sql[t] = d
        elif rel.endswith(".py") and not _is_test(rel):
            if in_migrations and ("op.create_table" in src or "op.add_column" in src):
                migrations["tool"] = "alembic"
                migrations["files"].append(rel)
                for t, cols in parse_alembic(src).items():
                    migrations["tables"].setdefault(t, []).extend(cols)
                continue
            if "__tablename__" in src or "table=True" in src:
                orm.update(parse_orm(src, rel))
            if re.search(r"metadata\.create_all\(|create_db_and_tables|SQLModel\.metadata\.create_all", src):
                creates_tables = True
    if any(rel.endswith("alembic.ini") for rel in sources):
        migrations["tool"] = migrations["tool"] or "alembic"
    return {"sql": sql, "orm": orm, "migrations": migrations, "creates_tables": creates_tables,
            "files": sorted({d["file"] for d in list(sql.values()) + list(orm.values())})}


# --- environment -----------------------------------------------------------------------------------------------------

def environment(sources: Dict[str, str]) -> Dict[str, List[Dict[str, Any]]]:
    out: Dict[str, List[Dict[str, Any]]] = {"backend": [], "frontend": []}
    for rel, src in sources.items():
        if _is_test(rel):
            continue
        if rel.endswith(".py"):
            for m in re.finditer(r"os\.(?:getenv|environ\.get)\(\s*['\"](\w+)['\"]\s*(,)?|os\.environ\[\s*['\"](\w+)['\"]\s*\]", src):
                out["backend"].append({"name": m.group(1) or m.group(3), "file": rel, "line": src[:m.start()].count("\n") + 1,
                                       "has_default": bool(m.group(2))})
        elif rel.endswith(JS):
            for m in re.finditer(r"(?:import\.meta\.env|process\.env)\.(\w+)", src):
                out["frontend"].append({"name": m.group(1), "file": rel, "line": src[:m.start()].count("\n") + 1, "has_default": False})
    return out


# --- snapshot --------------------------------------------------------------------------------------------------------

def fingerprint(be: Dict[str, Any], db: Dict[str, Any]) -> Dict[str, Any]:
    """The comparable summary drift detection diffs: per operation and per table."""
    ops = {}
    for r in be.get("routes", []):
        req = r.get("request_schema") or {}
        res = r.get("response_schema") or {}
        res_obj = res.get("items") if res.get("type") == "array" else res
        ops[f"{r['method']} {itf._norm(r['path'])}"] = {
            "path": r["path"], "auth": r.get("auth"), "status": r.get("status_code"),
            "request": {k: (v or {}).get("type") for k, v in (req.get("properties") or {}).items()},
            "request_required": sorted(req.get("required") or []),
            "response_type": res.get("type"),
            "response": {k: (v or {}).get("type") for k, v in ((res_obj or {}).get("properties") or {}).items()},
            "file": r["file"], "line": r["line"]}
    tables = {}
    for src_name in ("sql", "orm"):
        for t, d in (db.get(src_name) or {}).items():
            tables.setdefault(t, {}).update({c: {"type": v["type"], "nullable": v["nullable"], "references": v.get("references")}
                                            for c, v in d["columns"].items()})
    return {"operations": ops, "tables": tables}


def snapshot(project: Path, sources: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    sources = sources if sources is not None else read_sources(project)
    be, fe, db = backend(sources), frontend(sources), database(sources)
    fp = fingerprint(be, db)
    return {"backend": be, "frontend": fe, "database": db, "environment": environment(sources), "fingerprint": fp,
            "digest": hashlib.sha256(json.dumps(fp, sort_keys=True, default=str).encode()).hexdigest()[:16],
            "files_read": len(sources)}
