"""
The shared contract: derived from the architect's output (the contract the code agents already build from - routes,
models and the Database Schema section, see services/validator.py), validated, diffed between versions and sliced for
each agent.

  derive(project_id, arch, plan)   API operations ("METHOD /path" lines or structured `apis`), entities with the fields
                                   and types the Database Schema section states, per-operation auth when the API line
                                   says so; everything else is recorded in `unspecified` (never assumed)
  validate(contract)               structural errors (rejected) and warnings (kept, reported)
  diff(old, new, implementation)   ChangeItems: what changed, whether it breaks consumers and why, which components
                                   (and, from the last analysis, which code) it affects
  slice_for(contract, agent)       the part of the contract the frontend, backend or database agent implements
  render(slice)                    the slice as a prompt section
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from backend.compatibility.models import FIELD_FORMATS, FIELD_TYPES, ChangeItem, Entity, EntityField, SharedContract
from backend.swarm.interfaces import _norm
from backend.swarm.models import Contract, Endpoint

HTTP_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")
WILDCARD = "2xx"                                  # "some success status": the source did not say which
_ROUTE = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE)\s+`?(/[A-Za-z0-9_\-/{}:.]*)`?(.*)$", re.M)
_AUTH_YES = re.compile(r"\b(auth(?:enticated|orization|-required)?|protected|requires? (?:a )?(?:login|token)|bearer|jwt)\b|🔒", re.I)
_AUTH_NO = re.compile(r"\b(public|no auth|unauthenticated|anonymous)\b", re.I)
_ENV_NAME = re.compile(r"^[A-Z][A-Z0-9_]{1,80}$")
TYPE_WORDS = {"int": "integer", "integer": "integer", "bigint": "integer", "serial": "integer", "smallint": "integer",
              "str": "string", "string": "string", "text": "string", "varchar": "string", "char": "string",
              "bool": "boolean", "boolean": "boolean", "float": "number", "double": "number", "decimal": "number",
              "number": "number", "numeric": "number", "real": "number", "datetime": "string", "timestamp": "string",
              "date": "string", "uuid": "string", "email": "string", "json": "object", "jsonb": "object", "dict": "object",
              "object": "object", "list": "array", "array": "array"}
FORMAT_WORDS = {"datetime": "date-time", "timestamp": "date-time", "date": "date", "uuid": "uuid", "email": "email"}


def op_key(method: str, path: str) -> str:
    return f"{method.upper()} {path}"


def norm_key(method: str, path: str) -> str:
    return f"{method.upper()} {_norm(path)}"


def success(e: Endpoint) -> Tuple[List[str], Optional[Dict[str, Any]]]:
    """(the success statuses the contract states, excluding the wildcard; the success body schema or None)."""
    ok = sorted(k for k in (e.responses or {}) if str(k).startswith("2"))
    schema = next(((e.responses[k] or {}).get("schema") for k in ok if (e.responses[k] or {}).get("schema")), None)
    return [k for k in ok if k != WILDCARD], schema


def unspecified(c: SharedContract, key: str, aspect: str) -> bool:
    return aspect in (c.unspecified.get(key) or []) or aspect in (c.unspecified.get("contract") or [])


# --- derivation ------------------------------------------------------------------------------------------------------

def _split_top(text: str) -> List[str]:
    parts, depth, cur = [], 0, ""
    for ch in text:
        depth += {"(": 1, "[": 1, ")": -1, "]": -1}.get(ch, 0)
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    return [p.strip() for p in parts + [cur] if p.strip()]


def _field(spec: str) -> Optional[EntityField]:
    """'id (int, PK)' / 'user_id (int, FK -> users.id)' / 'title: str' / 'due_at (datetime, optional)'."""
    m = re.match(r"^`?\**([A-Za-z_][A-Za-z0-9_]*)\**`?\s*(?:\(([^)]*)\)|:\s*(.+))?\s*$", spec.strip())
    if not m:
        return None
    words = [w.strip().lower() for w in re.split(r"[,;]\s*", (m.group(2) or m.group(3) or "").strip()) if w.strip()]
    first = re.sub(r"\(.*", "", words[0]).strip() if words else ""
    ftype = TYPE_WORDS.get(first.split()[0] if first else "", "unknown")
    flags = " ".join(words)
    ref = re.search(r"(?:fk|references?|->|→)\s*(?:->\s*)?`?([A-Za-z_]\w*)\.([A-Za-z_]\w*)", flags)
    pk = bool(re.search(r"\b(pk|primary key|primary)\b", flags))
    optional = bool(re.search(r"\b(optional|nullable|null)\b", flags)) and "not null" not in flags
    return EntityField(name=m.group(1), type=ftype, format=FORMAT_WORDS.get(first.split()[0] if first else ""),
                       required=pk or not optional, nullable=optional and not pk, primary_key=pk,
                       references=f"{ref.group(1)}.{ref.group(2)}" if ref else None)


def entities_from_schema(schema_text: str, names: List[str]) -> Tuple[List[Entity], List[str]]:
    """Entities with fields from `- **table**: f (type), ...` lines (or a `### table` heading with field bullets).
    Returns (entities, names whose fields the text does not state)."""
    out: Dict[str, Entity] = {}
    current = None
    for raw in schema_text.splitlines():
        line = raw.rstrip()
        head = re.match(r"^\s{0,3}#{3,6}\s+`?([A-Za-z_]\w*)`?\s*$", line)
        top = re.match(r"^\s{0,3}(?:[-*+]|\d+\.)\s+(?:\*\*|`)?([A-Za-z_]\w*)(?:\*\*|`)?\s*(?::|—|–|-)\s*(.*)$", line)
        sub = re.match(r"^\s{2,}(?:[-*+])\s+(.+)$", line)
        if head:
            current = out.setdefault(head.group(1), Entity(name=head.group(1), table=head.group(1)))
        elif top and not line.startswith((" ", "\t")) and top.group(1).lower() not in ("id", "pk", "fk", "relationships", "indexes", "note"):
            current = out.setdefault(top.group(1), Entity(name=top.group(1), table=top.group(1)))
            for spec in _split_top(top.group(2)):
                f = _field(spec)
                if f and f.name not in {x.name for x in current.fields}:
                    current.fields.append(f)
        elif sub and current is not None:
            f = _field(sub.group(1))
            if f and f.name not in {x.name for x in current.fields}:
                current.fields.append(f)
    for n in names:
        if n not in out and n.lower() not in {k.lower() for k in out}:
            out[n] = Entity(name=n, table=None)
    return list(out.values()), [e.name for e in out.values() if not e.fields]


def derive(project_id: str, arch: Dict[str, Any], plan: Optional[Dict[str, Any]] = None) -> SharedContract:
    """The contract the architecture states. Not registered here (see service.register)."""
    from backend.services.validator import _section, _sections
    arch = arch if isinstance(arch, dict) else {}
    plan = plan if isinstance(plan, dict) else {}
    document = str(arch.get("document") or "")
    sections = _sections(document) if document else {}
    api_text = _section(sections, "api") if sections else document
    lines = {norm_key(m.group(1), m.group(2).rstrip(".").rstrip("`")): m.group(3) for m in _ROUTE.finditer(api_text)}
    endpoints: Dict[str, Endpoint] = {}
    unspec: Dict[str, List[str]] = {}
    structured = [a for a in (arch.get("apis") or []) if isinstance(a, dict) and a.get("method") and a.get("path")]
    for a in structured:
        key = norm_key(str(a["method"]), str(a["path"]))
        req = [f for f in (a.get("request_fields") or []) if isinstance(f, str)]
        res = [f for f in (a.get("response_fields") or []) if isinstance(f, str)]
        e = Endpoint(method=str(a["method"]).upper(), path=str(a["path"]), description=str(a.get("description", "")),
                     request_fields=req, response_fields=res,
                     responses={WILDCARD: {"content_type": "application/json",
                                           "schema": {"type": "object", "properties": {f: {} for f in res}, "required": res}
                                           if res else None}},
                     request_schema={"type": "object", "properties": {f: {} for f in req}, "required": req} if req else None)
        endpoints[key] = e
        unspec[op_key(e.method, e.path)] = ["success_status", "field_types"] + ([] if res else ["response_schema"]) \
            + ([] if req or e.method in ("GET", "DELETE") else ["request_schema"])
    for r in arch.get("routes") or []:
        m = re.match(r"^\s*(GET|POST|PUT|PATCH|DELETE)\s+(/\S*)", str(r), re.I)
        if not m:
            continue
        method, path = m.group(1).upper(), m.group(2).rstrip(".").rstrip("`")
        key = norm_key(method, path)
        if key in endpoints:
            continue
        endpoints[key] = Endpoint(method=method, path=path, description="as listed in the architecture's API specification",
                                  responses={WILDCARD: {"content_type": "application/json", "schema": None}})
        unspec[op_key(method, path)] = ["success_status", "response_schema"] + \
            (["request_schema"] if method in ("POST", "PUT", "PATCH") else [])
    for key, e in endpoints.items():
        text = lines.get(key, "")
        k = op_key(e.method, e.path)
        if _AUTH_NO.search(text):
            e.auth = "none"
        elif _AUTH_YES.search(text):
            e.auth = "bearer"
        else:
            unspec.setdefault(k, []).append("auth")
    schema_text = _section(sections, "database", "schema", "data model") if sections else ""
    entities, no_fields = entities_from_schema(schema_text, [str(n) for n in (arch.get("models") or [])])
    for n in no_fields:
        unspec.setdefault(f"entity {n}", []).append("fields")
    reqs = [str(r) for r in (plan.get("functional_requirements") or plan.get("requirements") or [])][:40]
    reqs += [f"feature: {f}" for f in (plan.get("features") or [])][:20]
    auth_text = " ".join(str(arch.get(k) or "") for k in ("authentication", "auth_strategy"))
    scheme = "bearer" if re.search(r"jwt|bearer|token|oauth", auth_text, re.I) else "unspecified"
    stack_backend = str(arch.get("backend") or plan.get("backend") or "")
    conventions: Dict[str, str] = {}
    error_format = None
    if not stack_backend or "fastapi" in stack_backend.lower():
        error_format = {"type": "object", "properties": {"detail": {}}, "required": ["detail"]}
        conventions["error_format"] = "FastAPI's HTTPException body ({\"detail\": ...}): the stack's convention"
    conventions["datetime_format"] = "ISO 8601 strings: JSON / Pydantic's serialisation of datetimes"
    contract_unspec = ["pagination", "environment"] + ([] if error_format else ["error_format"])
    unspec["contract"] = contract_unspec
    return SharedContract(project_id=project_id, api=Contract(name=str(plan.get("project_name") or arch.get("name") or "api"),
                                                               endpoints=list(endpoints.values())),
                          entities=entities, auth={"scheme": scheme, "source": auth_text[:200] or "not stated"},
                          error_format=error_format, datetime_format="iso8601", environment=[],
                          dependencies={"frontend": ["backend"], **({"backend": ["database"]} if entities else {})},
                          requirements=reqs, unspecified={k: sorted(set(v)) for k, v in unspec.items()},
                          conventions=conventions, source="architect", author="architect")


# --- validation ------------------------------------------------------------------------------------------------------

def validate(c: SharedContract) -> Tuple[List[str], List[str]]:
    import jsonschema
    errors: List[str] = []
    warnings: List[str] = []
    seen: Dict[str, str] = {}
    for e in c.api.endpoints:
        k = op_key(e.method, e.path)
        if e.method.upper() not in HTTP_METHODS:
            errors.append(f"{k}: method must be one of {', '.join(HTTP_METHODS)}")
        if not e.path.startswith("/") or " " in e.path or ".." in e.path:
            errors.append(f"{k}: path must start with '/' and contain no spaces or '..'")
        nk = norm_key(e.method, e.path)
        if nk in seen:
            errors.append(f"{k}: duplicates {seen[nk]} (same method and path shape)")
        seen[nk] = k
        params = set(re.findall(r"\{(\w+)\}", e.path))
        if set(e.path_params) - params:
            errors.append(f"{k}: path_params {sorted(set(e.path_params) - params)} are not in the path")
        if e.request_schema and e.method.upper() in ("GET", "DELETE"):
            warnings.append(f"{k}: a request body on {e.method.upper()} is unusual; clients may not send it")
        for where, s in ([("request_schema", e.request_schema)] + [(f"responses.{st}", (r or {}).get("schema")) for st, r in e.responses.items()]
                         + [(f"path_params.{n}", s) for n, s in e.path_params.items()]):
            if s:
                try:
                    jsonschema.Draft202012Validator.check_schema(s)
                except jsonschema.SchemaError as err:
                    errors.append(f"{k}: {where} is not a valid JSON Schema ({err.message})")
        for st in list(e.responses) + list(e.errors):
            if not (st == WILDCARD or re.fullmatch(r"[1-5]\d\d", str(st))):
                errors.append(f"{k}: status '{st}' must be a 3-digit code or '{WILDCARD}'")
        if not any(str(s).startswith("2") for s in e.responses):
            errors.append(f"{k}: no success response")
    names = [x.name for x in c.entities]
    for dup in sorted({n for n in names if names.count(n) > 1}):
        errors.append(f"entity {dup} is defined more than once")
    fields_of = {x.name: {f.name for f in x.fields} for x in c.entities}
    tables = {(x.table or x.name): x.name for x in c.entities}
    for x in c.entities:
        fn = [f.name for f in x.fields]
        for dup in sorted({n for n in fn if fn.count(n) > 1}):
            errors.append(f"entity {x.name}: field {dup} is defined more than once")
        if x.fields and not any(f.primary_key for f in x.fields):
            warnings.append(f"entity {x.name} has no primary key")
        for f in x.fields:
            if f.type not in FIELD_TYPES:
                errors.append(f"entity {x.name}.{f.name}: type must be one of {', '.join(FIELD_TYPES)}")
            if f.format not in FIELD_FORMATS:
                errors.append(f"entity {x.name}.{f.name}: format must be one of {', '.join(str(v) for v in FIELD_FORMATS if v)}")
            if f.references:
                ent, _, col = f.references.partition(".")
                target = ent if ent in fields_of else tables.get(ent)
                if target is None or (fields_of[target] and col not in fields_of[target]):
                    errors.append(f"entity {x.name}.{f.name} references {f.references}, which the contract does not define")
    for v in c.environment:
        if not _ENV_NAME.match(v.name):
            errors.append(f"environment variable '{v.name}' must be UPPER_SNAKE_CASE")
    if c.auth.get("scheme") not in ("bearer", "none", "unspecified"):
        errors.append("auth.scheme must be bearer, none or unspecified")
    if c.pagination and c.pagination.get("style") not in ("envelope", "array"):
        errors.append("pagination.style must be 'envelope' or 'array'")
    if c.datetime_format not in (None, "iso8601", "epoch_seconds", "epoch_millis"):
        errors.append("datetime_format must be iso8601, epoch_seconds or epoch_millis")
    if not c.api.endpoints and not c.entities:
        errors.append("the contract defines no API operation and no entity")
    return errors, warnings


# --- diff ------------------------------------------------------------------------------------------------------------

def _props(schema: Optional[Dict[str, Any]]) -> Tuple[Dict[str, Any], set, Optional[Any]]:
    s = schema or {}
    if s.get("type") == "array":
        s = s.get("items") or {}
    return dict(s.get("properties") or {}), set(s.get("required") or []), (schema or {}).get("type")


def _types(s: Dict[str, Any]) -> set:
    t = (s or {}).get("type")
    return set(t if isinstance(t, list) else [t]) - {None} if t else set()


def _code_for(impl: Optional[Dict[str, Any]], method: str, path: str) -> List[str]:
    if not impl:
        return []
    nk = norm_key(method, path)
    out = [f"{r['file']}:{r['line']}" for r in (impl.get("backend") or {}).get("routes", []) if norm_key(r["method"], r["path"]) == nk]
    out += [f"{c['file']}:{c['line']}" for c in (impl.get("frontend") or {}).get("calls", [])
            if c.get("path") and norm_key(c["method"], c["path"]) == nk]
    return out


def diff(old: Optional[SharedContract], new: SharedContract, impl: Optional[Dict[str, Any]] = None) -> List[ChangeItem]:
    """What changed from `old` to `new`, each with whether it breaks existing consumers and why."""
    items: List[ChangeItem] = []
    api_parts = ["backend", "frontend", "integration_tests"]

    def add(kind, target, before, after, breaking, why, components, code=()):
        items.append(ChangeItem(kind=kind, target=target, before=before, after=after, breaking=breaking, why=why,
                                affected_components=list(components), affected_code=list(code)))
    if old is None:
        for e in new.api.endpoints:
            add("endpoint_added", op_key(e.method, e.path), None, op_key(e.method, e.path), False, "first version", api_parts,
                _code_for(impl, e.method, e.path))
        for x in new.entities:
            add("entity_added", f"entity {x.name}", None, [f.name for f in x.fields], False, "first version", ["database", "backend"])
        return items
    o = {norm_key(e.method, e.path): e for e in old.api.endpoints}
    n = {norm_key(e.method, e.path): e for e in new.api.endpoints}
    for k in sorted(set(o) - set(n)):
        e = o[k]
        add("endpoint_removed", op_key(e.method, e.path), op_key(e.method, e.path), None, True,
            "clients that call it will get 404/405", api_parts, _code_for(impl, e.method, e.path))
    for k in sorted(set(n) - set(o)):
        e = n[k]
        add("endpoint_added", op_key(e.method, e.path), None, op_key(e.method, e.path), False,
            "existing clients are unaffected; the backend must implement it", ["backend", "integration_tests"],
            _code_for(impl, e.method, e.path))
    for k in sorted(set(o) & set(n)):
        a, b = o[k], n[k]
        t = op_key(b.method, b.path)
        code = _code_for(impl, b.method, b.path)
        if a.auth != b.auth:
            add("auth_changed", t, a.auth, b.auth, b.auth == "bearer",
                "clients without a token are now rejected" if b.auth == "bearer" else "requests no longer need a token "
                "(not breaking, but a security decision to review)", api_parts, code)
        ap, areq, _ = _props(a.request_schema)
        bp, breq, _ = _props(b.request_schema)
        for f in sorted(set(ap) - set(bp)):
            add("request_field_removed", f"{t} request.{f}", f, None, False,
                "clients that still send it are not rejected unless the model forbids extra fields", ["backend", "frontend"], code)
        for f in sorted(set(bp) - set(ap)):
            req = f in breq
            add("request_field_added", f"{t} request.{f}", None, {"required": req}, req,
                "existing clients do not send it and will get 422" if req else "optional: existing clients keep working",
                ["backend", "frontend"], code)
        for f in sorted(set(ap) & set(bp)):
            if (f in areq) != (f in breq):
                add("request_field_required" if f in breq else "request_field_optional", f"{t} request.{f}",
                    f in areq, f in breq, f in breq, "clients that omit it will get 422" if f in breq else "relaxes the request",
                    ["backend", "frontend"], code)
            if _types(ap[f]) and _types(bp[f]) and not (_types(ap[f]) & _types(bp[f])):
                add("request_field_type", f"{t} request.{f}", sorted(_types(ap[f])), sorted(_types(bp[f])), True,
                    "clients send the old type", ["backend", "frontend"], code)
        a_ok, a_schema = success(a)
        b_ok, b_schema = success(b)
        if a_ok and b_ok and set(a_ok) != set(b_ok):
            add("status_changed", t, a_ok, b_ok, True, "clients that check the status code see a different one", api_parts, code)
        rp, rreq, rtype = _props(a_schema)
        sp, sreq, stype = _props(b_schema)
        if rtype and stype and rtype != stype:
            add("response_shape_changed", f"{t} response", rtype, stype, True,
                "clients parse the old shape (e.g. a list became an object)", api_parts, code)
        for f in sorted(set(rp) - set(sp)):
            add("response_field_removed", f"{t} response.{f}", f, None, True, "clients that read it get undefined", api_parts, code)
        for f in sorted(set(sp) - set(rp)):
            add("response_field_added", f"{t} response.{f}", None, f, False, "clients ignore fields they do not read",
                ["backend", "integration_tests"], code)
        for f in sorted(set(rp) & set(sp)):
            if _types(rp[f]) and _types(sp[f]) and _types(rp[f]) != _types(sp[f]):
                add("response_field_type", f"{t} response.{f}", sorted(_types(rp[f])), sorted(_types(sp[f])),
                    not _types(rp[f]) <= _types(sp[f]) or "null" in _types(sp[f]) - _types(rp[f]),
                    "clients may receive a type (or null) they do not handle", api_parts, code)
            if f in rreq and f not in sreq:
                add("response_field_optional", f"{t} response.{f}", True, False, True, "clients may no longer receive it",
                    api_parts, code)
        for name in sorted(set(a.path_params) & set(b.path_params)):
            if _types(a.path_params[name]) and _types(b.path_params[name]) and _types(a.path_params[name]) != _types(b.path_params[name]):
                add("path_param_type", f"{t} {{{name}}}", sorted(_types(a.path_params[name])), sorted(_types(b.path_params[name])),
                    True, "identifiers in existing links / client code have the old format", api_parts, code)
        before_unspec = set(old.unspecified.get(op_key(a.method, a.path)) or [])
        after_unspec = set(new.unspecified.get(t) or [])
        for aspect in sorted(before_unspec - after_unspec):
            add("aspect_specified", t, f"{aspect}: unspecified", f"{aspect}: specified", False,
                "the contract now states it: implementations are checked against it", ["backend", "frontend"], code)
    oe = {x.name: x for x in old.entities}
    ne = {x.name: x for x in new.entities}
    for name in sorted(set(oe) - set(ne)):
        add("entity_removed", f"entity {name}", name, None, True, "persisted data and code that use it break", ["database", "backend"])
    for name in sorted(set(ne) - set(oe)):
        add("entity_added", f"entity {name}", None, [f.name for f in ne[name].fields], False, "needs a table / model and a migration",
            ["database", "backend"])
    for name in sorted(set(oe) & set(ne)):
        of = {f.name: f for f in oe[name].fields}
        nf = {f.name: f for f in ne[name].fields}
        for f in sorted(set(of) - set(nf)):
            add("entity_field_removed", f"entity {name}.{f}", f, None, True, "stored values and the code reading them break",
                ["database", "backend", "frontend"])
        for f in sorted(set(nf) - set(of)):
            strict = nf[f].required and not nf[f].nullable
            add("entity_field_added", f"entity {name}.{f}", None, nf[f].model_dump(), strict,
                "existing rows have no value for a required column (needs a default or a migration)" if strict
                else "nullable: existing rows stay valid", ["database", "backend"])
        for f in sorted(set(of) & set(nf)):
            x, y = of[f], nf[f]
            if (x.type, x.format) != (y.type, y.format) and "unknown" not in (x.type, y.type):
                add("entity_field_type", f"entity {name}.{f}", f"{x.type}/{x.format}", f"{y.type}/{y.format}", True,
                    "stored values and client code have the old type", ["database", "backend", "frontend"])
            if x.nullable != y.nullable:
                add("entity_field_nullability", f"entity {name}.{f}", x.nullable, y.nullable, True,
                    "existing nulls violate NOT NULL" if not y.nullable else "readers may now receive null",
                    ["database", "backend", "frontend"])
            if x.references != y.references:
                add("relationship_changed", f"entity {name}.{f}", x.references, y.references, True,
                    "the foreign key and the code joining on it change", ["database", "backend"])
    for attr, kind in (("error_format", "error_format_changed"), ("pagination", "pagination_changed"),
                       ("datetime_format", "datetime_format_changed")):
        if getattr(old, attr) != getattr(new, attr):
            add(kind, attr, getattr(old, attr), getattr(new, attr), getattr(old, attr) is not None,
                "the frontend parses the old convention" if getattr(old, attr) is not None else "the convention is now stated",
                ["backend", "frontend"])
    if old.auth.get("scheme") != new.auth.get("scheme"):
        add("auth_scheme_changed", "auth.scheme", old.auth.get("scheme"), new.auth.get("scheme"),
            new.auth.get("scheme") == "bearer", "clients must now authenticate" if new.auth.get("scheme") == "bearer"
            else "authentication requirement changed", api_parts)
    oenv = {v.name: v for v in old.environment}
    nenv = {v.name: v for v in new.environment}
    for v in sorted(set(nenv) - set(oenv)):
        add("environment_added", f"env {v}", None, nenv[v].component, nenv[v].required,
            "deployments must now set it" if nenv[v].required else "optional", [nenv[v].component])
    for v in sorted(set(oenv) - set(nenv)):
        add("environment_removed", f"env {v}", oenv[v].component, None, False, "no longer read", [oenv[v].component])
    return items


# --- agent slices ----------------------------------------------------------------------------------------------------

def _op(e: Endpoint, full: bool) -> Dict[str, Any]:
    ok, schema = success(e)
    out = {"operation": op_key(e.method, e.path), "auth": e.auth, "request_schema": e.request_schema,
           "success_status": ok or "any 2xx", "response_schema": schema, "errors": sorted(e.errors)}
    if full:
        out.update({"path_params": e.path_params, "query_params": e.query_params, "description": e.description})
    return out


def slice_for(c: SharedContract, agent: str) -> Dict[str, Any]:
    """The part of the contract an agent implements (and the conventions it must follow)."""
    common = {"contract_version": c.version, "revision": c.revision, "error_format": c.error_format,
              "datetime_format": c.datetime_format, "pagination": c.pagination, "unspecified": c.unspecified}
    if agent == "backend":
        return {**common, "operations": [_op(e, True) for e in c.api.endpoints],
                "entities": [x.model_dump() for x in c.entities], "auth": c.auth,
                "environment": [v.model_dump() for v in c.environment if v.component == "backend"]}
    if agent == "frontend":
        return {**common, "operations": [_op(e, False) for e in c.api.endpoints], "auth": c.auth,
                "environment": [v.model_dump() for v in c.environment if v.component == "frontend"]}
    if agent == "database":
        return {"contract_version": c.version, "revision": c.revision, "entities": [x.model_dump() for x in c.entities],
                "datetime_format": c.datetime_format,
                "environment": [v.model_dump() for v in c.environment if v.component == "database"]}
    raise ValueError(f"no contract slice for agent '{agent}'")


def render(sl: Dict[str, Any], agent: str) -> str:
    """A prompt section: the shared contract the agent must implement exactly (other agents build against it)."""
    import json
    rules = {"backend": "Implement every operation exactly: method, path, request fields and their types, success status, "
                        "response fields, authentication and error bodies. Do not rename fields or paths.",
             "frontend": "Call only these operations, with exactly these methods, paths and request fields; send the "
                         "Authorization header where auth is 'bearer'; read only the response fields listed.",
             "database": "Create exactly these entities: tables, columns, types, nullability, primary and foreign keys."}[agent]
    return (f"Shared integration contract v{sl.get('contract_version')} (revision {sl.get('revision')}) - the other agents "
            f"implement the same contract. {rules} Aspects listed under 'unspecified' are yours to choose; state them.\n"
            f"```json\n{json.dumps(sl, indent=1, default=str)[:12000]}\n```")
