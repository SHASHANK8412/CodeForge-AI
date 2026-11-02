"""
Safe verification: benign, bounded HTTP requests against a disposable copy of the app, inside the
Chaos Engineer's isolated sandbox (internal Docker network, hardened non-root container, limits; the
requests come from a probe container on that network). Nothing is sent to the user's real systems or
to any third party, and nothing destructive is attempted beyond the disposable copy itself.

Each verifier states its method and what counts as proof. A finding becomes "verified" only when the
response shows the issue; otherwise "not_reproduced" (or "unavailable" when the test cannot run).
Response bodies are stored redacted and truncated.
"""

import json
import re
from pathlib import Path
from typing import Any, Callable, Dict, List

from backend.evolution.autopilot.models import now_iso
from backend.evolution.autopilot.redact import redact
from backend.guardian.models import Finding, Verification

PROBE_REQUEST = r'''
import json, sys, urllib.request, urllib.error, urllib.parse
spec = json.loads(sys.argv[1])
url = spec["base"] + spec["path"]
if spec.get("params"):
    url += "?" + urllib.parse.urlencode(spec["params"])
data = json.dumps(spec["body"]).encode() if spec.get("body") is not None else None
headers = dict(spec.get("headers") or {})
if data is not None:
    headers["Content-Type"] = "application/json"
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None
opener = urllib.request.build_opener(NoRedirect)
req = urllib.request.Request(url, data=data, method=spec["method"], headers=headers)
try:
    r = opener.open(req, timeout=10)
    out = {"status": r.status, "headers": dict(r.headers), "body": r.read(8000).decode("utf-8", "replace")}
except urllib.error.HTTPError as e:
    out = {"status": e.code, "headers": dict(e.headers), "body": e.read(8000).decode("utf-8", "replace")}
except Exception as e:
    out = {"status": None, "headers": {}, "body": "", "error": type(e).__name__ + ": " + str(e)[:200]}
print(json.dumps(out))
'''
SQL_ERRORS = re.compile(r"sqlite3\.|OperationalError|syntax error|SQL syntax|unterminated quoted|psycopg2|ProgrammingError|"
                        r"near \".*\": syntax", re.I)
MARK = "aiforge_probe_no_match_7341"
METHODS_WITH_BODY = ("POST", "PUT", "PATCH")


def _fill(path: str) -> str:
    return re.sub(r"\{[^}]+\}", "1", path)


class Prober:
    """Sends one request from the probe container and keeps a redacted record of it."""

    def __init__(self, sandbox, record: List[Dict[str, Any]]):
        self.sb, self.record = sandbox, record

    def send(self, method: str, path: str, params=None, headers=None, body=None, purpose: str = "") -> Dict[str, Any]:
        from backend.chaos.sandbox import _docker
        spec = {"base": self.sb.app_url, "method": method, "path": path, "params": params, "headers": headers, "body": body}
        res = _docker("exec", self.sb.probe_c, "python", "-c", PROBE_REQUEST, json.dumps(spec), timeout=40)
        try:
            out = json.loads((res.stdout or "").strip().splitlines()[-1])
        except (ValueError, IndexError):
            out = {"status": None, "headers": {}, "body": "", "error": (res.stderr or "probe failed")[-200:]}
        self.record.append({"purpose": purpose, "request": {"method": method, "path": path, "params": params,
                                                            "headers": headers, "body": body},
                            "status": out.get("status"), "error": out.get("error"),
                            "headers": {k: v for k, v in (out.get("headers") or {}).items()
                                        if k.lower().startswith(("access-control", "location", "content-type", "set-cookie"))},
                            "body": redact(out.get("body", ""))[:600]})
        return out


def _json(out) -> Any:
    try:
        return json.loads(out.get("body") or "")
    except ValueError:
        return None


def _size(data) -> int:
    return len(data) if isinstance(data, (list, dict)) else (0 if data is None else 1)


def _keys(data, found=None) -> set:
    found = set() if found is None else found
    if isinstance(data, dict):
        for k, v in data.items():
            if v not in (None, "", [], {}):
                found.add(str(k).lower())
            _keys(v, found)
    elif isinstance(data, list):
        for x in data[:50]:
            _keys(x, found)
    return found


# --- verifiers ---------------------------------------------------------------------------------------

