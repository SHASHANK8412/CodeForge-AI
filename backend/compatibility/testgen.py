"""
Integration tests generated from the shared contract, and their execution.

generate(contract, snap, stack) writes one pytest module (FastAPI's TestClient against the project's own app, the
project's existing test framework) with, per contract operation:

  endpoint_exists          a route of the app serves the contract's method + path
  valid_request            a request built from the contract's schemas (path parameters from a resource created first
                           when the contract has the collection's POST) gets the contract's success status, and the body
                           validates against the contract's response schema; skipped - not passed - when no resource
                           could be created to read
  missing_required_field   a body without a required field is rejected (400/422), in the contract's error format
  unauthenticated          an operation the contract protects rejects a request without credentials (401/403)

per frontend call the analysis read: frontend_request - the exact method, path and body fields the frontend sends reach
a route and are accepted (not 404/405/422, no server error); and, when the project has a SQL schema: db_schema (it
applies to an isolated SQLite database and has the contract's tables and columns) and db_roundtrip per entity (a row
with the contract's fields is written and read back). Valid requests authenticate through the app's own auth
dependency, overridden with a test principal (the override is stated in the test).

Nothing in the expectations comes from what the implementation does: every expected status and schema is the
contract's. Tests run only through the Execution Guardian's isolated Python runner (Docker sandbox: install with
network, tests with --network none; or the explicit AIFORGE_TEST_SANDBOX=local opt-in) on a working copy that holds
the project's sources and the generated tests (the project's own tests are the Guardian's check, not these).
Each test records its own outcome; a test that did not run is reported as not run, never as passed.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.compatibility import contract as ct
from backend.compatibility.models import GeneratedTest, SharedContract

TEST_DIR = "aice_integration"
TEST_FILE = f"{TEST_DIR}/test_aice_contract.py"
RESULTS_FILE = f"{TEST_DIR}/results.jsonl"

RUNTIME = r'''
import functools
import importlib
import json
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RESULTS = Path(__file__).with_name("results.jsonl")
POSTGRES_ONLY = re.compile(r"CREATE\s+EXTENSION|CREATE\s+TYPE|::|gen_random_uuid|uuid_generate_v4|\bnow\(\)", re.I)


def _record(test_id, status, detail=""):
    try:
        with RESULTS.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"id": test_id, "status": status, "detail": str(detail)[:700]}) + "\n")
    except OSError:
        pass


def recorded(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            fn(*args, **kwargs)
        except pytest.skip.Exception as e:
            _record(fn.__name__, "skipped", e)
            raise
        except AssertionError as e:
            _record(fn.__name__, "failed", e)
            raise
        except Exception as e:  # noqa: BLE001
            _record(fn.__name__, "error", f"{type(e).__name__}: {e}")
            raise
        _record(fn.__name__, "passed")
    return wrapper


class Principal(dict):
    """The test principal the app's auth dependency is overridden with (attribute and key access)."""
    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError:
            raise AttributeError(k) from None


PRINCIPAL = Principal(id=1, user_id=1, sub="aice-contract-test", username="aice", email="aice@example.test",
                      is_active=True, role="user")
_APP = {}


def app():
    if "app" not in _APP and "error" not in _APP:
        for p in (str(ROOT / APP_WORKDIR), str(ROOT)):
            if p not in sys.path:
                sys.path.insert(0, p)
        errors = []
        for mod in APP_MODULES:
            try:
                _APP["app"] = getattr(importlib.import_module(mod), APP_ATTR)
                break
            except Exception as e:  # noqa: BLE001
                errors.append(f"{mod}: {type(e).__name__}: {e}")
        if "app" not in _APP:
            _APP["error"] = "; ".join(errors) or "no module to import"
    if "app" not in _APP:
        raise AssertionError("the backend app could not be imported: " + _APP["error"])
    return _APP["app"]


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    with TestClient(app(), raise_server_exceptions=False) as c:
        yield c


def _auth_overrides(application):
    names, found = set(AUTH_DEPENDENCIES), []

    def walk(dep):
        for d in getattr(dep, "dependencies", []):
            if getattr(d.call, "__name__", None) in names and d.call not in found:
                found.append(d.call)
            walk(d)
    for r in application.routes:
        if hasattr(r, "dependant"):
            walk(r.dependant)
    return {f: (lambda: PRINCIPAL) for f in found}


