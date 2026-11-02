"""
Deterministic compatibility analysis: the shared contract against what the code implements (extract.snapshot).

  api        per contract operation: the backend route (missing endpoint / wrong method / wrong path / request and
             response schemas, required vs optional, types, success status, auth, error bodies, pagination shape,
             timestamp formats); per frontend call: the operation it reaches (method, path, body fields, Authorization
             header, the response fields it reads, list vs envelope)
  database   per contract entity: the persisted schema (SQL DDL / migrations) and the ORM models - missing tables and
             fields, types, nullability, primary-key / identifier formats, relationships; ORM models that differ from
             the SQL schema; models no migration or create_all creates
  drift      against the previous analysis of the same project: implementation changes (an endpoint removed, a field
             renamed, auth added, a column changed) the contract did not make, classified as breaking or backward
             compatible, with the consumers that use them

Every rule is deterministic. A language model is consulted only for one ambiguous case - which contract field a
frontend read most likely means when no name matches - and its answer is labelled (basis "model"), used only for the
recommended fix, and never makes anything pass. Without a contract, frontend calls are matched against the backend
directly; which side is right is then a contract decision (status needs_contract_decision), never guessed.
"""

import difflib
import hashlib
import json
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

from backend.compatibility import contract as ct
from backend.compatibility.models import CompatFinding, SharedContract
from backend.swarm.interfaces import _norm

SEVERITY = {
    "missing_endpoint": "high", "incorrect_http_method": "high", "incorrect_url_path": "high",
    "frontend_call_not_in_contract": "high", "request_field_mismatch": "high", "missing_required_field": "high",
    "optional_field_inconsistency": "medium", "response_field_mismatch": "high", "incorrect_data_type": "high",
    "auth_mismatch": "critical", "error_response_mismatch": "medium", "pagination_mismatch": "high",
    "datetime_format_mismatch": "medium", "incorrect_status_code": "medium", "undeclared_endpoint": "low",
    "unreadable_call": "low", "db_missing_table": "high", "db_missing_field": "high", "db_field_type_mismatch": "high",
    "db_missing_relationship": "medium", "db_identifier_format_mismatch": "high", "db_nullability_mismatch": "medium",
    "db_missing_migration": "high", "db_model_schema_drift": "high", "contract_drift": "high",
    "contract_inconsistency": "medium", "frontend_backend_mismatch": "high", "environment_mismatch": "low",
}
FIX = {
    "missing_endpoint": "implement the operation exactly as the contract defines it",
    "incorrect_http_method": "use the contract's HTTP method",
    "incorrect_url_path": "use the contract's path",
    "frontend_call_not_in_contract": "call an operation the contract defines, or have the architect add it to the contract",
    "request_field_mismatch": "send / accept exactly the contract's request fields",
    "missing_required_field": "make the request carry every field the contract requires",
    "optional_field_inconsistency": "make the field required / optional exactly as the contract says",
    "response_field_mismatch": "return / read exactly the contract's response fields",
    "incorrect_data_type": "use the contract's type for the field",
    "auth_mismatch": "apply the contract's authentication on both sides",
    "error_response_mismatch": "return errors in the contract's error format (FastAPI: HTTPException -> {\"detail\": ...})",
    "pagination_mismatch": "use the contract's list shape (a JSON array, or the envelope it defines)",
    "datetime_format_mismatch": "serialise timestamps in the contract's format",
    "incorrect_status_code": "return the contract's success status code",
    "db_missing_table": "create the table (schema / migration and ORM model)",
    "db_missing_field": "add the column to the schema / migration and the model",
    "db_field_type_mismatch": "use the contract's column type",
    "db_missing_relationship": "add the foreign key the contract defines",
    "db_identifier_format_mismatch": "use one identifier format (the contract's) in the schema, models and paths",
    "db_nullability_mismatch": "make the column NULL / NOT NULL as the contract says",
    "db_missing_migration": "add a migration that creates it (or create the tables at startup)",
    "db_model_schema_drift": "make the ORM model and the persisted schema agree with the contract",
}


def _fid(key: str) -> str:
    return "cf_" + hashlib.sha1(key.encode()).hexdigest()[:10]


def _types(s: Optional[Dict[str, Any]]) -> set:
    t = (s or {}).get("type")
    return (set(t) if isinstance(t, list) else {t}) - {None} if t else set()


def _obj(schema: Optional[Dict[str, Any]]) -> Tuple[Optional[str], Dict[str, Any], set]:
    """(top-level type, the object properties - of the items for an array -, required)."""
    if not schema:
        return None, {}, set()
    t = schema.get("type")
    t = next((x for x in t if x != "null"), None) if isinstance(t, list) else t
    inner = (schema.get("items") or {}) if t == "array" else schema
    return t, dict(inner.get("properties") or {}), set(inner.get("required") or [])


def canon(name: str) -> str:
    return re.sub(r"[_\-]", "", name).lower()


def _segments(path: str) -> List[str]:
    return [s for s in _norm(path).split("/") if s]


def _singular(s: str) -> str:
    return s[:-3] + "y" if s.endswith("ies") else s[:-2] if s.endswith(("ses", "xes")) else s[:-1] if s.endswith("s") else s


def near(path: str, candidates: List[str]) -> Optional[str]:
    """A candidate that is the same path with a prefix added / removed (/api, /api/v1) or one segment singular vs
    plural - the usual way generated components disagree on a URL. None when no candidate is that close."""
    a = _segments(path)
    for c in candidates:
        b = _segments(c)
        if a == b:
            continue
        for x, y in ((a, b), (b, a)):
            if len(x) > len(y) and x[len(x) - len(y):] == y and len(x) - len(y) <= 2 and all(s != "{}" for s in x[:len(x) - len(y)]):
                return c
        if len(a) == len(b) and sum(1 for s, t in zip(a, b) if s != t) == 1:
            s, t = next((s, t) for s, t in zip(a, b) if s != t)
            if "{}" not in (s, t) and _singular(s) == _singular(t):
                return c
    return None


