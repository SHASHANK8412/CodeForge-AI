"""
Evidence-based failure classification. Runtime checks (runtime.py) and code extraction (interfaces.py) become
structured findings:

  basis runtime   a check executed against the integrated backend / client in the isolated environment.
                  'verified' when the responsible component follows from the evidence:
                    - a request built from the contract got a non-conforming answer      -> backend
                    - invalid input the contract forbids was accepted / crashed          -> backend
                    - the client sent something the contract does not allow              -> frontend
                    - the client threw on a conforming response                          -> frontend
                  otherwise 'unresolved' (insufficient evidence, flaky, both sides involved).
  basis static    read from the code (AST / fetch parsing): 'unverified' until a runtime check confirms it.
  basis declared  the app's own /openapi.json: 'unverified' as well.

Nothing an agent says about its own output is used. Severity is fixed per category, not estimated.
"""

import uuid
from typing import Any, Dict, List, Optional

from backend.swarm import schemas
from backend.swarm.interfaces import _norm
from backend.swarm.models import Finding

SEVERITY = {"request_contract_mismatch": "high", "response_schema_mismatch": "high", "http_status_mismatch": "high",
            "frontend_integration_error": "high", "backend_runtime_error": "high", "auth_mismatch": "critical",
            "security_violation": "critical", "test_infrastructure_failure": "medium", "insufficient_evidence": "medium"}
CORRECTION = {
    ("request_contract_mismatch", "frontend"): "send exactly the contract's method, path, parameters and request body",
    ("request_contract_mismatch", "backend"): "validate requests exactly as the contract's request schema says (reject what it forbids)",
    ("response_schema_mismatch", "backend"): "return the contract's response body schema and content type",
    ("http_status_mismatch", "backend"): "return the contract's status codes (status_code= on the route, documented errors)",
    ("frontend_integration_error", "frontend"): "handle the contract's response as specified (fields, types, status codes)",
    ("backend_runtime_error", "backend"): "fix the server error shown in the evidence",
    ("auth_mismatch", "backend"): "require the contract's authentication on this operation",
    ("auth_mismatch", "frontend"): "send the Authorization header the contract requires",
}


def _new(mission_id: str, round_no: int, **kw) -> Finding:
    cat = kw["category"]
    resp = kw.get("responsible")
    kw.setdefault("severity", SEVERITY.get(cat, "medium"))
    kw.setdefault("recommended_correction", CORRECTION.get((cat, resp or ""), "a person reviews the evidence and decides"))
    return Finding(id="fd_" + uuid.uuid4().hex[:10], mission_id=mission_id, round=round_no, **kw)