class authenticated:
    def __init__(self, c):
        self.app = c.app

    def __enter__(self):
        self.saved = dict(self.app.dependency_overrides)
        self.app.dependency_overrides.update(_auth_overrides(self.app))

    def __exit__(self, *exc):
        self.app.dependency_overrides.clear()
        self.app.dependency_overrides.update(self.saved)


def example(schema, name=""):
    if not schema:
        return "example"
    t = schema.get("type")
    if isinstance(t, list):
        t = next((x for x in t if x != "null"), "string")
    if "enum" in schema:
        return schema["enum"][0]
    fmt = schema.get("format")
    if t == "integer":
        return max(1, int(schema.get("minimum", 1)))
    if t == "number":
        return 1.5
    if t == "boolean":
        return True
    if t == "array":
        return [example(schema.get("items"))] if schema.get("items") else []
    if t == "object":
        return {k: example(v, k) for k, v in (schema.get("properties") or {}).items()}
    if fmt == "date-time":
        return "2024-01-01T00:00:00Z"
    if fmt == "date":
        return "2024-01-01"
    if fmt == "uuid":
        return "00000000-0000-4000-8000-000000000001"
    if fmt == "email" or name == "email":
        return "aice@example.test"
    return f"example-{name}" if name else "example"


def _is(v, t):
    return {"integer": isinstance(v, int) and not isinstance(v, bool), "number": isinstance(v, (int, float)) and not isinstance(v, bool),
            "string": isinstance(v, str), "boolean": isinstance(v, bool), "object": isinstance(v, dict),
            "array": isinstance(v, list), "null": v is None}.get(t, True)


def check(value, schema, path="body"):
    """Errors of `value` against a contract schema (types, required, properties, items, date-time format)."""
    if not schema:
        return []
    t = schema.get("type")
    types = t if isinstance(t, list) else ([t] if t else [])
    if types and not any(_is(value, x) for x in types):
        return [f"{path}: expected {types}, got {type(value).__name__}"]
    errs = []
    if isinstance(value, dict):
        errs += [f"{path}.{r}: missing" for r in schema.get("required") or [] if r not in value]
        for k, s in (schema.get("properties") or {}).items():
            if k in value:
                errs += check(value[k], s, f"{path}.{k}")
    if isinstance(value, list) and schema.get("items"):
        for i, v in enumerate(value[:20]):
            errs += check(v, schema["items"], f"{path}[{i}]")
    if schema.get("format") in ("date-time", "date") and isinstance(value, str):
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            errs.append(f"{path}: '{value}' is not an ISO 8601 {schema['format']}")
    return errs


def _json(resp):
    try:
        return resp.json()
    except ValueError:
        return None


def _excerpt(resp):
    return f"{resp.status_code} {resp.text[:300]}"


def route_for(method, path):
    from starlette.routing import Match
    scope = {"type": "http", "method": method, "path": path, "root_path": "", "query_string": b"", "headers": []}
    for r in app().routes:
        if hasattr(r, "matches"):
            m, _ = r.matches(scope)
            if m == Match.FULL:
                return r
    return None


def served():
    return sorted(f"{','.join(sorted(getattr(r, 'methods', None) or []))} {r.path}" for r in app().routes if hasattr(r, "path"))[:40]


def concrete(op, values=None):
    values = values or {}
    return re.sub(r"\{(\w+)\}", lambda m: str(values.get(m.group(1), example((op.get("path_params") or {}).get(m.group(1)) or {"type": "integer"}, m.group(1)))), op["path"])


def created_id(c, op):
    """For GET/PUT/PATCH/DELETE /things/{id}: create one with the contract's POST /things first; its id or None."""
    params = re.findall(r"\{(\w+)\}", op["path"])
    if not params:
        return {}
    parent = op["path"].rsplit("/{", 1)[0]
    post = next((o for o in OPERATIONS if o["method"] == "POST" and o["path"] == parent), None)
    if post is None or post.get("request_unspecified") or re.search(r"\{", parent):
        return None
    with authenticated(c):
        resp = c.post(parent, json=example(post.get("request_schema")) if post.get("request_schema") else None)
    body = _json(resp)
    if resp.status_code >= 300 or not isinstance(body, dict):
        return None
    ident = body.get(params[-1], body.get("id"))
    return {params[-1]: ident} if ident is not None else None