class Analysis:
    def __init__(self, contract: Optional[SharedContract], snap: Dict[str, Any],
                 previous: Optional[Dict[str, Any]] = None, adjudicate: Optional[Callable[[str, str], str]] = None):
        self.c = contract
        self.s = snap
        self.prev = previous                     # {"fingerprint", "contract_revision", "contract_items": [ChangeItem dicts]}
        self.adjudicate = adjudicate
        self.findings: Dict[str, CompatFinding] = {}
        self.coverage: List[Dict[str, str]] = []
        self.routes = (snap.get("backend") or {}).get("routes", [])
        self.calls = (snap.get("frontend") or {}).get("calls", [])
        self.db = snap.get("database") or {}

    # --- helpers ---------------------------------------------------------------------------------------------------

    def add(self, rule: str, target: str, expected: str, actual: str, agent: Optional[str], evidence: Dict[str, Any],
            components: List[str], basis: str = "static", status: Optional[str] = None, severity: Optional[str] = None,
            fix: Optional[str] = None, key_extra: str = "", repairable: Optional[bool] = None, breaking: Optional[bool] = None) -> CompatFinding:
        key = f"{rule}|{target}{'|' + key_extra if key_extra else ''}"
        if status is None:
            status = "open" if agent in ("frontend", "backend", "database") else "needs_contract_decision" if agent == "architect" else "unresolved"
        f = CompatFinding(id=_fid(key), key=key, rule=rule, severity=severity or SEVERITY.get(rule, "medium"), target=target,
                          components=components, expected=expected, actual=actual, evidence=evidence,
                          recommended_fix=fix or FIX.get(rule, "a person reviews the evidence and decides"),
                          responsible_agent=agent, basis=basis, status=status, breaking=breaking,
                          repairable=repairable if repairable is not None else (status == "open" and agent in ("frontend", "backend", "database")))
        self.findings.setdefault(key, f)
        return f

    def cover(self, check: str, status: str, detail: str) -> None:
        self.coverage.append({"check": check, "status": status, "detail": detail})

    def _unspec(self, e, aspect: str) -> bool:
        return bool(self.c) and ct.unspecified(self.c, ct.op_key(e.method, e.path), aspect)

    @staticmethod
    def _where(x: Dict[str, Any]) -> str:
        return f"{x['file']}:{x['line']}"

    # --- run -------------------------------------------------------------------------------------------------------

    def run(self) -> Tuple[List[CompatFinding], List[Dict[str, str]], Dict[str, Any]]:
        be, fe = self.s.get("backend") or {}, self.s.get("frontend") or {}
        components = {
            "backend": {"routes": len(self.routes), "files": be.get("files", []), "python_files": be.get("python_files", 0)},
            "frontend": {"calls": len(self.calls), "unresolved_calls": sum(1 for c in self.calls if not c["resolved"]),
                         "files": fe.get("files", []), "js_files": fe.get("js_files", 0), "proxy_rewrites": fe.get("proxy_rewrites", [])},
            "database": {"sql_tables": sorted(self.db.get("sql", {})), "orm_tables": sorted(self.db.get("orm", {})),
                         "migrations": (self.db.get("migrations") or {}).get("tool"), "files": self.db.get("files", [])},
            "contract": {"version": self.c.version, "revision": self.c.revision, "operations": len(self.c.api.endpoints),
                         "entities": len(self.c.entities)} if self.c else None,
        }
        if self.c is None:
            self.cover("contract", "not_checked", "no shared contract is registered: frontend calls were matched against the backend "
                                                  "directly; which side is right needs a contract")
            self._without_contract()
        else:
            self._api()
            self._frontend()
            self._database()
            self._environment()
            self._contract_consistency()
        self._drift()
        return list(self.findings.values()), self.coverage, components

    # --- API: contract vs backend ----------------------------------------------------------------------------------

    def _api(self) -> None:
        c = self.c
        if not self.routes:
            self.cover("backend routes", "blocked" if c.api.endpoints else "not_checked",
                       "no FastAPI route was found in the backend code" if c.api.endpoints else "the contract defines no operation")
        by_norm = {ct.norm_key(r["method"], r["path"]): r for r in self.routes}
        contract_norm = {ct.norm_key(e.method, e.path) for e in c.api.endpoints}
        for e in c.api.endpoints:
            key = ct.op_key(e.method, e.path)
            r = by_norm.get(ct.norm_key(e.method, e.path))
            if r is None:
                same_path = [x for x in self.routes if _norm(x["path"]) == _norm(e.path)]
                close = near(e.path, [x["path"] for x in self.routes if x["method"] == e.method.upper()])
                if same_path:
                    self.add("incorrect_http_method", key, f"{e.method.upper()} {e.path}",
                             f"the backend serves this path with {', '.join(sorted({x['method'] for x in same_path}))} "
                             f"({self._where(same_path[0])})", "backend", {"routes": [self._where(x) for x in same_path]},
                             ["backend", "frontend"])
                elif close:
                    r2 = next(x for x in self.routes if x["path"] == close and x["method"] == e.method.upper())
                    self.add("incorrect_url_path", key, e.path, f"{r2['method']} {close} ({self._where(r2)})", "backend",
                             {"route": self._where(r2), "route_path": close, "contract_path": e.path}, ["backend", "frontend"])
                else:
                    self.add("missing_endpoint", key, key, "no such route in the backend code", "backend",
                             {"backend_files": (self.s.get("backend") or {}).get("files", [])}, ["backend", "frontend"])
                continue
            self._request(e, key, r)
            self._response(e, key, r)
            self._auth_backend(e, key, r)
            self._errors(e, key, r)
        for r in self.routes:
            nk = ct.norm_key(r["method"], r["path"])
            if nk not in contract_norm and not near(r["path"], [e.path for e in c.api.endpoints if e.method.upper() == r["method"]]):
                self.add("undeclared_endpoint", f"{r['method']} {r['path']}", "operations the contract defines",
                         f"the backend also serves {r['method']} {r['path']} ({self._where(r)})", None, {"route": self._where(r)},
                         ["backend"], status="info", fix="add it to the contract if clients use it; otherwise nothing to do")
        self.cover("API operations vs backend routes", "checked" if self.routes else "blocked",
                   f"{len(c.api.endpoints)} contract operation(s), {len(self.routes)} backend route(s) read from the code")

    def _request(self, e, key: str, r: Dict[str, Any]) -> None:
        if self._unspec(e, "request_schema") or not e.request_schema:
            if e.method.upper() in ("POST", "PUT", "PATCH"):
                self.cover(f"{key} request body", "not_checked", "the contract does not state the request schema")
            return
        _, cp, creq = _obj(e.request_schema)
        rs = r.get("request_schema")
        if not rs:
            self.add("request_field_mismatch", key, f"a JSON body with {sorted(cp)}",
                     f"the handler takes no request model ({self._where(r)}): the body is not read or not validated",
                     "backend", {"route": self._where(r)}, ["backend", "frontend"], key_extra="no_model")
            return
        _, bp, breq = _obj(rs)
        types_known = not self._unspec(e, "field_types")
        for f in sorted(set(cp) - set(bp)):
            self.add("request_field_mismatch", key, f"request field '{f}'" + (" (required)" if f in creq else ""),
                     f"the request model has no '{f}' (fields: {sorted(bp)}; {self._where(r)})", "backend",
                     {"route": self._where(r), "field": f}, ["backend", "frontend"], key_extra=f"missing:{f}")
        for f in sorted(set(bp) - set(cp)):
            if f in breq:
                self.add("missing_required_field", key, f"the contract's request fields {sorted(cp)}",
                         f"the backend requires '{f}', which the contract does not define: conforming clients get 422 ({self._where(r)})",
                         "backend", {"route": self._where(r), "field": f}, ["backend", "frontend"], key_extra=f"extra:{f}")
        for f in sorted(set(cp) & set(bp)):
            if f in creq and f not in breq:
                self.add("optional_field_inconsistency", key, f"'{f}' required", f"optional in the request model ({self._where(r)})",
                         "backend", {"route": self._where(r), "field": f}, ["backend"], key_extra=f.lower(), severity="medium")
            elif f not in creq and f in breq:
                self.add("optional_field_inconsistency", key, f"'{f}' optional",
                         f"required by the request model: clients that omit it get 422 ({self._where(r)})", "backend",
                         {"route": self._where(r), "field": f}, ["backend", "frontend"], key_extra=f.lower(), severity="high")
            if types_known and _types(cp[f]) and _types(bp[f]) and not (_types(cp[f]) & _types(bp[f])):
                self.add("incorrect_data_type", key, f"request.{f}: {sorted(_types(cp[f]))}",
                         f"request.{f}: {sorted(_types(bp[f]))} ({self._where(r)})", "backend",
                         {"route": self._where(r), "field": f}, ["backend", "frontend"], key_extra=f"request:{f}")

    def _response(self, e, key: str, r: Dict[str, Any]) -> None:
        ok, schema = ct.success(e)
        status = r.get("status_code") or 200
        if ok and not self._unspec(e, "success_status") and str(status) not in ok:
            self.add("incorrect_status_code", key, f"status {', '.join(ok)}",
                     f"status {status}{'' if r.get('status_code_explicit') else ' (FastAPI default)'} ({self._where(r)})",
                     "backend", {"route": self._where(r)}, ["backend", "frontend"])
        if self._unspec(e, "response_schema") or not schema:
            self.cover(f"{key} response body", "not_checked", "the contract does not state the response schema")
            return
        rs = r.get("response_schema")
        if not rs:
            self.cover(f"{key} response body", "not_checked",
                       f"no response_model / return annotation ({self._where(r)}): checked only by the generated tests")
            return
        ct_type, cp, creq = _obj(schema)
        bt, bp, _ = _obj(rs)
        if ct_type and bt and ct_type != bt:
            array_side = ct_type == "array" or bt == "array"
            self.add("pagination_mismatch" if array_side else "response_field_mismatch", key,
                     f"a {ct_type} body" + (f" ({self.c.pagination})" if self.c.pagination else ""),
                     f"a {bt} body ({self._where(r)})", "backend", {"route": self._where(r)}, ["backend", "frontend"],
                     key_extra="shape")
            return
        types_known = not self._unspec(e, "field_types")
        for f in sorted(set(cp) - set(bp)):
            self.add("response_field_mismatch", key, f"response field '{f}'" + (" (required)" if f in creq else ""),
                     f"the response model has no '{f}' (fields: {sorted(bp)}; {self._where(r)})", "backend",
                     {"route": self._where(r), "field": f}, ["backend", "frontend"], key_extra=f"missing:{f}")
        for f in sorted(set(cp) & set(bp)):
            ctypes, btypes = _types(cp[f]), _types(bp[f])
            if not (types_known and ctypes and btypes):
                continue
            fmt = (cp[f] or {}).get("format")
            if fmt in ("date-time", "date") and btypes & {"integer", "number"}:
                self.add("datetime_format_mismatch", key, f"response.{f}: ISO 8601 {fmt} string",
                         f"response.{f}: a number (epoch timestamp) ({self._where(r)})", "backend",
                         {"route": self._where(r), "field": f}, ["backend", "frontend"], key_extra=f)
            elif not (ctypes - {"null"}) & (btypes - {"null"}):
                self.add("incorrect_data_type", key, f"response.{f}: {sorted(ctypes)}", f"response.{f}: {sorted(btypes)} ({self._where(r)})",
                         "backend", {"route": self._where(r), "field": f}, ["backend", "frontend"], key_extra=f"response:{f}")
            elif "null" in btypes and "null" not in ctypes and f in creq:
                self.add("optional_field_inconsistency", key, f"response.{f} never null",
                         f"response.{f} may be null ({self._where(r)})", "backend", {"route": self._where(r), "field": f},
                         ["backend", "frontend"], key_extra=f"response:{f}", severity="medium")

    def _auth_backend(self, e, key: str, r: Dict[str, Any]) -> None:
        if self._unspec(e, "auth"):
            if r.get("auth") == "bearer":
                self.cover(f"{key} authentication", "not_checked",
                           "the contract does not say whether it needs authentication; the backend requires it")
            return
        if e.auth == "bearer" and r.get("auth") != "bearer":
            self.add("auth_mismatch", key, "authentication required (bearer token)",
                     f"no authentication dependency on the route ({self._where(r)})", "backend", {"route": self._where(r)},
                     ["backend", "frontend"], key_extra="backend")
        elif e.auth == "none" and r.get("auth") == "bearer":
            self.add("auth_mismatch", key, "no authentication",
                     f"the route requires {', '.join(r.get('auth_dependencies') or ['a token'])}: clients following the "
                     f"contract get 401/403 ({self._where(r)})", "backend", {"route": self._where(r)}, ["backend", "frontend"],
                     key_extra="backend", severity="high")

    def _errors(self, e, key: str, r: Dict[str, Any]) -> None:
        documented = {str(s) for s in list(e.errors) + list(e.responses)}
        undocumented = [s for s in r.get("raises") or [] if str(s) not in documented and s != 422]
        if undocumented and e.errors:
            self.add("error_response_mismatch", key, f"documented errors {sorted(e.errors)}",
                     f"the handler raises {undocumented} ({self._where(r)})", "backend", {"route": self._where(r), "statuses": undocumented},
                     ["backend", "frontend"], key_extra="status", severity="low")

    # --- API: frontend vs contract ---------------------------------------------------------------------------------

    def _frontend(self) -> None:
        c = self.c
        ops = {ct.norm_key(e.method, e.path): e for e in c.api.endpoints}
        if not self.calls:
            self.cover("frontend calls", "not_checked", "no fetch / axios call was found in the frontend code")
        backend_norm = {ct.norm_key(r["method"], r["path"]) for r in self.routes}
        for call in self.calls:
            where = self._where(call)
            if not call["resolved"]:
                self.add("unreadable_call", where, "a URL that can be read", "the URL is built dynamically",
                         None, {"call": where, "url": call["url_expr"]}, ["frontend"], status="info",
                         fix="build the URL from the contract's path (a literal or a template string)")
                continue
            nk = ct.norm_key(call["method"], call["path"])
            e = ops.get(nk)
            ev = {"call": where, "url": call["url_expr"], "client": call["client"],
                  **({"browser_path": call["browser_path"]} if call.get("browser_path") else {})}
            if e is None:
                same_path = [x for x in c.api.endpoints if _norm(x.path) == _norm(call["path"])]
                close = near(call["path"], [x.path for x in c.api.endpoints if x.method.upper() == call["method"]])
                if nk in backend_norm:
                    # both components agree on an operation the contract lacks: a contract decision, never a repair
                    self.add("frontend_call_not_in_contract", f"{call['method']} {call['path']}", "operations the contract defines",
                             f"the frontend calls {call['method']} {call['path']} ({where}); the backend implements it too",
                             "architect", ev, ["frontend", "backend"], key_extra=where)
                elif same_path:
                    self.add("incorrect_http_method", f"{call['method']} {call['path']}",
                             f"{', '.join(sorted(x.method.upper() for x in same_path))} {same_path[0].path}",
                             f"the frontend sends {call['method']} ({where})", "frontend",
                             {**ev, "contract_methods": sorted(x.method.upper() for x in same_path), "contract_path": same_path[0].path},
                             ["frontend"], key_extra=where)
                elif close:
                    self.add("incorrect_url_path", f"{call['method']} {call['path']}", close, f"the frontend calls {call['path']} ({where})",
                             "frontend", {**ev, "contract_path": close, "called_path": call["path"]}, ["frontend"], key_extra=where)
                    # the operation the call evidently means: its body, auth and reads are checked against it too
                    meant = next(x for x in c.api.endpoints if x.path == close and x.method.upper() == call["method"])
                    mkey = ct.op_key(meant.method, meant.path)
                    self._call_body(meant, mkey, call, ev)
                    self._call_auth(meant, mkey, call, ev)
                    self._call_reads(meant, mkey, call, ev)
                else:
                    self.add("frontend_call_not_in_contract", f"{call['method']} {call['path']}", "operations the contract defines",
                             f"the frontend calls {call['method']} {call['path']} ({where}); the backend does not implement it",
                             "frontend", ev, ["frontend"], key_extra=where)
                continue
            key = ct.op_key(e.method, e.path)
            self._call_body(e, key, call, ev)
            self._call_auth(e, key, call, ev)
            self._call_reads(e, key, call, ev)
        self.cover("frontend calls vs contract", "checked" if self.calls else "not_checked",
                   f"{len(self.calls)} call(s) read (fetch / axios), {sum(1 for x in self.calls if not x['resolved'])} with a dynamic URL")

    def _call_body(self, e, key, call, ev) -> None:
        if call["body_fields"] is None:
            if e.request_schema and call["method"] in ("POST", "PUT", "PATCH"):
                self.cover(f"{key} request body ({self._where(call)})", "not_checked",
                           "the body is built from a variable: its fields cannot be read statically")
            return
        if not e.request_schema or self._unspec(e, "request_schema"):
            return
        _, cp, creq = _obj(e.request_schema)
        sent = set(call["body_fields"])
        unknown = sorted(sent - set(cp))
        missing = sorted(creq - sent)
        if unknown:
            self.add("request_field_mismatch", key, f"request fields {sorted(cp)}",
                     f"the frontend sends {unknown}, which the contract does not define ({self._where(call)})", "frontend",
                     {**ev, "sent": sorted(sent), "unknown": unknown}, ["frontend"], key_extra=f"{self._where(call)}:unknown")
        if missing:
            self.add("missing_required_field", key, f"required fields {sorted(creq)}",
                     f"the frontend omits {missing} ({self._where(call)})", "frontend", {**ev, "sent": sorted(sent), "missing": missing},
                     ["frontend"], key_extra=f"{self._where(call)}:missing")

    def _call_auth(self, e, key, call, ev) -> None:
        if self._unspec(e, "auth"):
            return
        if e.auth == "bearer" and not call["auth_header"]:
            self.add("auth_mismatch", key, "an Authorization: Bearer header",
                     f"the call sends no Authorization header ({self._where(call)})", "frontend", ev, ["frontend"],
                     key_extra=f"frontend:{self._where(call)}", severity="high")

    def _call_reads(self, e, key, call, ev) -> None:
        reads = call.get("reads") or {}
        if not reads.get("found"):
            return
        _, schema = ct.success(e)
        if not schema or self._unspec(e, "response_schema"):
            return
        ctype, cp, _ = _obj(schema)
        if reads.get("array") is True and ctype == "object":
            self.add("pagination_mismatch", key, f"an object body ({sorted(cp)})", f"the frontend treats the body as a list ({self._where(call)})",
                     "frontend", {**ev, "reads": reads}, ["frontend"], basis="static_heuristic", key_extra=self._where(call))
            return
        if reads.get("array") is False and reads.get("envelope") and ctype == "array":
            self.add("pagination_mismatch", key, "a JSON array", f"the frontend reads {reads['envelope']} from an envelope ({self._where(call)})",
                     "frontend", {**ev, "reads": reads}, ["frontend"], basis="static_heuristic", key_extra=self._where(call))
            return
        read = set(reads.get("item_fields") or []) | (set(reads.get("top_fields") or []) if ctype != "array" else set())
        unknown = sorted(read - set(cp))
        unread = sorted(set(cp) - read)
        for f in unknown:
            candidate, how = self._candidate(f, unread, key)
            fix = (f"read '{candidate}' instead of '{f}' ({how})" if candidate else
                   f"read only fields the contract returns: {sorted(cp)}")
            self.add("response_field_mismatch", key, f"response fields {sorted(cp)}",
                     f"the frontend reads '{f}', which the contract's response does not have ({self._where(call)})", "frontend",
                     {**ev, "field": f, "candidates": unread, **({"likely": candidate, "likely_by": how} if candidate else {})},
                     ["frontend"], basis="static_heuristic", key_extra=f"{self._where(call)}:{f}", fix=fix,
                     repairable=True)

    def _candidate(self, f: str, unread: List[str], key: str) -> Tuple[Optional[str], str]:
        """Which contract field a frontend read means: same name in another convention (taskName / task_name) or a
        near-identical name decide it; otherwise the model is asked (advisory, labelled); otherwise nothing."""
        for u in unread:
            if canon(u) == canon(f):
                return u, "same name in another naming convention"
        close = [u for u in unread if difflib.SequenceMatcher(None, canon(u), canon(f)).ratio() >= 0.8]
        if len(close) == 1:
            return close[0], "near-identical name"
        if not unread or self.adjudicate is None:
            return None, ""
        prompt = (f"A frontend reads the field '{f}' from the response of {key}. The contract's response has these fields the "
                  f"frontend does not read: {unread}. Which one does '{f}' most likely mean? Answer with JSON only: "
                  '{"field": "<one of the listed names, or none>", "reason": "<short>"}')
        try:
            reply = self.adjudicate("You compare API field names. Answer only with the requested JSON.", prompt)
            m = re.search(r"\{[^{}]*\}", reply or "")
            pick = json.loads(m.group(0)).get("field") if m else None
        except Exception:  # noqa: BLE001 - the model is advisory: no answer leaves the finding unresolved
            return None, ""
        return (pick, "model suggestion (advisory)") if pick in unread else (None, "")

    # --- without a contract ----------------------------------------------------------------------------------------

    def _without_contract(self) -> None:
        from backend.swarm.interfaces import match
        if not self.routes or not self.calls:
            self.cover("frontend calls vs backend routes", "not_checked",
                       "no backend route" if not self.routes else "no frontend call" + " was found")
            return
        for m in match([c for c in self.calls], self.routes):
            if m["status"] != "mismatch":
                continue
            close = near(m["path"], [r["path"] for r in self.routes if r["method"] == m["method"]]) if m.get("path") else None
            self.add("frontend_backend_mismatch", f"{m['method']} {m['path']}", "a backend route the call reaches",
                     f"{m['reason']}" + (f" (the backend has {close})" if close else "") + f" ({self._where(m)})", "architect",
                     {"call": self._where(m), **({"backend_path": close} if close else {})}, ["frontend", "backend"],
                     key_extra=self._where(m), fix="register a shared contract that decides the operation; then the side that "
                                                  "departs from it is repaired")
        self.cover("frontend calls vs backend routes", "checked", f"{len(self.calls)} call(s) against {len(self.routes)} route(s)")

    # --- database --------------------------------------------------------------------------------------------------

    @staticmethod
    def _table(entity, tables: Dict[str, Any]) -> Optional[str]:
        names = [entity.table, entity.name] if entity.table else [entity.name]
        cands = []
        for n in [x for x in names if x]:
            low = re.sub(r"(?<!^)(?=[A-Z])", "_", n).lower()
            cands += [n, n.lower(), low, low + "s", low + "es", low[:-1] + "ies" if low.endswith("y") else low, _singular(low)]
        lower = {t.lower(): t for t in tables}
        return next((lower[c.lower()] for c in cands if c and c.lower() in lower), None)

    def _database(self) -> None:
        c = self.c
        sql, orm = self.db.get("sql") or {}, self.db.get("orm") or {}
        mig = self.db.get("migrations") or {}
        if not c.entities:
            self.cover("database entities", "not_applicable", "the contract defines no entity")
        elif not sql and not orm:
            for x in c.entities:
                self.add("db_missing_table", f"entity {x.name}", f"a table / model for {x.name}",
                         "no SQL schema, migration or ORM model was found", "database", {}, ["database", "backend"])
            self.cover("database entities", "checked", "no persisted schema or ORM model exists")
        else:
            for x in c.entities:
                for source, tables, comp in (("schema", sql, "database"), ("model", orm, "database")):
                    if not tables:
                        continue
                    t = self._table(x, tables)
                    if t is None:
                        self.add("db_missing_table", f"entity {x.name}", f"a {'table' if source == 'schema' else 'model'} for {x.name}",
                                 f"none among the {source}s: {sorted(tables)}", comp, {"source": source, "tables": sorted(tables)},
                                 ["database", "backend"], key_extra=source)
                        continue
                    self._entity_vs(x, t, tables[t], source)
            self.cover("database entities vs schema / models", "checked",
                       f"{len(c.entities)} entit(y/ies) against {len(sql)} SQL table(s) and {len(orm)} ORM model(s)")
        # ORM models vs the persisted schema (what the code expects vs what is stored)
        if sql and orm:
            for t, d in orm.items():
                st = next((s for s in sql if s.lower() == t.lower()), None)
                if st is None:
                    continue
                for col, spec in d["columns"].items():
                    sc = sql[st]["columns"].get(col)
                    if sc is None:
                        self.add("db_model_schema_drift", f"table {t}.{col}", f"the persisted schema has {t}.{col}",
                                 f"the model {d.get('class')} ({d['file']}:{d['line']}) has '{col}'; {sql[st]['file']} does not",
                                 "database", {"model": f"{d['file']}:{d['line']}", "schema": sql[st]["file"]}, ["database", "backend"])
                    elif "unknown" not in (spec["type"], sc["type"]) and spec["type"] != sc["type"]:
                        self.add("db_model_schema_drift", f"table {t}.{col}", f"{sql[st]['file']}: {sc['type']}",
                                 f"model {d.get('class')}: {spec['type']} ({d['file']}:{d['line']})", "database",
                                 {"model": f"{d['file']}:{d['line']}", "schema": sql[st]["file"]}, ["database", "backend"], key_extra="type")
        # migrations: ORM models need something that creates their tables
        if orm:
            if mig.get("tool") == "alembic" and mig.get("files"):
                for t, d in orm.items():
                    cols = set(mig["tables"].get(t) or [])
                    if t not in mig["tables"]:
                        self.add("db_missing_migration", f"table {t}", f"a migration that creates {t}",
                                 f"no migration in {mig['files']} creates it (model {d['file']}:{d['line']})", "database",
                                 {"migrations": mig["files"], "model": f"{d['file']}:{d['line']}"}, ["database"])
                    else:
                        for col in sorted(set(d["columns"]) - cols):
                            self.add("db_missing_migration", f"table {t}.{col}", f"a migration that adds {t}.{col}",
                                     f"the migrations create {t} without '{col}'", "database", {"migrations": mig["files"]},
                                     ["database"], key_extra=col)
                self.cover("migrations", "checked", f"{len(mig['files'])} migration file(s) read")
            elif not self.db.get("creates_tables") and not sql:
                self.add("db_missing_migration", "ORM models", "migrations, a schema, or metadata.create_all",
                         f"models {sorted(orm)} exist but nothing creates their tables", "database",
                         {"models": [f"{d['file']}:{d['line']}" for d in orm.values()]}, ["database", "backend"])
        if sql:
            self.cover("migration in an isolated database", "not_checked",
                       "applied by the generated tests (SQLite in memory) when tests run; analysis alone does not execute it")
        # identifier formats: contract path parameters vs the entity's primary key
        pk = {x.name.lower(): next((f for f in x.fields if f.primary_key), None) for x in c.entities}
        for e in c.api.endpoints:
            for name in re.findall(r"\{(\w+)\}", e.path):
                ent = name[:-3] if name.endswith("_id") else _singular(_segments(e.path)[_segments(e.path).index("{}") - 1]) \
                    if "{}" in _segments(e.path) and _segments(e.path).index("{}") > 0 else None
                f = pk.get((ent or "").lower()) or pk.get(_singular((ent or "").lower()))
                if not f or f.type == "unknown":
                    continue
                r = next((x for x in self.routes if ct.norm_key(x["method"], x["path"]) == ct.norm_key(e.method, e.path)), None)
                ptype = ((r or {}).get("path_param_schemas") or {}).get(name, {}).get("type")
                want = "string" if f.format == "uuid" else f.type
                if ptype and ptype != want:
                    self.add("db_identifier_format_mismatch", f"{ct.op_key(e.method, e.path)} {{{name}}}",
                             f"{want} (the primary key {ent}.{f.name}{' is a UUID' if f.format == 'uuid' else ''})",
                             f"the route declares {name}: {ptype} ({self._where(r)})", "backend", {"route": self._where(r)},
                             ["backend", "frontend", "database"])

    def _entity_vs(self, x, table: str, d: Dict[str, Any], source: str) -> None:
        cols = d["columns"]
        loc = f"{d['file']}:{d.get('line', 1)}"
        known = {canon(f.name) for f in x.fields}
        if x.fields:
            for col, spec in cols.items():
                if canon(col) not in known and not spec.get("nullable") and not spec.get("default") and not spec.get("primary_key"):
                    self.add("db_extra_required_column", f"entity {x.name}.{col}", f"only the contract's fields {sorted(f.name for f in x.fields)}",
                             f"{source} {table} has '{col}' NOT NULL without a default: records created from the contract's "
                             f"fields are rejected ({loc})", "database", {"source": source, "table": table, "file": d["file"], "column": col},
                             ["database", "backend"], key_extra=source, severity="medium",
                             fix="drop the column, make it nullable / give it a default, or have the architect add it to the contract")
        for f in x.fields:
            col = cols.get(f.name) or next((v for k, v in cols.items() if canon(k) == canon(f.name)), None)
            target = f"entity {x.name}.{f.name}"
            if col is None:
                self.add("db_missing_field", target, f"column '{f.name}' ({f.type})", f"{source} {table} has {sorted(cols)} ({loc})",
                         "database", {"source": source, "table": table, "file": d["file"]}, ["database", "backend"], key_extra=source)
                continue
            want_fmt = f.format
            if f.type != "unknown" and col["type"] != "unknown":
                id_like = f.primary_key or f.format == "uuid" or (f.references is not None)
                if col["type"] != f.type or (want_fmt in ("date-time", "date") and col.get("format") not in (want_fmt, None)
                                             and col.get("format") != want_fmt):
                    self.add("db_identifier_format_mismatch" if id_like else "db_field_type_mismatch", target,
                             f"{f.type}{'/' + want_fmt if want_fmt else ''}",
                             f"{col['type']}{'/' + col['format'] if col.get('format') else ''} in {source} {table} ({loc})",
                             "database", {"source": source, "table": table, "file": d["file"], "column": f.name},
                             ["database", "backend", "frontend"], key_extra=source)
            if f.primary_key and not col.get("primary_key"):
                self.add("db_identifier_format_mismatch", target, "the primary key", f"not a primary key in {source} {table} ({loc})",
                         "database", {"source": source, "table": table, "file": d["file"]}, ["database", "backend"], key_extra=f"{source}:pk")
            want_null = f.nullable or not f.required
            if not f.primary_key and bool(col.get("nullable")) != want_null:
                self.add("db_nullability_mismatch", target, "nullable" if want_null else "NOT NULL",
                         ("nullable" if col.get("nullable") else "NOT NULL") + f" in {source} {table} ({loc})", "database",
                         {"source": source, "table": table, "file": d["file"], "column": f.name}, ["database", "backend"], key_extra=source)
            if f.references and not col.get("references"):
                self.add("db_missing_relationship", target, f"a foreign key to {f.references}",
                         f"no foreign key in {source} {table} ({loc})", "database",
                         {"source": source, "table": table, "file": d["file"], "column": f.name, "references": f.references},
                         ["database", "backend"], key_extra=source)

    # --- environment / contract consistency ------------------------------------------------------------------------

    def _environment(self) -> None:
        env = self.s.get("environment") or {}
        read = {(comp, v["name"]) for comp, vs in env.items() for v in vs}
        if not self.c.environment:
            self.cover("environment configuration", "not_checked", "the contract does not list environment variables")
            return
        for v in self.c.environment:
            if v.required and (v.component, v.name) not in read and v.component in ("backend", "frontend"):
                self.add("environment_mismatch", f"env {v.name}", f"{v.component} reads {v.name}",
                         f"no {v.component} code reads it", v.component, {"read": sorted(n for c_, n in read if c_ == v.component)},
                         [v.component], severity="low")
        self.cover("environment configuration", "checked", f"{len(self.c.environment)} variable(s) in the contract")

    def _contract_consistency(self) -> None:
        """Contradictions inside the contract itself go to the architect (never repaired by changing code)."""
        names = {x.name.lower(): x for x in self.c.entities}
        for e in self.c.api.endpoints:
            for name, s in e.path_params.items():
                ent = names.get(name[:-3]) if name.endswith("_id") else None
                f = next((x for x in (ent.fields if ent else []) if x.primary_key), None)
                want = ("string" if f.format == "uuid" else f.type) if f else None
                if f and want != "unknown" and _types(s) and want not in _types(s):
                    self.add("contract_inconsistency", f"{ct.op_key(e.method, e.path)} {{{name}}}",
                             f"the type of {ent.name}.{f.name} ({want})", f"the contract declares {name}: {sorted(_types(s))}",
                             "architect", {}, ["architect"], fix="correct the contract (a new version with a reason)")

    # --- drift -----------------------------------------------------------------------------------------------------

    def _drift(self) -> None:
        if not self.prev or not self.prev.get("fingerprint"):
            self.cover("contract drift", "not_applicable", "no earlier analysis of this project to compare with")
            return
        old, new = self.prev["fingerprint"], self.s.get("fingerprint") or {}
        contract_changed = {i.get("target", "") for i in self.prev.get("contract_items") or []}

        def explained(target: str) -> bool:
            return any(target.startswith(t) or t.startswith(target) for t in contract_changed)

        def consumers(op: str) -> List[str]:
            m, _, p = op.partition(" ")
            return [self._where(c) for c in self.calls if c.get("path") and ct.norm_key(c["method"], c["path"]) == f"{m} {p}"]
        oo, no = old.get("operations") or {}, new.get("operations") or {}
        open_targets = [f.target for f in self.findings.values() if f.status in ("open", "unresolved", "needs_contract_decision")]
        contract_ops = {ct.norm_key(e.method, e.path) for e in self.c.api.endpoints} if self.c else set()

        def conforms(target: str) -> bool:
            """The changed element is defined by the contract and nothing about it departs from the contract now: the
            change brought the implementation into line with the contract (e.g. a repair) - not drift away from it."""
            if not self.c:
                return False
            m = re.match(r"^(GET|POST|PUT|PATCH|DELETE) (\S+)", target)
            if m:
                k = ct.norm_key(m.group(1), m.group(2))
                return k in contract_ops and not any(_op_key(t) == k for t in open_targets)
            m = re.match(r"^table (\w+)", target)
            if m:
                ent = next((x for x in self.c.entities if self._table(x, {m.group(1): {}})), None)
                return ent is not None and not any(t.startswith(f"entity {ent.name}") or t.startswith(f"table {m.group(1)}")
                                                   for t in open_targets)
            return False

        def add(target, before, after, breaking, why, comps, code):
            if explained(target) or conforms(target):
                return
            self.add("contract_drift", target, f"as at the last analysis: {before}", f"now: {after}", None,
                     {"consumers": code, "why": why}, comps, status="open" if breaking else "info",
                     severity="high" if breaking else "low", breaking=breaking, key_extra=str(after)[:80],
                     fix=("revert the implementation change, or register a new contract version (with a reason) after "
                          "checking the requirements and the consumers listed" if breaking else
                          "backward compatible: record it in the contract when it is intended"), repairable=False)
        for op in sorted(set(oo) - set(no)):
            add(f"{op.split(' ')[0]} {oo[op]['path']}", "implemented", "removed", True, "clients calling it get 404/405",
                ["backend", "frontend"], consumers(op))
        for op in sorted(set(no) - set(oo)):
            add(f"{op.split(' ')[0]} {no[op]['path']}", "absent", "added", False, "existing clients are unaffected", ["backend"], [])
        for op in sorted(set(oo) & set(no)):
            a, b = oo[op], no[op]
            t = f"{op.split(' ')[0]} {b['path']}"
            if a.get("auth") != b.get("auth"):
                add(t, f"auth {a.get('auth')}", f"auth {b.get('auth')}", b.get("auth") == "bearer",
                    "clients without a token are now rejected" if b.get("auth") == "bearer" else "requests no longer need a token",
                    ["backend", "frontend"], consumers(op))
            if a.get("status") != b.get("status"):
                add(t, f"status {a.get('status')}", f"status {b.get('status')}", True, "clients checking the status break",
                    ["backend", "frontend"], consumers(op))
            for side in ("request", "response"):
                ra, rb = a.get(side) or {}, b.get(side) or {}
                removed, added = sorted(set(ra) - set(rb)), sorted(set(rb) - set(ra))
                renamed = list(zip(removed, added)) if len(removed) == len(added) == 1 else []
                for x, y in renamed:
                    add(f"{t} {side}.{x}", f"{side} field '{x}'", f"renamed to '{y}'", True, "consumers use the old name",
                        ["backend", "frontend"], consumers(op))
                for x in [r for r in removed if not renamed]:
                    add(f"{t} {side}.{x}", f"{side} field '{x}'", "removed", side == "response" or x in (a.get("request_required") or []),
                        "consumers read / send it", ["backend", "frontend"], consumers(op))
                for y in [n for n in added if not renamed]:
                    newly_required = side == "request" and y in (b.get("request_required") or [])
                    add(f"{t} {side}.{y}", "absent", f"{side} field '{y}' added" + (" (required)" if newly_required else ""),
                        newly_required, "existing clients do not send it" if newly_required else "consumers ignore it",
                        ["backend", "frontend"], consumers(op))
                for x in sorted(set(ra) & set(rb)):
                    if ra[x] and rb[x] and ra[x] != rb[x]:
                        add(f"{t} {side}.{x}", f"{side}.{x}: {ra[x]}", f"{side}.{x}: {rb[x]}", True, "consumers handle the old type",
                            ["backend", "frontend"], consumers(op))
            if a.get("response_type") and b.get("response_type") and a["response_type"] != b["response_type"]:
                add(f"{t} response", f"a {a['response_type']} body", f"a {b['response_type']} body", True,
                    "clients parse the old shape", ["backend", "frontend"], consumers(op))
        ot, nt = old.get("tables") or {}, new.get("tables") or {}
        for t in sorted(set(ot) - set(nt)):
            add(f"table {t}", "present", "removed", True, "stored data and the code using it break", ["database", "backend"], [])
        for t in sorted(set(ot) & set(nt)):
            for col in sorted(set(ot[t]) - set(nt[t])):
                add(f"table {t}.{col}", "present", "removed", True, "stored values and readers break", ["database", "backend"], [])
            for col in sorted(set(nt[t]) - set(ot[t])):
                strict = nt[t][col].get("nullable") is False
                add(f"table {t}.{col}", "absent", "added" + (" NOT NULL" if strict else ""), strict,
                    "existing rows have no value" if strict else "nullable: existing rows stay valid", ["database", "backend"], [])
            for col in sorted(set(ot[t]) & set(nt[t])):
                if ot[t][col] != nt[t][col]:
                    add(f"table {t}.{col}", ot[t][col], nt[t][col], True, "stored values / readers have the old definition",
                        ["database", "backend"], [])
        self.cover("contract drift", "checked", "implementation compared with the previous analysis")


def _op_key(target: str) -> Optional[str]:
    m = re.match(r"^(GET|POST|PUT|PATCH|DELETE) (\S+)", target)
    return ct.norm_key(m.group(1), m.group(2)) if m else None


def analyze(contract: Optional[SharedContract], snap: Dict[str, Any], previous: Optional[Dict[str, Any]] = None,
            adjudicate: Optional[Callable[[str, str], str]] = None):
    return Analysis(contract, snap, previous, adjudicate).run()