def from_runtime(mission_id: str, round_no: int, run: Dict[str, Any], artifacts: Dict[str, Optional[str]]) -> List[Finding]:
    out: List[Finding] = []
    ev_base = {"runtime_run": run.get("id"), "environment": run.get("environment"), **{k: v for k, v in artifacts.items() if v}}
    status = run.get("status")
    if status in ("blocked", "timeout", "error"):
        out.append(_new(mission_id, round_no, key=f"test_infrastructure_failure|integration|{status}", endpoint="integration tests",
                        component="infrastructure", category="test_infrastructure_failure",
                        expected="the integration tests run in the isolated environment", observed=run.get("error") or status,
                        evidence={**ev_base, "cleanup": run.get("cleanup")}, basis="runtime", responsible=None,
                        confidence="high", status="blocked",
                        recommended_correction="make the isolated environment available (e.g. start Docker) and resume the mission"))
        return out
    if status == "app_failed":
        install = "dependency install failed" in (run.get("error") or "")
        out.append(_new(mission_id, round_no, key="backend_runtime_error|backend|startup", endpoint="backend startup", component="backend",
                        category="test_infrastructure_failure" if install else "backend_runtime_error",
                        expected="the integrated backend starts and serves /openapi.json", observed=run.get("error") or "did not start",
                        evidence={**ev_base, "app_logs": (run.get("app_logs") or "")[-1500:]}, basis="runtime",
                        responsible=None if install else "backend", confidence="high",
                        status="unresolved" if install else "verified"))
        return out
    for c in run.get("checks", []):
        if c["status"] == "passed":
            continue
        evidence = {**ev_base, "check": c["id"], "request": c.get("request"), "response": c.get("response"),
                    "client_requests": c.get("requests"), "static_call": c.get("static_call"), "rerun": c.get("rerun")}
        evidence = {k: v for k, v in evidence.items() if v is not None}
        where = c.get("export") or c["kind"]
        if c["status"] == "blocked":
            out.append(_new(mission_id, round_no, key=f"test_infrastructure_failure|{c['endpoint']}|{where}", endpoint=c["endpoint"],
                            component="infrastructure", category="test_infrastructure_failure", expected=c["expected"],
                            observed=c["observed"], evidence=evidence, basis="runtime", confidence="high", status="blocked"))
            continue
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for p in c.get("problems") or []:
            groups.setdefault(p["category"], []).append(p)
        for cat, problems in groups.items():
            responsible = problems[0].get("responsible", "backend" if c["source"] == "contract_test" else None)
            observed = "; ".join(p["detail"] for p in problems)
            flaky = c["status"] == "flaky"
            if flaky:
                observed += " (failed, then passed when re-run in the same environment: flaky)"
            settled = responsible and not flaky and cat != "insufficient_evidence"
            out.append(_new(mission_id, round_no, key=f"{cat}|{c['endpoint']}|{where}", endpoint=c["endpoint"],
                            component="frontend" if c["source"] == "frontend_client" else "backend", category=cat,
                            severity="low" if cat == "insufficient_evidence" else SEVERITY.get(cat, "medium"),
                            expected=c["expected"], observed=observed, evidence=evidence, basis="runtime",
                            responsible=responsible if settled else None,
                            confidence="high" if settled else "low",
                            status="verified" if settled else "unresolved"))
    return out


def from_static(mission_id: str, round_no: int, contract: Dict[str, Any], routes: List[Dict[str, Any]],
                matched_calls: List[Dict[str, Any]], artifacts: Dict[str, Optional[str]]) -> List[Finding]:
    """Read from the code; never 'verified' on their own (a runtime check decides)."""
    out: List[Finding] = []
    ev = {k: v for k, v in artifacts.items() if v}
    for e in contract["endpoints"]:
        key = f"{e['method'].upper()} {e['path']}"
        r = next((x for x in routes if x["method"] == e["method"].upper() and _norm(x["path"]) == _norm(e["path"])), None)
        if r is None:
            out.append(_new(mission_id, round_no, key=f"request_contract_mismatch|{key}|static_route", endpoint=key, component="backend",
                            category="request_contract_mismatch", expected=f"a {key} route", observed="no such route in the backend code",
                            evidence=ev, basis="static", responsible="backend", status="unverified", confidence="medium"))
            continue
        if r.get("status_code_explicit") and str(r["status_code"]) not in (e.get("responses") or {}):
            out.append(_new(mission_id, round_no, key=f"http_status_mismatch|{key}|static_status", endpoint=key, component="backend",
                            category="http_status_mismatch", expected=f"status {sorted(e.get('responses') or {})}",
                            observed=f"status_code={r['status_code']} ({r['file']}:{r['line']})", evidence=ev, basis="static",
                            responsible="backend", status="unverified"))
        if e.get("auth") == "bearer" and r.get("auth") != "bearer":
            out.append(_new(mission_id, round_no, key=f"auth_mismatch|{key}|static_auth", endpoint=key, component="backend",
                            category="auth_mismatch", expected="an authentication dependency", observed="none found in the route",
                            evidence=ev, basis="static", responsible="backend", status="unverified"))
        for d in schemas.schema_diff(r.get("request_schema") or {}, e.get("request_schema") or {}):
            out.append(_new(mission_id, round_no, key=f"request_contract_mismatch|{key}|static_body", endpoint=key, component="backend",
                            category="request_contract_mismatch", expected="the contract's request schema",
                            observed=f"request model: {d} ({r['file']}:{r['line']})", evidence=ev, basis="static",
                            responsible="backend", status="unverified"))
            break
    for c in matched_calls:
        if c["status"] == "mismatch":
            out.append(_new(mission_id, round_no, key=f"request_contract_mismatch|{c['method']} {c['path']}|static_call",
                            endpoint=f"{c['method']} {c['path']}", component="frontend", category="request_contract_mismatch",
                            expected="a call that matches a backend route", observed=f"{c['reason']} ({c['file']}:{c['line']})",
                            evidence=ev, basis="static", status="unverified"))
        elif c["status"] == "unresolved":
            out.append(_new(mission_id, round_no, key=f"insufficient_evidence|{c['file']}:{c['line']}|static_call",
                            endpoint=f"{c['file']}:{c['line']}", component="frontend", category="insufficient_evidence",
                            severity="low", expected="a URL that can be read", observed=c.get("reason", "dynamic URL"),
                            evidence=ev, basis="static", status="unverified"))
    return out


