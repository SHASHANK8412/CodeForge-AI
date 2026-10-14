"""
Runtime contract testing: the integrated backend runs in the Chaos Engineer's isolated sandbox (hardened app
container on an internal Docker network, no route out), and a node:20-slim container on the same network runs
harness.mjs, which

  1. fetches the app's /openapi.json (declared behaviour),
  2. sends contract tests built here from the contract (valid request, missing required field, malformed body,
     wrongly typed / missing parameters, no credentials, unknown resource),
  3. imports the generated frontend client and calls each exported function, recording every request it makes
     and the response it gets,
  4. tries to reach the outside (must fail).

Everything it returns is raw; evaluate() validates it here against the contract with jsonschema. A check that
failed is executed once more in the same environment: failing again = failed, passing = flaky (never a pass).
Docker missing = blocked (never skipped or passed).

  build_plan(contract, routes, exports)   the requests and client calls to make (no generated code is read
                                          for values except the backend's declared types where the contract
                                          leaves a type open)
  evaluate(contract, plan, raw)           checks: passed | failed | inconclusive | blocked, with evidence
  DockerRuntime                           start / execute / isolation / stop (explicit timeouts, always cleaned)
"""

import json
import logging
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.evolution.autopilot.redact import redact
from backend.swarm import schemas
from backend.swarm.interfaces import _norm

_logger = logging.getLogger("aiforge.swarm.runtime")
HARNESS = Path(__file__).with_name("harness.mjs")
NODE_IMAGE = "node:20-slim"
TEST_TOKEN = "aiforge-contract-test-token"          # a fixed dummy credential; never a real one
STORAGE_KEYS = ("token", "access_token", "accessToken", "authToken", "auth_token", "jwt")
EGRESS_TARGETS = ("http://1.1.1.1/", "http://host.docker.internal:8000/")
INVALID_KINDS = ("missing_required_field", "malformed_body", "invalid_path_param", "missing_query_param")


class RuntimeBlocked(RuntimeError):
    """The isolated environment could not be provided (e.g. Docker is not running)."""


class AppFailed(RuntimeError):
    """The generated backend did not start or answer (its logs are attached)."""

    def __init__(self, message: str, logs: str = ""):
        super().__init__(message)
        self.logs = logs


# --- plan ----------------------------------------------------------------------------------------------------

def _path_regex(path: str) -> re.Pattern:
    return re.compile("^" + re.sub(r"\\\{\w+\\\}", r"[^/]+", re.escape(path.rstrip("/") or "/")) + "/?$")


def _find(endpoints: List[Dict[str, Any]], method: str, path: str) -> Optional[Dict[str, Any]]:
    for e in endpoints:
        if e["method"].upper() == method.upper() and (_norm(e["path"]) == _norm(path) or _path_regex(e["path"]).match(path.split("?")[0])):
            return e
    return None