def error_format_errors(resp):
    if not ERROR_FORMAT:
        return []
    return check(_json(resp), ERROR_FORMAT, "error body")


def run_valid_request(c, op):
    if op.get("request_unspecified"):
        pytest.skip("the contract does not state the request body, so a valid request cannot be built from it")
    values = created_id(c, op)
    if values is None:
        values = {}
        no_resource = True
    else:
        no_resource = False
    path = concrete(op, values)
    body = example(op.get("request_schema")) if op.get("request_schema") else None
    with authenticated(c):
        resp = c.request(op["method"], path, json=body)
    assert resp.status_code < 500, f"server error for a valid request: {_excerpt(resp)}"
    assert resp.status_code not in (404, 405) or re.search(r"\{", op["path"]), f"{op['method']} {path} is not served: {_excerpt(resp)}"
    if resp.status_code == 404 and no_resource:
        pytest.skip(f"{path}: no resource could be created first, so the response could not be validated (404)")
    if op["success"]:
        assert str(resp.status_code) in op["success"], f"expected status {op['success']}, got {_excerpt(resp)}"
    else:
        assert 200 <= resp.status_code < 300, f"expected a success status, got {_excerpt(resp)}"
    if op.get("response_schema"):
        errs = check(_json(resp), op["response_schema"])
        assert not errs, f"the response does not match the contract: {errs[:6]}"


def run_missing_field(c, op):
    schema = op["request_schema"]
    body = example(schema)
    missing = (schema.get("required") or [None])[0]
    body.pop(missing, None)
    values = created_id(c, op) or {}
    with authenticated(c):
        resp = c.request(op["method"], concrete(op, values), json=body)
    assert resp.status_code in (400, 422), f"a body without '{missing}' was not rejected: {_excerpt(resp)}"
    errs = error_format_errors(resp)
    assert not errs, f"the error body is not in the contract's error format: {errs[:4]}"


def run_unauthenticated(c, op):
    resp = c.request(op["method"], concrete(op), json=example(op.get("request_schema")) if op.get("request_schema") else None)
    assert resp.status_code in (401, 403), f"a request without credentials was not rejected: {_excerpt(resp)}"
    errs = error_format_errors(resp)
    assert not errs, f"the error body is not in the contract's error format: {errs[:4]}"


def run_frontend_call(c, call):
    path = re.sub(r"\{\}", "1", call["path"])
    assert route_for(call["method"], path) is not None, (
        f"the frontend's {call['method']} {call['path']} ({call['where']}) reaches no route; the app serves {served()}")
    body = {k: example((call.get("field_schemas") or {}).get(k), k) for k in call["body_fields"]} if call["body_fields"] is not None else None
    if call["auth_header"]:
        with authenticated(c):
            resp = c.request(call["method"], path, json=body)
    else:
        resp = c.request(call["method"], path, json=body)
    assert resp.status_code < 500, f"server error for the frontend's request: {_excerpt(resp)}"
    assert resp.status_code != 422, f"the backend rejects the body the frontend sends ({sorted(body or {})}): {_excerpt(resp)}"
    assert resp.status_code != 405, f"the backend does not accept {call['method']} here: {_excerpt(resp)}"


def _schema_sql():
    sql = (ROOT / SCHEMA_SQL).read_text(encoding="utf-8")
    if POSTGRES_ONLY.search(sql):
        pytest.skip("the schema uses PostgreSQL-only syntax and no isolated PostgreSQL is available: not applied")
    con = sqlite3.connect(":memory:")
    con.executescript(sql)
    return con


def _table(con, entity):
    names = {r[0].lower(): r[0] for r in con.execute("select name from sqlite_master where type='table'")}
    for cand in entity["candidates"]:
        if cand.lower() in names:
            return names[cand.lower()]
    return None


def run_db_schema():
    con = _schema_sql()
    problems = []
    for e in ENTITIES:
        t = _table(con, e)
        if t is None:
            problems.append(f"no table for {e['name']}")
            continue
        cols = {r[1] for r in con.execute(f'pragma table_info("{t}")')}
        missing = [f["name"] for f in e["fields"] if f["name"] not in cols]
        if missing:
            problems.append(f"{t} lacks {missing}")
    assert not problems, "; ".join(problems)


