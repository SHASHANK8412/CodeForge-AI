"""
Repair coordination for compatibility findings. The contract is the specification: a component that departs from it
is changed, never the contract to fit the component. A mismatch the contract does not decide (both sides agree on
something it lacks, a contradiction inside the contract) is a contract decision for the architect / a person - it
defers the implementation repairs that touch the same operation, and is never resolved automatically.

  order       contract decisions first (they block repairs on the same target), then database -> backend -> frontend
              (upstream first: the frontend is built against the backend, the backend against the data model)
  strategy    deterministic, line-precise fixes where the evidence names one exact change:
                frontend  the call's URL (contract path), its HTTP method, a request-body key renamed 1:1 to the
                          contract's, a response field read renamed to the contract's (when the analysis established
                          which field is meant)
                backend   the route decorator's path / method (keeping the handler's parameter names)
                database  schema.sql: a missing column, the column type, NULL / NOT NULL, a missing foreign key
              otherwise the responsible agent's model repair (its own system prompt, the contract slice and the
              evidence), limited to the files the findings name inside that agent's scope; secrets are hidden from the
              model and tests / env files are never changed (Execution Guardian scope rules)
"""

import logging
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from backend.compatibility import contract as ct
from backend.compatibility.models import CompatFinding, SharedContract
from backend.swarm import interfaces as itf

_logger = logging.getLogger("aiforge.compatibility.repair")
AGENT_ORDER = ("database", "backend", "frontend")
SQL_TYPE = {"integer": "INTEGER", "string": "TEXT", "boolean": "BOOLEAN", "number": "REAL", "object": "JSON", "array": "JSON"}


def _op_of(target: str) -> str:
    """'GET /api/tasks' from 'GET /api/tasks' / 'entity Task.title' -> 'entity Task'."""
    m = re.match(r"^(GET|POST|PUT|PATCH|DELETE) (\S+)", target)
    if m:
        return ct.norm_key(m.group(1), m.group(2))
    m = re.match(r"^entity (\w+)", target)
    return f"entity {m.group(1)}" if m else target


def pick(findings: List[CompatFinding], exhausted: set) -> Tuple[Optional[str], List[CompatFinding], List[CompatFinding]]:
    """(agent, its repairable findings, findings deferred by a pending contract decision)."""
    decisions = {_op_of(f.target) for f in findings if f.status == "needs_contract_decision"}
    cands = [f for f in findings if f.status == "open" and f.repairable and f.responsible_agent in AGENT_ORDER
             and f.key not in exhausted]
    deferred = [f for f in cands if _op_of(f.target) in decisions]
    cands = [f for f in cands if f not in deferred]
    for agent in AGENT_ORDER:
        group = [f for f in cands if f.responsible_agent == agent]
        if group:
            return agent, group, deferred
    return None, [], deferred


# --- deterministic strategies ------------------------------------------------------------------------------------

def _call(snap: Dict[str, Any], where: str) -> Optional[Dict[str, Any]]:
    file, _, line = where.rpartition(":")
    return next((c for c in (snap.get("frontend") or {}).get("calls", []) if c["file"] == file and str(c["line"]) == line), None)


def _pieces(path: str) -> List[str]:
    return re.sub(r"\{[^}]*\}", "{}", path).split("{}")


def fix_call_path(src: str, call: Dict[str, Any], contract_path: str) -> Optional[str]:
    """Rewrite the static parts of the call's URL expression so it reaches the contract's path."""
    if call.get("browser_path"):
        return None                                        # behind a dev-proxy rewrite: not a call-site change
    expr = call["url_expr"]
    expr_url, _ = itf._url_parts(expr)
    if expr_url is None:
        return None
    full = re.sub(r"\{[^}]*\}", "{}", call["path"])
    own = re.sub(r"\{[^}]*\}", "{}", expr_url)
    if not full.endswith(own):
        return None
    base = full[:len(full) - len(own)]
    target = re.sub(r"\{[^}]*\}", "{}", contract_path)
    if not target.startswith(base):
        return None
    new_own = target[len(base):]
    old_p, new_p = own.split("{}"), new_own.split("{}")
    if len(old_p) != len(new_p):
        return None
    out, cursor = expr, 0
    for a, b in zip(old_p, new_p):
        if a == b:
            if a:
                cursor = out.find(a, cursor) + len(a)
            continue
        if not a:
            return None
        i = out.find(a, cursor)
        if i < 0:
            return None
        out = out[:i] + b + out[i + len(a):]
        cursor = i + len(b)
    span = src[call["start"]:call["end"]]
    if expr not in span:
        return None
    return src[:call["start"]] + span.replace(expr, out, 1) + src[call["end"]:]