def v_sql_injection(p: Prober, f: Finding, v: Verification) -> None:
    method, path = f.route.split(" ", 1)
    params = [x for x in f.context.get("params", []) if "{" + x + "}" not in path]
    if not params:
        v.status, v.conclusion = "unavailable", "no query parameter to send the probe in"
        return
    q = params[0]
    v.method = (f"GET {path}?{q}=<value>: a non-matching value, a single quote, and a tautology "
                f"(\"{MARK}' OR '1'='1\"). Proof: an SQL error in the answer, or the tautology returning more results "
                "than the non-matching value.")
    base = p.send("GET", _fill(path), {q: MARK}, purpose="baseline (non-matching value)")
    quote = p.send("GET", _fill(path), {q: "'"}, purpose="single quote")
    taut = p.send("GET", _fill(path), {q: f"{MARK}' OR '1'='1"}, purpose="tautology")
    sql_error = bool(SQL_ERRORS.search(quote.get("body", "")) or SQL_ERRORS.search(taut.get("body", "")))
    more_rows = taut.get("status") and taut["status"] < 400 and _size(_json(taut)) > _size(_json(base))
    if more_rows or sql_error:
        v.status = "verified"
        v.conclusion = ("the tautology returned " + f"{_size(_json(taut))} result(s) vs {_size(_json(base))} for a non-matching "
                        "value, so the input changed the query logic" if more_rows else
                        "a quote in the input produced a database error in the response")
    else:
        v.status = "not_reproduced"
        v.conclusion = (f"no SQL error and no extra results (statuses: base {base.get('status')}, quote {quote.get('status')}, "
                        f"tautology {taut.get('status')})")
        if quote.get("status") == 500:
            v.limitations.append("the quote caused a 500 without database error text: suspicious but not proof")


def v_missing_auth(p: Prober, f: Finding, v: Verification) -> None:
    method, path = f.route.split(" ", 1)
    v.method = f"{method} {_fill(path)} without any credentials. Proof: a successful (2xx/3xx) answer."
    v.limitations.append("runs against the disposable copy only; a state-changing request may change its throwaway data")
    out = p.send(method, _fill(path), body={} if method in METHODS_WITH_BODY else None, purpose="request without credentials")
    st = out.get("status")
    if st in (401, 403):
        v.status, v.conclusion = "not_reproduced", f"refused with {st}: authentication is enforced"
    elif st is None or st >= 400:
        # 404 can mean the route was not matched, 422 can come from an auth dependency's missing header
        v.status, v.conclusion = "not_reproduced", f"no successful answer ({st or out.get('error')}); authentication not proven missing"
        if st in (404, 422):
            v.limitations.append(f"{st} does not show whether an authentication check would have run")
    else:
        v.status, v.conclusion = "verified", f"answered {st} without credentials"


def v_sensitive_exposure(p: Prober, f: Finding, v: Verification) -> None:
    method, path = f.route.split(" ", 1)
    wanted = set(f.context.get("sensitive_keys") or [])
    v.method = f"GET {_fill(path)}. Proof: response keys among {sorted(wanted)} with non-empty values (values are not stored)."
    out = p.send("GET", _fill(path), purpose="read the response")
    present = sorted(_keys(_json(out)) & wanted)
    if present:
        v.status, v.conclusion = "verified", f"the response contains {present} with values"
    else:
        v.status = "not_reproduced"
        v.conclusion = f"status {out.get('status')}; none of the sensitive keys appeared"
        if _size(_json(out)) == 0:
            v.limitations.append("the response was empty: with no data rows the exposure cannot be observed")


def v_path_traversal(p: Prober, f: Finding, v: Verification) -> None:
    method, path = f.route.split(" ", 1)
    params = [x for x in f.context.get("params", []) if "{" + x + "}" not in path]
    v.method = "GET with the file parameter set to '../../../../etc/passwd' (the sandbox container's own file). Proof: its contents in the answer."
    attempts = []
    if params:
        attempts.append(("GET", _fill(path), {params[0]: "../../../../../../etc/passwd"}))
    for x in [x for x in f.context.get("params", []) if "{" + x + "}" in path]:
        attempts.append(("GET", path.replace("{" + x + "}", "..%2F..%2F..%2F..%2F..%2Fetc%2Fpasswd"), None))
    if not attempts:
        v.status, v.conclusion = "unavailable", "no parameter to send the path in"
        return
    for m, pth, params_ in attempts:
        out = p.send(m, re.sub(r"\{[^}]+\}", "1", pth), params_, purpose="traversal attempt")
        if "root:x:0:0" in out.get("body", "") or re.search(r"^root:.*:0:0:", out.get("body", ""), re.M):
            v.status, v.conclusion = "verified", "the answer contained /etc/passwd from outside the intended folder"
            return
    v.status, v.conclusion = "not_reproduced", "no file content from outside the folder was returned"