def from_declared(mission_id: str, round_no: int, contract: Dict[str, Any], declared: Dict[str, Any], run_id: Optional[str]) -> List[Finding]:
    out = []
    for e in contract["endpoints"]:
        key = f"{e['method'].upper()} {e['path']}"
        d = declared.get(key)
        if d is None:
            continue
        if not d.get("present"):
            out.append(_new(mission_id, round_no, key=f"request_contract_mismatch|{key}|declared", endpoint=key, component="backend",
                            category="request_contract_mismatch", expected=f"{key} in the app's OpenAPI document",
                            observed="not declared", evidence={"runtime_run": run_id}, basis="declared", status="unverified"))
            continue
        missing = sorted(set(k for k in (e.get("responses") or {})) - set(d.get("statuses") or []))
        if missing:
            out.append(_new(mission_id, round_no, key=f"http_status_mismatch|{key}|declared", endpoint=key, component="backend",
                            category="http_status_mismatch", expected=f"declared success status {missing}",
                            observed=f"declared statuses {d.get('statuses')}", evidence={"runtime_run": run_id},
                            basis="declared", status="unverified"))
    return out


def properties(contract: Dict[str, Any], routes: List[Dict[str, Any]], declared: Dict[str, Any], checks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Per operation: what the contract says, what the code says (static), what OpenAPI says (declared) and what was
    observed (verified). The runtime observation decides when it exists."""
    out = {}
    for e in contract["endpoints"]:
        key = f"{e['method'].upper()} {e['path']}"
        r = next((x for x in routes if x["method"] == e["method"].upper() and _norm(x["path"]) == _norm(e["path"])), None) or {}
        d = declared.get(key) or {}
        valid = next((c for c in checks if c["endpoint"] == key and c["kind"] == "valid"), None)
        unauth = next((c for c in checks if c["endpoint"] == key and c["kind"] == "unauthenticated"), None)
        invalid = [c for c in checks if c["endpoint"] == key and c["kind"] in ("missing_required_field", "malformed_body",
                                                                               "invalid_path_param", "missing_query_param")]
        client = [c for c in checks if c["endpoint"] == key and c["source"] == "frontend_client"]
        observed_status = ((valid or {}).get("response") or {}).get("status")
        out[key] = {
            "success_status": {"contract": sorted(e.get("responses") or {}), "static": r.get("status_code"),
                               "declared": d.get("statuses"), "verified": observed_status,
                               "decided_by": "runtime" if observed_status is not None else "static" if r else "unknown"},
            "response_body": {"contract": "schema" if any((v or {}).get("schema") for v in (e.get("responses") or {}).values()) else "none",
                              "static": "response_model" if r.get("response_schema") else "untyped" if r else None,
                              "verified": (valid or {}).get("status"), "decided_by": "runtime" if valid else "static"},
            "request_validation": {"contract": (e.get("request_schema") or {}).get("required"), "static": r.get("required_fields"),
                                   "verified": [f"{c['kind']}: {c['status']}" for c in invalid] or None,
                                   "decided_by": "runtime" if invalid else "static"},
            "auth": {"contract": e.get("auth"), "static": r.get("auth"), "declared": d.get("auth"),
                     "verified": (unauth or {}).get("status"), "decided_by": "runtime" if unauth else "static"},
            "frontend_client": {"verified": [f"{c.get('export')}: {c['status']}" for c in client] or None,
                                "decided_by": "runtime" if client else "unknown"},
        }
    return out