def fix_call_method(src: str, call: Dict[str, Any], method: str) -> Optional[str]:
    span = src[call["start"]:call["end"]]
    if call["client"] == "fetch":
        if re.search(r"method\s*:\s*['\"]\w+['\"]", span):
            new = re.sub(r"(method\s*:\s*['\"])\w+(['\"])", rf"\g<1>{method}\g<2>", span, count=1)
        elif method == "GET":
            return None
        else:
            return None
    else:
        new = re.sub(r"^(\w+)\.(get|post|put|patch|delete)\(", lambda m: f"{m.group(1)}.{method.lower()}(", span, count=1)
    return src[:call["start"]] + new + src[call["end"]:] if new != span else None


def fix_body_key(src: str, call: Dict[str, Any], old: str, new: str) -> Optional[str]:
    span = src[call["start"]:call["end"]]
    pat = re.compile(rf"([{{,]\s*){re.escape(old)}(\s*[:,}}])")
    m = pat.search(span)
    if not m:
        return None
    shorthand = m.group(2).strip().startswith((",", "}"))
    repl = f"{m.group(1)}{new}: {old}{m.group(2)}" if shorthand else f"{m.group(1)}{new}{m.group(2)}"
    return src[:call["start"]] + span[:m.start()] + repl + span[m.end():] + src[call["end"]:]


def fix_field_read(src: str, old: str, new: str) -> Optional[str]:
    out = re.sub(rf"(?<=[\w)\]])\.{re.escape(old)}\b", f".{new}", src)
    return out if out != src else None


def _route_decorator(lines: List[str], def_line: int) -> Optional[int]:
    for i in range(def_line - 2, max(-1, def_line - 12), -1):
        if re.search(r"@\w+\.(get|post|put|patch|delete)\(", lines[i]):
            return i
    return None


def fix_route(src: str, route_line: int, route_path: str, contract_method: Optional[str], contract_path: Optional[str]) -> Optional[str]:
    lines = src.split("\n")
    i = _route_decorator(lines, route_line)
    if i is None:
        return None
    line = lines[i]
    m = re.search(r"@(\w+)\.(get|post|put|patch|delete)\(\s*(['\"])([^'\"]*)\3", line)
    if not m:
        return None
    dec_path = m.group(4)
    new_line = line
    if contract_path is not None:
        if not route_path.endswith(dec_path):
            return None
        prefix = route_path[:len(route_path) - len(dec_path)]
        names = re.findall(r"\{(\w+)\}", route_path)
        pieces = _pieces(contract_path)
        if len(pieces) - 1 != len(names):
            return None
        full = pieces[0] + "".join("{" + n + "}" + p for n, p in zip(names, pieces[1:]))
        if not full.startswith(prefix):
            return None
        new_line = new_line[:m.start(4)] + full[len(prefix):] + new_line[m.end(4):]
    if contract_method is not None:
        new_line = re.sub(r"@(\w+)\.(get|post|put|patch|delete)\(", lambda x: f"@{x.group(1)}.{contract_method.lower()}(", new_line, count=1)
    if new_line == line:
        return None
    lines[i] = new_line
    return "\n".join(lines)


def _table_block(src: str, table: str) -> Optional[Tuple[int, int]]:
    m = re.search(rf"create\s+table\s+(?:if\s+not\s+exists\s+)?[`\"\[]?{re.escape(table)}[`\"\]]?\s*\(", src, re.I)
    if not m:
        return None
    depth, i = 1, m.end()
    while i < len(src) and depth:
        depth += {"(": 1, ")": -1}.get(src[i], 0)
        i += 1
    return m.end(), i - 1