def v_cors(p: Prober, f: Finding, v: Verification) -> None:
    v.method = ("OPTIONS / with Origin: http://evil.example (a name that resolves nowhere; nothing is contacted). "
                "Proof: the origin (or *) allowed together with credentials.")
    out = p.send("OPTIONS", "/", headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "GET"},
                 purpose="CORS preflight from a foreign origin")
    h = {k.lower(): v for k, v in (out.get("headers") or {}).items()}
    allow, creds = h.get("access-control-allow-origin"), h.get("access-control-allow-credentials", "").lower() == "true"
    if allow in ("http://evil.example", "*") and creds:
        v.status, v.conclusion = "verified", f"Access-Control-Allow-Origin: {allow} with Allow-Credentials: true"
    elif allow in ("http://evil.example", "*"):
        v.status, v.conclusion = "verified", f"any origin is allowed (Access-Control-Allow-Origin: {allow}), without credentials"
    else:
        v.status, v.conclusion = "not_reproduced", f"foreign origin not allowed (header: {allow})"


def v_open_redirect(p: Prober, f: Finding, v: Verification) -> None:
    method, path = f.route.split(" ", 1)
    params = [x for x in f.context.get("params", []) if "{" + x + "}" not in path]
    if not params:
        v.status, v.conclusion = "unavailable", "no parameter for the target URL"
        return
    v.method = f"GET {path}?{params[0]}=https://example.invalid/ (redirects are not followed). Proof: a 3xx to that URL."
    out = p.send("GET", _fill(path), {params[0]: "https://example.invalid/"}, purpose="redirect target from the request")
    loc = {k.lower(): v for k, v in (out.get("headers") or {}).items()}.get("location", "")
    if out.get("status") and 300 <= out["status"] < 400 and loc.startswith("https://example.invalid"):
        v.status, v.conclusion = "verified", f"redirected ({out['status']}) to {loc}"
    else:
        v.status, v.conclusion = "not_reproduced", f"status {out.get('status')}, Location {loc or 'none'}"


VERIFIERS: Dict[str, Callable[[Prober, Finding, Verification], None]] = {
    "sql_injection": v_sql_injection, "missing_auth": v_missing_auth, "sensitive_exposure": v_sensitive_exposure,
    "path_traversal": v_path_traversal, "cors": v_cors, "open_redirect": v_open_redirect,
}


def verify(project: Path, findings: List[Finding], should_stop: Callable[[], bool],
           on_event: Callable[[str], None] = lambda s: None) -> Dict[str, Verification]:
    """Run the safe verification of each finding in one disposable sandbox. Always cleans up."""
    from backend.chaos.models import AssessmentConfig, Limits, Target
    from backend.chaos.sandbox import Sandbox, SandboxError
    results: Dict[str, Verification] = {}
    todo = [f for f in findings if f.verifiable in VERIFIERS and (f.route or f.verifiable == "cors")]
    for f in findings:
        if f not in todo:
            results[f.id] = Verification(method="-", status="unavailable", started_at=now_iso(), finished_at=now_iso(),
                                         conclusion="no safe automated verification exists for this finding",
                                         limitations=[f.context.get("verification_note", "")] if f.context.get("verification_note") else [])
    if not todo:
        return results
    sb = Sandbox(Path(project), AssessmentConfig(scenarios=["app_restart"], limits=Limits()), "guardian")
    try:
        on_event("creating the isolated sandbox")
        sb.setup()
        if sb.wait_healthy(Target(path="/health"), 60) is None and sb.wait_healthy(Target(path="/docs"), 20) is None:
            raise SandboxError("the app did not start in the sandbox; nothing was verified")
        for f in todo:
            if should_stop():
                break
            v = Verification(method="", status="running", started_at=now_iso(),
                             preconditions=["disposable copy running in an isolated sandbox", "app answered its health check"])
            on_event(f"verifying {f.id} ({f.verifiable})")
            try:
                VERIFIERS[f.verifiable](Prober(sb, v.requests), f, v)
            except Exception as e:  # noqa: BLE001 - recorded on the verification
                v.status, v.conclusion = "error", redact(f"{type(e).__name__}: {e}", 300)
            v.finished_at = now_iso()
            results[f.id] = v
        for f in todo:
            if f.id not in results:
                results[f.id] = Verification(method="-", status="aborted", conclusion="aborted before this finding was verified")
    except SandboxError as e:
        for f in todo:
            results.setdefault(f.id, Verification(method="-", status="unavailable", conclusion=redact(str(e), 300)))
    finally:
        on_event("removing the sandbox: " + "; ".join(sb.cleanup()))
    return results


STATE_OF = {"verified": "verified", "not_reproduced": "not_reproduced", "unavailable": "verification_unavailable",
            "error": "verification_unavailable", "aborted": "detected"}