def _insert(con, table, seen):
    info = list(con.execute(f'pragma table_info("{table}")'))
    fks = {r[3]: (r[2], r[4]) for r in con.execute(f'pragma foreign_key_list("{table}")')}
    row = {}
    for cid, name, ctype, notnull, default, pk in info:
        if pk and "INT" in (ctype or "").upper():
            continue
        if name in fks:
            parent, col = fks[name]
            if parent not in seen:
                seen.add(parent)
                _insert(con, parent, seen)
            row[name] = con.execute(f'select "{col or "rowid"}" from "{parent}" limit 1').fetchone()[0]
        elif notnull or pk:
            if default is not None:
                continue
            t = (ctype or "").upper()
            row[name] = 1 if any(k in t for k in ("INT", "BOOL")) else 1.5 if any(k in t for k in ("REAL", "FLOA", "DOUB", "NUM", "DEC")) \
                else "2024-01-01T00:00:00Z" if any(k in t for k in ("DATE", "TIME")) else f"aice-{name}"
    cols = ", ".join(f'"{k}"' for k in row)
    if row:
        con.execute(f'insert into "{table}" ({cols}) values ({", ".join("?" for _ in row)})', list(row.values()))
    else:
        con.execute(f'insert into "{table}" default values')
    return row


def run_db_roundtrip(entity):
    con = _schema_sql()
    con.execute("pragma foreign_keys = on")
    t = _table(con, entity)
    assert t is not None, f"no table for {entity['name']}"
    row = _insert(con, t, {t})
    got = con.execute(f'select * from "{t}"').fetchall()
    assert len(got) == 1, f"the row written to {t} was not read back"
    names = [r[1] for r in con.execute(f'pragma table_info("{t}")')]
    stored = dict(zip(names, got[0]))
    assert all(stored[k] == v for k, v in row.items()), f"values changed on the round trip: wrote {row}, read {stored}"