def fix_sql(src: str, table: str, column: str, rule: str, field: Dict[str, Any], ref_table: Optional[str]) -> Optional[str]:
    block = _table_block(src, table)
    if block is None:
        return None
    start, end = block
    body = src[start:end]
    col_re = re.compile(rf"^([ \t]*)[`\"]?{re.escape(column)}[`\"]?[ \t]+([A-Za-z]+(?:\s*\([^)]*\))?)([^,\n]*)(,?)[ \t]*$", re.M | re.I)
    m = col_re.search(body)
    if rule == "db_missing_field":
        if m:
            return None
        sql_type = "TIMESTAMP" if field.get("format") == "date-time" else SQL_TYPE.get(field.get("type"), "TEXT")
        not_null = " NOT NULL" if field.get("required", True) and not field.get("nullable") else ""
        stripped = body.rstrip()
        indent = re.search(r"\n(\s+)\S", body)
        new_body = stripped + f",\n{indent.group(1) if indent else '  '}{column} {sql_type}{not_null}\n"
        return src[:start] + new_body + src[end:]
    if not m:
        return None
    ws, ctype, rest, comma = m.group(1), m.group(2), m.group(3), m.group(4)
    if rule == "db_field_type_mismatch":
        new_type = "TIMESTAMP" if field.get("format") == "date-time" else SQL_TYPE.get(field.get("type"))
        if not new_type:
            return None
        if field.get("type") == "boolean" and re.search(r"default\s+'[^']*'", rest, re.I):
            rest = re.sub(r"default\s+'[^']*'", "DEFAULT 0", rest, flags=re.I)
        new = f"{ws}{column} {new_type}{rest}{comma}"
    elif rule == "db_nullability_mismatch":
        want_null = field.get("nullable") or not field.get("required", True)
        rest2 = re.sub(r"\s+not\s+null", "", rest, flags=re.I)
        new = f"{ws}{column} {ctype}{rest2 if want_null else (' NOT NULL' + rest2)}{comma}"
    elif rule == "db_missing_relationship" and ref_table:
        ref_col = (field.get("references") or ".id").split(".", 1)[1] or "id"
        if re.search(r"references", rest, re.I):
            return None
        new = f"{ws}{column} {ctype}{rest} REFERENCES {ref_table}({ref_col}){comma}"
    else:
        return None
    new_body = body[:m.start()] + new + body[m.end():]
    return src[:start] + new_body + src[end:]


def deterministic(group: List[CompatFinding], files: Dict[str, str], snap: Dict[str, Any], c: SharedContract
                  ) -> Tuple[Dict[str, str], List[str], List[str]]:
    """({path: new content}, strategies used, keys of the findings they address)."""
    changed: Dict[str, str] = {}
    used, keys = [], []
    shifts: Dict[str, List[Tuple[int, int]]] = {}       # per file: (offset, delta) of the edits made so far

    def cur(path):
        return changed.get(path, files.get(path))

    def located(call):
        """The call's span in the file as edited so far."""
        sh = shifts.get(call["file"], [])
        return {**call, "start": call["start"] + sum(d for o, d in sh if o < call["start"]),
                "end": call["end"] + sum(d for o, d in sh if o < call["end"])}
    by_call: Dict[str, List[CompatFinding]] = {}
    for f in group:
        if f.responsible_agent == "frontend" and f.evidence.get("call"):
            by_call.setdefault(f.evidence["call"], []).append(f)
    entities = {x.name: x for x in c.entities}
    # offset-based call edits from the end of each file backwards; file-wide renames last
    order = sorted(group, key=lambda f: (f.rule == "response_field_mismatch",
                                         -((_call(snap, f.evidence["call"]) or {}).get("start", 0) if f.evidence.get("call") else 0)))
    for f in order:
        ev = f.evidence
        new: Optional[str] = None
        path = None
        strategy = ""
        if f.responsible_agent == "frontend" and ev.get("call"):
            raw = _call(snap, ev["call"])
            if raw is None or cur(raw["file"]) is None:
                continue
            call = located(raw)
            path, src = call["file"], cur(call["file"])
            if f.rule == "incorrect_url_path" and ev.get("contract_path"):
                new, strategy = fix_call_path(src, call, ev["contract_path"]), "frontend_call_path"
            elif f.rule == "incorrect_http_method":
                methods = ev.get("contract_methods") or []
                if call["body_fields"] is not None and call["method"] in ("POST", "PUT", "PATCH"):
                    methods = [m for m in methods if m in ("POST", "PUT", "PATCH")] or methods
                if len(methods) == 1:
                    new, strategy = fix_call_method(src, call, methods[0]), "frontend_call_method"
            elif f.rule == "response_field_mismatch" and ev.get("likely") and ev.get("field"):
                new, strategy = fix_field_read(src, ev["field"], ev["likely"]), "frontend_read_field"
            elif f.rule in ("request_field_mismatch", "missing_required_field"):
                sibling = by_call.get(ev["call"], [])
                unknown = next((x.evidence.get("unknown") for x in sibling if x.rule == "request_field_mismatch"
                                and x.evidence.get("unknown")), None)
                missing = next((x.evidence.get("missing") for x in sibling if x.rule == "missing_required_field"
                                and x.evidence.get("missing")), None)
                if unknown and missing and len(unknown) == len(missing) == 1:
                    new, strategy = fix_body_key(src, call, unknown[0], missing[0]), "frontend_body_key"
                    if new:
                        for x in sibling:
                            if x.rule in ("request_field_mismatch", "missing_required_field") and x.key not in keys:
                                keys.append(x.key)
        elif f.responsible_agent == "backend" and f.rule in ("incorrect_url_path", "incorrect_http_method") and ev.get("route" if f.rule == "incorrect_url_path" else "routes"):
            where = ev.get("route") or (ev.get("routes") or [None])[0]
            file, _, line = where.rpartition(":")
            route = next((r for r in (snap.get("backend") or {}).get("routes", []) if r["file"] == file and str(r["line"]) == line), None)
            m = re.match(r"^(GET|POST|PUT|PATCH|DELETE) (\S+)", f.target)
            if route and m and cur(file) is not None:
                path = file
                if f.rule == "incorrect_url_path":
                    new, strategy = fix_route(cur(file), route["line"], route["path"], None, m.group(2)), "backend_route_path"
                else:
                    new, strategy = fix_route(cur(file), route["line"], route["path"], m.group(1), None), "backend_route_method"
        elif f.responsible_agent == "database" and ev.get("source") == "schema" and ev.get("file", "").endswith(".sql"):
            m = re.match(r"^entity (\w+)\.(\w+)$", f.target)
            if m and m.group(1) in entities and cur(ev["file"]) is not None:
                field = next((x for x in entities[m.group(1)].fields if x.name == m.group(2)), None)
                if field is not None:
                    ref_table = None
                    if field.references:
                        ent = entities.get(field.references.split(".")[0])
                        ref_table = (ent.table or ent.name) if ent else field.references.split(".")[0]
                    path = ev["file"]
                    new = fix_sql(cur(path), ev["table"], field.name, f.rule, field.model_dump(), ref_table)
                    strategy = f"schema_sql_{f.rule.replace('db_', '')}"
        if new and path:
            if f.responsible_agent == "frontend" and ev.get("call") and strategy != "frontend_read_field":
                shifts.setdefault(path, []).append((call["start"], len(new) - len(cur(path))))
            changed[path] = new
            if strategy not in used:
                used.append(strategy)
            if f.key not in keys:
                keys.append(f.key)
    return changed, used, keys