def _route_for(routes: List[Dict[str, Any]], e: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    return next((r for r in routes if r["method"] == e["method"].upper() and _norm(r["path"]) == _norm(e["path"])), None)


def _fill(schema: Optional[Dict[str, Any]], hint: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Where the contract leaves a property's type open ({}), use the backend's declared type: a value of that
    type satisfies both (recorded as a hint in the plan)."""
    if not schema or schema.get("type") != "object" or not hint:
        return schema
    props = dict(schema.get("properties") or {})
    hp = hint.get("properties") or {}
    for k, v in props.items():
        if not v and hp.get(k):
            props[k] = hp[k]
    return {**schema, "properties": props}


def _order(endpoints: List[Dict[str, Any]]) -> List[int]:
    """Creating operations first, so later operations can use the resources they create."""
    return sorted(range(len(endpoints)), key=lambda i: (endpoints[i]["method"].upper() not in ("POST", "PUT"), "{" in endpoints[i]["path"], i))


def _collection(endpoints, e, steps_by_endpoint) -> Optional[str]:
    """The step that created a resource this endpoint addresses (POST /x before GET /x/{id})."""
    prefix = e["path"].split("{")[0].rstrip("/")
    for j, other in enumerate(endpoints):
        if other["method"].upper() == "POST" and other["path"].rstrip("/") == prefix and j in steps_by_endpoint:
            return steps_by_endpoint[j]
    return None


def build_plan(contract: Dict[str, Any], routes: List[Dict[str, Any]], exports: List[Dict[str, Any]],
               root: str, base: str = "http://app:8000", request_timeout_ms: int = 8000,
               call_timeout_ms: int = 15000) -> Dict[str, Any]:
    endpoints = contract["endpoints"]
    direct: List[Dict[str, Any]] = []
    hints: List[str] = []
    valid_step: Dict[int, str] = {}
    for i in _order(endpoints):
        e = endpoints[i]
        key = f"{e['method'].upper()} {e['path']}"
        route = _route_for(routes, e)
        req = _fill(e.get("request_schema"), (route or {}).get("request_schema"))
        if req is not e.get("request_schema"):
            hints.append(f"{key}: open property types filled from the backend's declared model")
        pschemas = {p: (s or ((route or {}).get("path_param_schemas") or {}).get(p) or {}) for p, s in (e.get("path_params") or {}).items()}
        defaults = {p: schemas.example(s, p) if s else "1" for p, s in pschemas.items()}
        creator = _collection(endpoints, e, valid_step)
        bind = {p: [creator, "id"] for p in pschemas} if creator and len(pschemas) == 1 else {}
        q_required = {k: str(schemas.example(v.get("schema"), k)) for k, v in (e.get("query_params") or {}).items() if v.get("required")}
        hdrs = {k: f"example-{k}" for k, v in (e.get("headers") or {}).items() if v.get("required")}
        if e.get("auth") == "bearer":
            hdrs["Authorization"] = f"Bearer {TEST_TOKEN}"
        body = schemas.example(req) if req else None
        ctype = {"Content-Type": e.get("request_content_type") or "application/json"} if req else {}

        def step(kind, **over):
            s = {"id": f"e{i}:{kind}", "endpoint": key, "kind": kind, "method": e["method"].upper(), "path": e["path"],
                 "bind": bind, "defaults": defaults, "query": q_required, "headers": {**hdrs, **ctype},
                 "body_text": json.dumps(body) if body is not None else None}
            s.update(over)
            direct.append(s)
            return s["id"]
        valid_step[i] = step("valid")
        if req and req.get("required"):
            drop = req["required"][0]
            step("missing_required_field", body_text=json.dumps({k: v for k, v in (body or {}).items() if k != drop}), dropped=drop)
        if req:
            step("malformed_body", body_text='{"not valid json')
        typed = {p: s for p, s in pschemas.items() if s.get("type") in ("integer", "number")}
        if typed:
            step("invalid_path_param", bind={}, defaults={**defaults, **{p: "not-a-number" for p in typed}})
        if q_required:
            step("missing_query_param", query={k: v for k, v in list(q_required.items())[1:]}, dropped=next(iter(q_required)))
        if e.get("auth") == "bearer":
            step("unauthenticated", headers={k: v for k, v in {**hdrs, **ctype}.items() if k != "Authorization"})
        if "404" in (e.get("errors") or {}) and pschemas:
            step("not_found", bind={}, defaults={p: (999999 if s.get("type") in ("integer", "number") else "aiforge-missing")
                                                  for p, s in pschemas.items()})
    client = _client_steps(endpoints, routes, exports)
    return {"base": base, "root": root, "direct": direct, "client": client, "hints": hints,
            "request_timeout_ms": request_timeout_ms, "call_timeout_ms": call_timeout_ms,
            "storage": {k: TEST_TOKEN for k in STORAGE_KEYS}, "egress": list(EGRESS_TARGETS)}


def _nearest(endpoints, method, path) -> Optional[Dict[str, Any]]:
    """The contract endpoint a call was most likely meant for (same method, longest common path prefix)."""
    same = [e for e in endpoints if e["method"].upper() == method.upper()]
    if not same or not path:
        return same[0] if same else None

    def common(a, b):
        n = 0
        for x, y in zip(_norm(a).split("/"), _norm(b).split("/")):
            if x != y:
                break
            n += 1
        return n
    return max(same, key=lambda e: (common(e["path"], path), -abs(len(e["path"]) - len(path))))


def _client_steps(endpoints, routes, exports) -> List[Dict[str, Any]]:
    steps = []
    creators: Dict[str, str] = {}
    usable = [x for x in exports if x["calls"]]
    usable.sort(key=lambda x: (x["calls"][0]["method"] not in ("POST", "PUT"), "{}" in (x["calls"][0]["path"] or ""), x["line"]))
    for x in usable:
        c = x["calls"][0]
        e = _find(endpoints, c["method"], c["path"] or "") if c["path"] else None
        target = e or _nearest(endpoints, c["method"], c["path"] or "")
        route = _route_for(routes, target) if target else None
        req = _fill((target or {}).get("request_schema"), (route or {}).get("request_schema")) or {}
        props = req.get("properties") or {}
        pnames = list((target or {}).get("path_params") or {})
        args = []
        for p in x["params"]:
            if p in (c.get("path_exprs") or []):
                k = c["path_exprs"].index(p)
                pn = pnames[k] if k < len(pnames) else (pnames[0] if pnames else p)
                ps = ((target or {}).get("path_params") or {}).get(pn) or ((route or {}).get("path_param_schemas") or {}).get(pn) or {}
                default = schemas.example(ps, pn) if ps else 1
                creator = creators.get(target["path"].split("{")[0].rstrip("/")) if target else None
                args.append({"from": creator, "field": "id", "default": default} if creator else {"value": default})
            elif c.get("body_expr") == p:
                args.append({"value": schemas.example(req) if req else {}})
            elif any(re.search(rf"\b{re.escape(p)}\b", v) for v in (c.get("body_map") or {}).values()):
                key = next(k for k, v in c["body_map"].items() if re.search(rf"\b{re.escape(p)}\b", v))
                args.append({"value": schemas.example(props[key], key) if key in props else f"example-{key}"})
            else:
                args.append({"undefined": True})
        if c["method"] == "POST" and target:
            creators[target["path"].rstrip("/")] = x["export"]
        steps.append({"module": x["module"], "export": x["export"], "args": args,
                      "endpoint": f"{target['method'].upper()} {target['path']}" if target else None,
                      "static_call": {k: c.get(k) for k in ("method", "path", "file", "line")}})
    return steps


# --- evaluation ------------------------------------------------------------------------------------------------

def _json(text: Optional[str]) -> Tuple[bool, Any]:
    try:
        return True, json.loads(text or "")
    except (ValueError, TypeError):
        return False, None


def _ctype_ok(observed: Optional[str], expected: Optional[str]) -> bool:
    return not expected or (observed or "").split(";")[0].strip().lower() == expected.split(";")[0].strip().lower()


def _response_problems(e: Dict[str, Any], status: Optional[int], ctype: Optional[str], body: Optional[str]) -> Tuple[List[Dict[str, str]], str]:
    """Problems of a response to a valid request: (problems [{category, detail}], expected text)."""
    responses = e.get("responses") or {}
    expected = "status " + "/".join(sorted(responses)) + " with " + ", ".join(
        f"{k}: {v.get('content_type', 'application/json')}" for k, v in sorted(responses.items()))
    if status is None:
        return [{"category": "backend_runtime_error", "detail": "no response"}], expected
    if status >= 500:
        return [{"category": "backend_runtime_error", "detail": f"server error {status}: {(body or '')[:200]}"}], expected
    spec = responses.get(str(status))
    if spec is None:
        return [{"category": "http_status_mismatch", "detail": f"status {status}; the contract allows {sorted(responses)}"}], expected
    problems = []
    if not _ctype_ok(ctype, spec.get("content_type")):
        problems.append({"category": "response_schema_mismatch", "detail": f"content type {ctype!r}; the contract says {spec.get('content_type')!r}"})
    if (spec.get("content_type") or "application/json").startswith("application/json") and spec.get("schema") is not None:
        ok, value = _json(body)
        if not ok:
            problems.append({"category": "response_schema_mismatch", "detail": "the body is not JSON"})
        else:
            problems += [{"category": "response_schema_mismatch", "detail": f"response {m}"} for m in schemas.validate(value, spec["schema"])]
    return problems, expected


def evaluate(contract: Dict[str, Any], plan: Dict[str, Any], raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    endpoints = contract["endpoints"]
    by_key = {f"{e['method'].upper()} {e['path']}": e for e in endpoints}
    results = {r["id"]: r for r in raw.get("direct", [])}
    checks: List[Dict[str, Any]] = []
    valid_passed = set()
    for s in plan["direct"]:
        e, r = by_key[s["endpoint"]], results.get(s["id"])
        chk = {"id": s["id"], "source": "contract_test", "endpoint": s["endpoint"], "kind": s["kind"],
               "request": {"method": s["method"], "path": (r or {}).get("path", s["path"]) + (r or {}).get("query", ""),
                           "body": (s.get("body_text") or "")[:500] if s.get("body_text") else None,
                           "headers": sorted(s.get("headers") or {})},
               "response": {"status": (r or {}).get("status"), "content_type": (r or {}).get("content_type"),
                            "body": redact(((r or {}).get("body") or "")[:600])} if r else None}
        if r is None:
            checks.append({**chk, "status": "blocked", "expected": "the check runs", "observed": "not executed", "problems": []})
            continue
        if r.get("error"):
            cat = "backend_runtime_error"
            checks.append({**chk, "status": "failed", "expected": "a response", "observed": f"request error: {r['error']}",
                           "problems": [{"category": cat, "detail": f"request error: {r['error']}"}]})
            continue
        status = r.get("status")
        if s["kind"] == "valid":
            problems, expected = _response_problems(e, status, r.get("content_type"), r.get("body"))
            if e.get("auth") == "bearer" and status in (401, 403):
                checks.append({**chk, "status": "inconclusive", "expected": expected,
                               "observed": f"status {status}: the backend rejected the dummy test credential",
                               "problems": [{"category": "insufficient_evidence",
                                             "detail": "no test credential exists for this backend, so the success response cannot be verified"}]})
                continue
            if not problems:
                valid_passed.add(s["endpoint"])
            checks.append({**chk, "status": "failed" if problems else "passed", "expected": expected,
                           "observed": f"status {status}, {r.get('content_type')}", "problems": problems})
        elif s["kind"] in INVALID_KINDS:
            documented = sorted(k for k in (e.get("errors") or {}) if k.startswith("4"))
            expected = f"a client error ({'/'.join(documented) or '4xx'})"
            if status is not None and 200 <= status < 300:
                problems = [{"category": "request_contract_mismatch",
                             "detail": f"{s['kind'].replace('_', ' ')} was accepted with status {status}"}]
            elif status is not None and status >= 500:
                problems = [{"category": "backend_runtime_error", "detail": f"{s['kind'].replace('_', ' ')} caused server error {status}"}]
            elif documented and str(status) not in documented:
                problems = [{"category": "http_status_mismatch", "detail": f"status {status}; documented errors are {documented}"}]
            else:
                problems = []
            checks.append({**chk, "status": "failed" if problems else "passed", "expected": expected,
                           "observed": f"status {status}", "problems": problems})
        elif s["kind"] == "unauthenticated":
            ok = status in (401, 403)
            checks.append({**chk, "status": "passed" if ok else "failed", "expected": "401 or 403 without credentials",
                           "observed": f"status {status}",
                           "problems": [] if ok else [{"category": "auth_mismatch",
                                                       "detail": f"a request without credentials got status {status}"}]})
        elif s["kind"] == "not_found":
            ok = status == 404
            checks.append({**chk, "status": "passed" if ok else "failed", "expected": "404 for an unknown resource",
                           "observed": f"status {status}",
                           "problems": [] if ok else [{"category": "http_status_mismatch" if (status or 0) < 500 else "backend_runtime_error",
                                                       "detail": f"an unknown resource got status {status}"}]})
    checks += _client_checks(endpoints, plan, raw, valid_passed)
    return checks


def _client_checks(endpoints, plan, raw, valid_passed) -> List[Dict[str, Any]]:
    checks = []
    by_export = {r.get("export"): r for r in raw.get("client", [])}
    for st in plan["client"]:
        r = by_export.get(st["export"])
        base = {"id": f"client:{st['export']}", "source": "frontend_client", "endpoint": st.get("endpoint") or "unknown",
                "kind": "client_call", "export": st["export"], "module": st["module"], "static_call": st.get("static_call")}
        if r is None:
            checks.append({**base, "status": "blocked", "expected": "the client function is called", "observed": "not executed", "problems": []})
            continue
        reqs = r.get("requests") or []
        base["requests"] = [{k: (redact(v[:600]) if isinstance(v, str) else v) for k, v in q.items() if k != "response"} |
                            {"response": redact((q.get("response") or "")[:600])} for q in reqs]
        if r.get("error") and not reqs:
            checks.append({**base, "status": "failed", "expected": f"{st['export']}() calls {st.get('endpoint')}",
                           "observed": r["error"], "problems": [{"category": "frontend_integration_error", "responsible": "frontend",
                                                                  "detail": f"{st['export']}() failed before sending a request: {r['error']}"}]})
            continue
        if not reqs:
            checks.append({**base, "status": "failed", "expected": f"{st['export']}() sends a request", "observed": "no request was sent",
                           "problems": [{"category": "frontend_integration_error", "responsible": "frontend", "detail": "no request was sent"}]})
            continue
        problems: List[Dict[str, str]] = []
        for q in reqs:
            e = _find(endpoints, q["method"], q["path"])
            if e is None:
                near = _nearest(endpoints, q["method"], q["path"])
                hint = f" (nearest contract operation: {near['method'].upper()} {near['path']})" if near else ""
                problems.append({"category": "request_contract_mismatch", "responsible": "frontend",
                                 "detail": f"sends {q['method']} {q['path']}, which is not in the contract{hint}"})
                if near and near.get("request_schema") and q.get("body"):
                    ok, value = _json(q["body"])
                    if ok:
                        problems += [{"category": "request_contract_mismatch", "responsible": "frontend", "detail": f"request body {m}"}
                                     for m in schemas.validate(value, near["request_schema"])]
                continue
            base["endpoint"] = f"{e['method'].upper()} {e['path']}"
            if e.get("request_schema"):
                ok, value = _json(q.get("body"))
                if not ok:
                    problems.append({"category": "request_contract_mismatch", "responsible": "frontend", "detail": "the request body is not JSON"})
                else:
                    problems += [{"category": "request_contract_mismatch", "responsible": "frontend", "detail": f"request body {m}"}
                                 for m in schemas.validate(value, e["request_schema"])]
                ct = (q.get("headers") or {}).get("content-type")
                if not _ctype_ok(ct, e.get("request_content_type") or "application/json"):
                    problems.append({"category": "request_contract_mismatch", "responsible": "frontend",
                                     "detail": f"Content-Type {ct!r}; the contract says {e.get('request_content_type') or 'application/json'!r}"})
            if e.get("auth") == "bearer" and "authorization" not in (q.get("headers") or {}):
                problems.append({"category": "auth_mismatch", "responsible": "frontend", "detail": "sends no Authorization header"})
            for p, qp in (e.get("query_params") or {}).items():
                if qp.get("required") and f"{p}=" not in (q.get("query") or ""):
                    problems.append({"category": "request_contract_mismatch", "responsible": "frontend", "detail": f"omits required query parameter {p}"})
            if problems:
                continue
            if q.get("error"):
                problems.append({"category": "backend_runtime_error", "responsible": "backend", "detail": f"request error: {q['error']}"})
                continue
            resp_problems, _ = _response_problems(e, q.get("status"), q.get("content_type"), q.get("response"))
            if resp_problems:
                if base["endpoint"] in valid_passed and q.get("status") and 400 <= q["status"] < 500:
                    # the backend answered the contract test correctly; this request depends on state an earlier client call
                    # did not create (or on values the contract leaves open) - not attributable from this evidence
                    problems.append({"category": "insufficient_evidence", "responsible": None,
                                     "detail": f"status {q['status']} for a conforming request; the same operation passed its contract test"})
                else:
                    problems += [{**p, "responsible": "backend"} for p in resp_problems]
        if not problems and r.get("error"):
            problems.append({"category": "frontend_integration_error", "responsible": "frontend",
                             "detail": f"{st['export']}() threw on a conforming response: {r['error']}"})
        status = ("passed" if not problems else
                  "inconclusive" if all(p["category"] == "insufficient_evidence" for p in problems) else "failed")
        checks.append({**base, "status": status, "expected": f"{st['export']}() follows {base['endpoint']} of the contract",
                       "observed": "; ".join(p["detail"] for p in problems) or "conforms", "problems": problems,
                       "returned": r.get("returned") if not isinstance(r.get("returned"), str) else redact(r["returned"][:300])})
    return checks


def merge_rerun(first: List[Dict[str, Any]], second: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """A check that failed and then passed in the same environment is flaky (not a pass)."""
    again = {c["id"]: c for c in second}
    out = []
    for c in first:
        r = again.get(c["id"])
        if c["status"] == "failed" and r is not None:
            if r["status"] == "passed":
                c = {**c, "status": "flaky", "rerun": {"status": "passed"}}
            else:
                c = {**c, "rerun": {"status": r["status"], "observed": r.get("observed")}}
        out.append(c)
    return out


def declared(openapi_text: Optional[str], contract: Dict[str, Any]) -> Dict[str, Any]:
    """What the app's own OpenAPI document declares for each contract operation."""
    ok, spec = _json(openapi_text)
    if not ok or not isinstance(spec, dict):
        return {}
    out = {}
    for e in contract["endpoints"]:
        op = next(((ops or {}).get(e["method"].lower()) for p, ops in (spec.get("paths") or {}).items() if _norm(p) == _norm(e["path"])), None)
        key = f"{e['method'].upper()} {e['path']}"
        if op is None:
            out[key] = {"present": False}
            continue
        out[key] = {"present": True, "statuses": sorted((op.get("responses") or {})),
                    "request_body": bool(op.get("requestBody")),
                    "auth": "bearer" if op.get("security") or spec.get("security") else "none",
                    "query": sorted(p["name"] for p in op.get("parameters") or [] if p.get("in") == "query"),
                    "response_content_types": sorted({ct for r in (op.get("responses") or {}).values() for ct in (r.get("content") or {})})}
    return out


# --- the isolated environment ----------------------------------------------------------------------------------------

def prepare_workdir(files: Dict[str, str], plan: Dict[str, Any]) -> Path:
    """A throwaway folder (mounted read-only into the node container) with the client modules, the harness and
    the plan. `import.meta.env` (a bundler feature) is rewritten to an object the harness provides."""
    work = Path(tempfile.mkdtemp(prefix="aiforge_swarm_node_"))
    for rel, content in files.items():
        if not rel.startswith("frontend/") or not rel.endswith((".js", ".mjs")) or ".." in rel.split("/"):
            continue
        target = work / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content.replace("import.meta.env", "globalThis.__AIFORGE_ENV__"), encoding="utf-8")
    (work / "package.json").write_text('{"type": "module"}\n', encoding="utf-8")
    shutil.copyfile(HARNESS, work / "harness.mjs")
    (work / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
    return work


def parse_output(stdout: str) -> Dict[str, Any]:
    for line in reversed((stdout or "").splitlines()):
        if line.startswith("AIFORGE_RESULT "):
            return json.loads(line[len("AIFORGE_RESULT "):])
    raise ValueError("the harness printed no result")


class DockerRuntime:
    """The backend in the Chaos sandbox (internal network) + a hardened node container for the harness."""
    environment = "Docker: hardened app container + node:20-slim on an internal network"

    def __init__(self, start_budget_s: float = 90.0, exec_timeout_s: float = 240.0):
        self.start_budget_s = start_budget_s
        self.exec_timeout_s = exec_timeout_s
        self.sandbox = None
        self.node = None
        self.work: Optional[Path] = None
        self.steps: List[str] = []

    def start(self, workspace: Path, files: Dict[str, str]) -> Dict[str, Any]:
        from backend.chaos.models import AssessmentConfig, Target
        from backend.chaos.sandbox import Sandbox, SandboxError
        from backend.execution.docker_test_sandbox import docker_available
        from backend.execution.preview_manager import backend_entry, backend_problem
        if not docker_available():
            raise RuntimeBlocked("Docker is not available: the integration tests could not run (nothing was executed)")
        if backend_entry(workspace) is None:
            raise AppFailed(f"the integrated backend is not runnable: {backend_problem(workspace)}")
        self.sandbox = Sandbox(workspace, AssessmentConfig(scenarios=["contract"]), label="swarm")
        self.files = files
        try:
            self.steps += self.sandbox.setup()
        except SandboxError as e:
            raise AppFailed(str(e), self.sandbox.app_logs() if self.sandbox.started_at else "")
        if self.sandbox.wait_healthy(Target(method="GET", path="/openapi.json"), self.start_budget_s) is None:
            raise AppFailed(f"the backend did not answer /openapi.json within {self.start_budget_s:.0f}s", self.sandbox.app_logs())
        self.steps.append("the backend answered /openapi.json")
        self.node = self.sandbox.probe_c.replace("_probe_", "_node_")
        self.image = NODE_IMAGE
        return {"environment": self.environment, "steps": list(self.steps), "sandbox_id": self.sandbox.id}

    def execute(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        from backend.chaos.sandbox import DEP_LIMITS, _docker
        if self.work:
            shutil.rmtree(self.work, ignore_errors=True)
        self.work = prepare_workdir(self.files, {**plan, "root": "/work"})
        _docker("rm", "-f", self.node, timeout=60)
        args = ["run", "--rm", "--name", self.node, *self.sandbox.labels, "--network", self.sandbox.network,
                *DEP_LIMITS, "--tmpfs", "/tmp:rw,size=64m", "-e", "HOME=/tmp", "-v", f"{self.work}:/work:ro",
                self.image, "timeout", str(int(self.exec_timeout_s)), "node", "/work/harness.mjs", "/work/plan.json"]
        try:
            res = _docker(*args, timeout=self.exec_timeout_s + 30)
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"the contract harness exceeded {self.exec_timeout_s:.0f}s")
        if res.returncode == 124:
            raise TimeoutError(f"the contract harness exceeded {self.exec_timeout_s:.0f}s")
        try:
            return parse_output(res.stdout)
        except ValueError:
            raise RuntimeError("the contract harness failed: " + redact((res.stderr or res.stdout or "")[-800:]))

    def isolation(self) -> Dict[str, Any]:
        """Inspected from Docker itself, not assumed: the network is internal, the containers are hardened."""
        from backend.chaos.sandbox import _docker
        checks = []
        net = _docker("network", "inspect", "-f", "{{.Internal}}", self.sandbox.network, timeout=30).stdout.strip()
        checks.append({"check": "mission network is internal (no route out)", "passed": net == "true", "observed": net})
        for name in (self.sandbox.app,):
            res = _docker("inspect", "-f", "{{json .HostConfig}}|{{json .Config.User}}", name, timeout=30)
            try:
                hc_text, user = res.stdout.strip().rsplit("|", 1)
                hc, user = json.loads(hc_text), json.loads(user)
            except ValueError:
                checks.append({"check": f"{name} is hardened", "passed": False, "observed": "could not inspect"})
                continue
            observed = {"privileged": hc.get("Privileged"), "cap_drop": hc.get("CapDrop"), "read_only": hc.get("ReadonlyRootfs"),
                        "memory": hc.get("Memory"), "nano_cpus": hc.get("NanoCpus"), "pids_limit": hc.get("PidsLimit"),
                        "user": user, "security_opt": hc.get("SecurityOpt"), "port_bindings": hc.get("PortBindings")}
            ok = (not hc.get("Privileged") and "ALL" in (hc.get("CapDrop") or []) and hc.get("ReadonlyRootfs")
                  and (hc.get("Memory") or 0) > 0 and (hc.get("NanoCpus") or 0) > 0 and (hc.get("PidsLimit") or 0) > 0
                  and user not in ("", "root", "0") and not hc.get("PortBindings"))
            checks.append({"check": "backend container: unprivileged, capabilities dropped, read-only, limited, non-root, no host port",
                           "passed": bool(ok), "observed": observed})
        return {"verified": all(c["passed"] for c in checks), "checks": checks}

    def stop(self) -> Dict[str, Any]:
        from backend.chaos.sandbox import LABEL, _docker
        done: List[str] = []
        try:
            if self.sandbox is not None:
                done = self.sandbox.cleanup()
                left = _docker("ps", "-a", "-q", "--filter", f"label={LABEL}={self.sandbox.id}", timeout=30).stdout.split()
                nets = _docker("network", "ls", "-q", "--filter", f"name={self.sandbox.network}", timeout=30).stdout.split()
                return {"done": done, "leftover_containers": len(left), "leftover_networks": len(nets),
                        "verified": not left and not nets}
            return {"done": [], "verified": True}
        finally:
            if self.work:
                shutil.rmtree(self.work, ignore_errors=True)


def run_contract_tests(runtime, workspace: Path, files: Dict[str, str], contract: Dict[str, Any], routes: List[Dict[str, Any]],
                       exports: List[Dict[str, Any]], require_isolation: bool = True) -> Dict[str, Any]:
    """One integration-testing run: start, execute, re-execute failures once, inspect isolation, always clean up."""
    started = time.monotonic()
    plan = build_plan(contract, routes, exports, root="/work")
    run: Dict[str, Any] = {"status": "error", "environment": getattr(runtime, "environment", type(runtime).__name__),
                           "plan": {"direct": len(plan["direct"]), "client": len(plan["client"]), "hints": plan["hints"]},
                           "checks": [], "declared": {}, "egress": [], "isolation": {}, "cleanup": {}}
    try:
        info = runtime.start(workspace, files)
        run["steps"] = info.get("steps", [])
        run["sandbox_id"] = info.get("sandbox_id")
        raw = runtime.execute(plan)
        checks = evaluate(contract, plan, raw)
        if any(c["status"] == "failed" for c in checks):
            run["rerun"] = True
            checks = merge_rerun(checks, evaluate(contract, plan, runtime.execute(plan)))
        run["checks"] = checks
        run["declared"] = declared(raw.get("openapi"), contract)
        run["egress"] = raw.get("egress", [])
        run["harness"] = {"node": raw.get("node"), "version": raw.get("harness")}
        iso = runtime.isolation()
        reachable = [x["target"] for x in run["egress"] if x.get("reachable")]
        iso["checks"] = iso.get("checks", []) + [{"check": "no address outside the mission network is reachable from it",
                                                  "passed": bool(run["egress"]) and not reachable,
                                                  "observed": run["egress"]}]
        iso["verified"] = bool(iso.get("verified")) and not reachable
        run["isolation"] = iso
        run["status"] = "completed"
    except RuntimeBlocked as e:
        run.update(status="blocked", error=str(e))
    except AppFailed as e:
        run.update(status="app_failed", error=str(e), app_logs=redact(e.logs[-3000:]))
    except TimeoutError as e:
        run.update(status="timeout", error=str(e))
    except Exception as e:  # noqa: BLE001
        _logger.exception("contract tests failed")
        run.update(status="error", error=redact(f"{type(e).__name__}: {e}", 800))
    finally:
        try:
            run["cleanup"] = runtime.stop()
        except Exception as e:  # noqa: BLE001
            run["cleanup"] = {"verified": False, "error": redact(str(e), 300)}
        run["seconds"] = round(time.monotonic() - started, 1)
    counts: Dict[str, int] = {}
    for c in run["checks"]:
        counts[c["status"]] = counts.get(c["status"], 0) + 1
    run["counts"] = counts
    return run