'''


def _safe(s: str) -> str:
    return re.sub(r"\W+", "_", s).strip("_").lower()[:60]


def _entity_candidates(x) -> List[str]:
    out = []
    for n in [x.table, x.name]:
        if n:
            low = re.sub(r"(?<!^)(?=[A-Z])", "_", n).lower()
            out += [n, low, low + "s", low + "es", (low[:-1] + "ies") if low.endswith("y") else low]
    return list(dict.fromkeys(out))


def generate(c: SharedContract, snap: Dict[str, Any], stack: Dict[str, Any]) -> Tuple[List[GeneratedTest], Dict[str, str]]:
    """(the test list, {path: content} to write into the working copy)."""
    tests: List[GeneratedTest] = []
    body: List[str] = []
    ops = []
    for i, e in enumerate(c.api.endpoints):
        ok, schema = ct.success(e)
        key = ct.op_key(e.method, e.path)
        ops.append({"method": e.method.upper(), "path": e.path, "auth": e.auth, "path_params": e.path_params,
                    "request_schema": None if ct.unspecified(c, key, "request_schema") else e.request_schema,
                    "response_schema": None if ct.unspecified(c, key, "response_schema") else schema,
                    "success": [] if ct.unspecified(c, key, "success_status") else ok,
                    "auth_specified": not ct.unspecified(c, key, "auth"),
                    "request_unspecified": e.method.upper() in ("POST", "PUT", "PATCH") and ct.unspecified(c, key, "request_schema")})
        op = ops[-1]
        stem = f"{_safe(e.method + '_' + e.path)}_{i}"

        def add(kind, fn, desc, call):
            tests.append(GeneratedTest(id=fn, kind=kind, target=key, description=desc))
            body.append(f"@recorded\ndef {fn}({'client' if 'client' in call else ''}):\n    {call}\n")
        literal_key = key.replace("{", "{{").replace("}", "}}").replace('"', "'")
        add("endpoint_exists", f"test_exists_{stem}", f"a route serves {key}",
            f"assert route_for({op['method']!r}, concrete(OPERATIONS[{i}])) is not None, "
            f"f\"no route serves {literal_key}; the app serves {{served()}}\"")
        add("valid_request", f"test_valid_request_{stem}",
            f"a request built from the contract gets {', '.join(op['success']) or 'a 2xx status'}"
            + (" and a body matching the response schema" if op["response_schema"] else ""),
            f"run_valid_request(client, OPERATIONS[{i}])")
        if op["request_schema"] and (op["request_schema"].get("required") or []):
            add("missing_required_field", f"test_missing_required_{stem}",
                f"a body without '{op['request_schema']['required'][0]}' is rejected (400/422) in the error format",
                f"run_missing_field(client, OPERATIONS[{i}])")
        if op["auth"] == "bearer" and op["auth_specified"]:
            add("unauthenticated", f"test_unauthenticated_{stem}", "a request without credentials is rejected (401/403)",
                f"run_unauthenticated(client, OPERATIONS[{i}])")
    calls = []
    ops_by_norm = {ct.norm_key(e.method, e.path): e for e in c.api.endpoints}
    for call in (snap.get("frontend") or {}).get("calls", []):
        if not call.get("resolved"):
            continue
        e = ops_by_norm.get(ct.norm_key(call["method"], call["path"]))
        props = ((e.request_schema or {}).get("properties") or {}) if e else {}
        calls.append({"method": call["method"], "path": call["path"], "where": f"{call['file']}:{call['line']}",
                      "body_fields": call["body_fields"], "auth_header": call["auth_header"], "field_schemas": props})
        j = len(calls) - 1
        fn = f"test_frontend_request_{_safe(call['file'].rsplit('/', 1)[-1])}_{call['line']}_{j}"
        tests.append(GeneratedTest(id=fn, kind="frontend_request", target=f"{call['method']} {call['path']} ({call['file']}:{call['line']})",
                                   description="the frontend's exact request reaches a route and is accepted (no 404/405/422, no 5xx)"))
        body.append(f"@recorded\ndef {fn}(client):\n    run_frontend_call(client, FRONTEND_CALLS[{j}])\n")
    sql_files = sorted({d["file"] for d in ((snap.get("database") or {}).get("sql") or {}).values()
                        if not re.search(r"(^|/)(migrations|alembic)/", d["file"])})
    entities = [{"name": x.name, "candidates": _entity_candidates(x), "fields": [f.model_dump() for f in x.fields]}
                for x in c.entities if x.fields]
    if sql_files and entities:
        tests.append(GeneratedTest(id="test_db_schema_applies", kind="db_schema", target=sql_files[0],
                                   description="the SQL schema applies to an isolated SQLite database and has the contract's tables and columns"))
        body.append("@recorded\ndef test_db_schema_applies():\n    run_db_schema()\n")
        for k, x in enumerate(entities):
            fn = f"test_db_roundtrip_{_safe(x['name'])}_{k}"
            tests.append(GeneratedTest(id=fn, kind="db_roundtrip", target=f"entity {x['name']}",
                                       description="a row is written and read back unchanged (foreign keys enforced)"))
            body.append(f"@recorded\ndef {fn}():\n    run_db_roundtrip(ENTITIES[{k}])\n")
    entry = stack.get("fastapi_app") or ""
    workdir, _, module = entry.partition("/")
    mod, _, attr = module.partition(":")
    modules = ([f"{workdir}.{mod}"] if workdir not in ("", ".") else []) + ([mod] if mod else [])
    auth_deps = sorted({d for r in (snap.get("backend") or {}).get("routes", []) for d in r.get("auth_dependencies") or []
                        if d != "Authorization header"})

    def lit(v: Any) -> str:
        return f"json.loads({json.dumps(json.dumps(v, default=str))})"
    header = (f'"""Contract tests generated by AIForge AICE from the shared contract v{c.version} (revision {c.revision}).\n'
              'Expected statuses and schemas are the contract\'s; the app\'s auth dependency is overridden with a test principal\n'
              'for requests the contract makes as an authenticated client. Regenerate instead of editing."""\n')
    consts = (f"APP_WORKDIR = {workdir or '.'!r}\nAPP_MODULES = {modules!r}\nAPP_ATTR = {attr or 'app'!r}\n"
              f"AUTH_DEPENDENCIES = {auth_deps!r}\nOPERATIONS = {lit(ops)}\nFRONTEND_CALLS = {lit(calls)}\n"
              f"ERROR_FORMAT = {lit(c.error_format)}\nENTITIES = {lit(entities)}\nSCHEMA_SQL = {(sql_files[0] if sql_files else None)!r}\n")
    source = header + RUNTIME + "\n\n" + consts + "\n\n" + "\n\n".join(body)
    return tests, {TEST_FILE: source, f"{TEST_DIR}/__init__.py": ""}


def prepare(ws: Path, files: Dict[str, str]) -> List[str]:
    """Make the working copy hold the project's sources and only the generated tests. Returns what was changed in the
    copy (reported; the project itself is never touched)."""
    from backend.compatibility.extract import _is_test
    notes = []
    removed = [p for p in ws.rglob("*") if p.is_file() and _is_test(p.relative_to(ws).as_posix())
               and not p.relative_to(ws).as_posix().startswith(TEST_DIR + "/") and "node_modules" not in p.parts]
    for p in removed:
        p.unlink()
    if removed:
        notes.append(f"the project's own {len(removed)} test file(s) are left out of the copy (the Execution Guardian runs them)")
    for cfg in ("pytest.ini", "tox.ini"):
        if (ws / cfg).is_file():
            (ws / cfg).unlink()
    (ws / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    for rel, content in files.items():
        (ws / rel).parent.mkdir(parents=True, exist_ok=True)
        (ws / rel).write_text(content, encoding="utf-8")
    from backend.execution.project_env import requirements_file
    req = requirements_file(ws)
    if req is not None:
        text = req.read_text(encoding="utf-8", errors="replace")
        if not re.search(r"^\s*httpx\b", text, re.M | re.I):
            req.write_text(text.rstrip("\n") + "\nhttpx\n", encoding="utf-8")
            notes.append(f"httpx (needed by FastAPI's TestClient) is added to {req.relative_to(ws).as_posix()} in the copy")
    return notes


def execute(ws: Path, tests: List[GeneratedTest], timeout: float) -> Tuple[List[GeneratedTest], Dict[str, Any]]:
    """Run the generated tests in the Guardian's isolated Python runner; per-test outcomes from the results file."""
    from backend.execution_guardian import checks as chk
    from backend.execution_guardian.models import Check
    deps = Check(name="python_dependencies", label="Python dependency install")
    run = Check(name="python_tests", label="AICE contract tests")
    (ws / RESULTS_FILE).unlink(missing_ok=True)
    chk.run_python(deps, run, ws, timeout)
    results: Dict[str, Dict[str, str]] = {}
    try:
        for line in (ws / RESULTS_FILE).read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                results[r["id"]] = r
    except (OSError, ValueError):
        results = {}
    # a test whose fixture failed never reached its own recorder: pytest's summary names it
    summary = {m.group(2): m.group(1) for m in re.finditer(r"^(FAILED|ERROR) \S*::(\w+)", run.log_excerpt or "", re.M)}
    out = []
    for t in tests:
        r = results.get(t.id)
        if r:
            out.append(t.model_copy(update={"status": r["status"], "detail": r.get("detail", "")}))
        elif t.id in summary:
            out.append(t.model_copy(update={"status": "error" if summary[t.id] == "ERROR" else "failed",
                                            "detail": "the test could not start (a fixture failed, e.g. the backend app could "
                                                      "not be imported): see the log excerpt"}))
        elif run.status == "PASSED" and not run.counts.get("skipped") and run.counts.get("passed") == len(tests):
            out.append(t.model_copy(update={"status": "passed", "detail": "pytest reported every test passed"}))
        else:
            out.append(t.model_copy(update={"status": "not_run", "detail": run.reason or run.error_summary or "no result recorded"}))
    counts = {s: sum(1 for t in out if t.status == s) for s in ("passed", "failed", "error", "skipped", "not_run")}
    status = ("BLOCKED" if run.status == "BLOCKED" or deps.status in ("FAILED", "BLOCKED") and run.status != "PASSED"
              else "FAILED" if counts["failed"] or counts["error"] or run.status == "FAILED"
              else "PASSED" if counts["passed"] and not counts["not_run"] else "SKIPPED" if not counts["not_run"] else "BLOCKED")
    return out, {"status": status, "environment": run.environment or deps.environment, "counts": counts,
                 "pytest_counts": run.counts, "dependencies": deps.status, "reason": run.reason or deps.reason,
                 "error_summary": run.error_summary or deps.error_summary, "log_excerpt": run.log_excerpt or deps.log_excerpt,
                 "timed_out": run.timed_out}