# --- model repair ------------------------------------------------------------------------------------------------

def _files_named(group: List[CompatFinding]) -> List[str]:
    out = []
    for f in group:
        for k in ("call", "route", "model", "file"):
            v = f.evidence.get(k)
            if isinstance(v, str) and v:
                out.append(v.rsplit(":", 1)[0] if re.search(r":\d+$", v) else v)
        for v in f.evidence.get("routes") or []:
            out.append(v.rsplit(":", 1)[0])
    return sorted(set(out))


def model_repair(group: List[CompatFinding], agent: str, ws: Path, stack: Dict[str, Any], c: SharedContract, project_id: str,
                 generate: Optional[Callable[[str, str], str]]) -> Tuple[str, Dict[str, Optional[str]], str]:
    """The responsible agent's own repair with the contract slice and the evidence (Guardian / Autopilot machinery)."""
    from backend.evolution.autopilot.executor import HiddenLineChanged, model_changes
    from backend.execution_guardian import repair as grep_
    from backend.routes.export import _read_project_dir
    files = _read_project_dir(ws)
    named = [f for f in _files_named(group) if f in files and grep_.in_scope(agent, f, stack, [])[0]]
    if not named:
        named = sorted(f for f in files if grep_.in_scope(agent, f, stack, [])[0])[:4]
    if not named:
        return f"model:{agent}", {}, f"no file in the {agent} agent's scope to repair"
    request = ("Make the implementation match the shared integration contract. The contract is the specification: "
               "change the code, never the contract's paths, fields, types or statuses.\n\n"
               + ct.render(ct.slice_for(c, agent), agent) + "\n\nCompatibility findings to fix:\n"
               + "\n".join(f"- [{f.rule}] {f.target}: expected {f.expected}; actual {f.actual}. Fix: {f.recommended_fix}"
                           for f in group)
               + (f"\n\nProject requirements:\n" + "\n".join(f"- {r}" for r in c.requirements[:20]) if c.requirements else ""))
    try:
        changes = model_changes(ws, project_id, named, [], request, generate, topic=group[0].target,
                                system_prompt=grep_.agent_prompt(agent))
    except HiddenLineChanged as e:
        return f"model:{agent}", {}, f"rejected: the model altered a hidden secret line ({e})"
    except PermissionError as e:
        return f"model:{agent}", {}, str(e)
    except Exception as e:  # noqa: BLE001 - an unavailable model is a recorded, unproductive attempt
        return f"model:{agent}", {}, f"the {agent} agent's model was unavailable: {type(e).__name__}: {e}"[:300]
    return f"model:{agent}", {k: v for k, v in changes.items() if v != files.get(k)}, ""


def validate(changes: Dict[str, Optional[str]], agent: str, stack: Dict[str, Any], ws: Path, group: List[CompatFinding]):
    from backend.execution_guardian import repair as grep_
    return grep_.validate(changes, agent, stack, ws, _files_named(group))
