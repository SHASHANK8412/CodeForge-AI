"""
AIForge Security Guardian tests. The sample (sample_project.py) is a small FastAPI app with planted
vulnerabilities and one properly protected route. Advisory lookups are replaced by offline stubs except
where the lookup arguments themselves are tested; the Docker tests at the end run the genuine pipeline.
"""

import json
import subprocess

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import backend.guardian.scanners as scanners
import backend.guardian.service as gs
from backend.evolution.autopilot.service import AutopilotService
from backend.evolution.autopilot.store import AutopilotStore
from backend.guardian import correlate, regression, verify as gv
from backend.guardian.models import Finding, ToolRun, Verification
from backend.guardian.service import GuardianError, GuardianStore, SecurityGuardian
from tests.guardian.sample_project import write_sample

SECRET_VALUE = "super-secret-signing-key-123"


@pytest.fixture
def offline(monkeypatch):
    monkeypatch.setattr(scanners, "pip_audit", lambda p: ([], ToolRun(tool="pip-audit", status="unavailable",
                                                                      detail="advisory data could not be retrieved (offline test)")))
    monkeypatch.setattr(scanners, "npm_audit", lambda p: ([], ToolRun(tool="npm audit", status="skipped", detail="no package.json")))


@pytest.fixture
def sample(tmp_path):
    return write_sample(tmp_path / "users_app")


@pytest.fixture
def guardian(tmp_path, offline, monkeypatch):
    ap = AutopilotService(AutopilotStore(tmp_path / "ap"), background=False)
    sg = SecurityGuardian(GuardianStore(tmp_path / "g"), autopilot=ap, background=False)
    monkeypatch.setattr(gs, "global_security_guardian", sg)      # the Autopilot gate and other modules look it up
    return sg


def assessed(sg, project):
    a = sg.start("p1", project, "u1")
    return sg.store.get("p1", "assessments", a.id), {f.rule_id + " " + (f.route or ""): f for f in sg.store.list("p1", "findings")}


class FakeProber:
    """Stands in for the probe container: answers from a function, keeps the same request record."""

    def __init__(self, answer):
        self.answer, self.sent = answer, []

    def send(self, method, path, params=None, headers=None, body=None, purpose=""):
        self.sent.append((method, path, params, headers))
        return self.answer(method, path, params or {}, headers or {})


def finding(**kw):
    base = dict(id="sg_x", project_id="p1", rule_id="PY-SQLI", category="injection", title="t", description="d", severity="high",
                confidence="high", file="backend/main.py", line=1)
    base.update(kw)
    return Finding(**base)


# 1 detection, evidence and categories -----------------------------------------------------------------------
def test_planted_vulnerabilities_are_detected_with_evidence(guardian, sample):
    a, by = assessed(guardian, sample)
    assert a.status == "completed", a.error
    sqli = by["PY-SQLI GET /api/users/search"]
    assert sqli.severity == "high" and sqli.line == 46 and sqli.context["params"] == ["name"]
    assert any("SELECT id, name, email FROM users WHERE name" in e.detail for e in sqli.evidence)
    assert by["PY-SENSITIVE-RESPONSE GET /api/users"].context["sensitive_keys"] == ["password_hash"]
    assert by["PY-MISSING-AUTH DELETE /api/users/{user_id}"].confidence == "high"
    assert {"PY-CORS ", "PY-WEAK-HASH ", "PY-HARDCODED-KEY ", "DEP-UNPINNED "} <= set(by)
    assert {f.category for f in by.values()} >= {"injection", "auth", "secrets", "web", "crypto", "dependencies"}
    for f in by.values():
        assert f.evidence and f.remediation and f.impact is not None and f.priority in ("P1", "P2", "P3", "P4")


def test_a_properly_protected_route_is_not_reported(guardian, sample):
    a, by = assessed(guardian, sample)
    assert not any(f.route == "POST /api/admin/reset" for f in by.values())
    assert a.coverage["auth"]["protected_routes"] == ["POST /api/admin/reset"]


def test_a_parameterized_query_is_not_reported(guardian, sample):
    main = sample / "backend" / "main.py"
    main.write_text(main.read_text(encoding="utf-8").replace(
        "f\"SELECT id, name, email FROM users WHERE name = '{name}'\"", '"SELECT id, name, email FROM users WHERE name = ?", (name,)'),
        encoding="utf-8")
    _, by = assessed(guardian, sample)
    assert not any(k.startswith("PY-SQLI") for k in by)


# 2 deduplication -------------------------------------------------------------------------------------------------
def test_results_from_several_tools_become_one_finding(guardian, sample):
    _, by = assessed(guardian, sample)
    key = [f for f in by.values() if f.line == 9]
    assert len(key) == 1 and sorted(key[0].detection) == ["bandit", "guardian-ast", "secret-scanner"]
    assert sorted(by["PY-SQLI GET /api/users/search"].detection) == ["bandit", "guardian-ast"]


# 3 states: a rule match is never "verified" ----------------------------------------------------------------------
def test_static_matches_are_never_verified_or_fixed(guardian, sample):
    _, by = assessed(guardian, sample)
    assert {f.state for f in by.values()} <= {"detected", "requires_review"}
    assert by["PY-MISSING-AUTH GET /api/users"].state == "requires_review"     # a read route: design decision


# 4 secrets are redacted everywhere ---------------------------------------------------------------------------------
def test_secret_values_never_appear_in_findings_audit_or_reports(guardian, sample):
    a, by = assessed(guardian, sample)
    stored = json.dumps([f.model_dump(mode="json") for f in by.values()]) + json.dumps(a.model_dump(mode="json"))
    assert SECRET_VALUE not in stored
    assert SECRET_VALUE not in guardian.report("p1", "markdown")
    assert SECRET_VALUE not in json.dumps(guardian.report("p1", "json"))


# 5 honesty about coverage --------------------------------------------------------------------------------------------
def test_unavailable_tools_are_reported_and_never_treated_as_clean(guardian, sample):
    a, _ = assessed(guardian, sample)
    assert a.coverage["tools"]["pip-audit"] == "unavailable"
    assert any(x.startswith("pip-audit:") and "could not be retrieved" in x for x in a.coverage["not_covered"])
    md = guardian.report("p1", "markdown")
    assert "does not mean the project is secure" in md and "pip-audit: unavailable" in md
    assert "CVSS" not in md.replace("No CVSS", "")


def test_dependency_lookup_sends_only_pins_and_installs_nothing(tmp_path, monkeypatch):
    (tmp_path / "requirements.txt").write_text(
        "fastapi==0.109.0\nhttpx>=0.20\n--index-url https://user:pw@private.example/simple\ngit+https://x.example/y.git\n",
        encoding="utf-8")
    calls = []

    def run(cmd, **kw):
        if "--version" in cmd:
            return subprocess.CompletedProcess(cmd, 0, "pip-audit 2.10.1", "")
        calls.append((cmd, open(cmd[cmd.index("-r") + 1], encoding="utf-8").read()))
        out = {"dependencies": [{"name": "fastapi", "version": "0.109.0", "vulns": [
            {"id": "PYSEC-2024-38", "fix_versions": ["0.109.1"], "aliases": ["CVE-2024-24762"]},
            {"id": "PYSEC-2024-38", "fix_versions": ["0.109.1"], "aliases": ["CVE-2024-24762"]}]}]}
        return subprocess.CompletedProcess(cmd, 1, json.dumps(out), "")
    monkeypatch.setattr(scanners.subprocess, "run", run)
    found, tool = scanners.pip_audit(tmp_path)
    cmd, sent = calls[0]
    assert "--disable-pip" in cmd and "--no-deps" in cmd and sent == "fastapi==0.109.0\n"
    assert len(found) == 1 and found[0]["references"] == ["PYSEC-2024-38", "CVE-2024-24762"]     # de-duplicated
    assert tool.status == "partial" and "NOT checked" in tool.detail and "pw" not in tool.detail and tool.retrieved_at


def test_a_failed_advisory_lookup_is_an_error_not_a_clean_result(tmp_path, monkeypatch):
    (tmp_path / "requirements.txt").write_text("fastapi==0.109.0\n", encoding="utf-8")
    monkeypatch.setattr(scanners.subprocess, "run", lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, "", "ConnectionError: offline"))
    found, tool = scanners.pip_audit(tmp_path)
    assert found == [] and tool.status == "error" and "NOT checked" in tool.detail


# 6 safe verification ------------------------------------------------------------------------------------------------------
def test_verification_needs_explicit_approval_and_known_findings(guardian, sample):
    _, by = assessed(guardian, sample)
    fid = by["PY-SQLI GET /api/users/search"].id
    with pytest.raises(GuardianError):
        guardian.start_verification("p1", sample, "u1", [fid], approved=False)
    with pytest.raises(GuardianError):
        guardian.start_verification("p1", sample, "u1", ["sg_unknown"], approved=True)
    assert guardian.store.get("p1", "findings", fid).state == "detected"


def test_sql_injection_is_verified_only_by_observed_behaviour():
    f = finding(route="GET /api/users/search", verifiable="sql_injection", context={"params": ["name"]})
    rows = lambda n: {"status": 200, "headers": {}, "body": json.dumps([{"id": i} for i in range(n)])}  # noqa: E731
    v = Verification(method="")
    gv.v_sql_injection(FakeProber(lambda m, p, q, h: rows(3 if "OR" in q["name"] else 0)), f, v)
    assert v.status == "verified" and "3 result(s) vs 0" in v.conclusion
    v = Verification(method="")
    gv.v_sql_injection(FakeProber(lambda m, p, q, h: rows(0)), f, v)
    assert v.status == "not_reproduced"
    v = Verification(method="")
    gv.v_sql_injection(FakeProber(lambda m, p, q, h: {"status": 500, "headers": {}, "body": "Internal Server Error"}), f, v)
    assert v.status == "not_reproduced" and v.limitations          # a bare 500 is suspicious, not proof


def test_missing_authentication_is_verified_only_by_a_successful_answer():
    f = finding(rule_id="PY-MISSING-AUTH", category="auth", route="DELETE /api/users/{user_id}", verifiable="missing_auth")
    for status, expected in ((200, "verified"), (401, "not_reproduced"), (403, "not_reproduced"),
                             (404, "not_reproduced"), (422, "not_reproduced"), (500, "not_reproduced")):
        v = Verification(method="")
        p = FakeProber(lambda m, pth, q, h, s=status: {"status": s, "headers": {}, "body": "{}"})
        gv.v_missing_auth(p, f, v)
        assert v.status == expected, status
        assert p.sent == [("DELETE", "/api/users/1", None, None)]


def test_cors_and_sensitive_exposure_verifiers():
    v = Verification(method="")
    gv.v_cors(FakeProber(lambda m, p, q, h: {"status": 200, "body": "", "headers": {
        "access-control-allow-origin": "http://evil.example", "access-control-allow-credentials": "true"}}), finding(verifiable="cors"), v)
    assert v.status == "verified" and "Allow-Credentials" in v.conclusion
    v = Verification(method="")
    gv.v_cors(FakeProber(lambda m, p, q, h: {"status": 400, "body": "", "headers": {}}), finding(verifiable="cors"), v)
    assert v.status == "not_reproduced"
    f = finding(route="GET /api/users", verifiable="sensitive_exposure", context={"sensitive_keys": ["password_hash"]})
    v = Verification(method="")
    gv.v_sensitive_exposure(FakeProber(lambda m, p, q, h: {"status": 200, "headers": {}, "body": json.dumps([{"password_hash": "x"}])}), f, v)
    assert v.status == "verified"
    v = Verification(method="")
    gv.v_sensitive_exposure(FakeProber(lambda m, p, q, h: {"status": 200, "headers": {}, "body": "[]"}), f, v)
    assert v.status == "not_reproduced" and v.limitations


def test_without_a_sandbox_verification_is_unavailable_not_verified(guardian, sample, monkeypatch):
    from backend.chaos.sandbox import Sandbox, SandboxError

    def no_sandbox(self):
        raise SandboxError("Docker is not available")
    monkeypatch.setattr(Sandbox, "setup", no_sandbox)
    monkeypatch.setattr(Sandbox, "cleanup", lambda self: ["nothing to remove"])
    _, by = assessed(guardian, sample)
    ids = [by["PY-SQLI GET /api/users/search"].id, by["PY-WEAK-HASH "].id]
    job = guardian.start_verification("p1", sample, "u1", ids, approved=True)
    assert guardian.store.get("p1", "assessments", job.id).status == "completed"
    sqli, weak = (guardian.store.get("p1", "findings", i) for i in ids)
    assert sqli.state == "verification_unavailable" and "Docker" in sqli.verification.conclusion
    assert weak.state == "verification_unavailable" and "no safe automated verification" in weak.verification.conclusion


def test_a_crashed_verification_fails_the_job_and_keeps_the_findings(guardian, sample, monkeypatch):
    _, by = assessed(guardian, sample)
    fid = by["PY-SQLI GET /api/users/search"].id

    def boom(*a, **k):
        raise RuntimeError("sandbox exploded")
    monkeypatch.setattr(gs, "verify", boom)
    job = guardian.start_verification("p1", sample, "u1", [fid], approved=True)
    job = guardian.store.get("p1", "assessments", job.id)
    assert job.status == "failed" and "sandbox exploded" in job.error
    assert guardian.store.get("p1", "findings", fid).state == "detected"
    assert guardian.active_job("p1") is None


def test_only_one_security_job_runs_per_project(guardian, sample):
    guardian._active["p1"] = "sga_running"
    with pytest.raises(gs.Busy):
        guardian.start("p1", sample, "u1")
    assert [a.id for a in guardian.store.list("p1", "assessments")] == []     # the refused job is not left queued


# 7 accepted risk and history --------------------------------------------------------------------------------------------
def test_accepted_risk_needs_a_reason_and_survives_reassessment(guardian, sample):
    _, by = assessed(guardian, sample)
    fid = by["PY-CORS "].id
    with pytest.raises(GuardianError):
        guardian.accept_risk("p1", fid, "u1", "  ")
    guardian.accept_risk("p1", fid, "u1", "public read-only API, no cookies")
    _, by = assessed(guardian, sample)
    f = by["PY-CORS "]
    assert f.state == "accepted_risk" and f.accepted_by == "u1" and f.accepted_note.startswith("public")


def test_history_marks_resolved_and_recurring_findings(guardian, sample):
    first, by = assessed(guardian, sample)
    main = sample / "backend" / "main.py"
    original = main.read_text(encoding="utf-8")
    main.write_text(original.replace("hashlib.md5(", "hashlib.sha256("), encoding="utf-8")
    second, by2 = assessed(guardian, sample)
    weak = guardian.store.get("p1", "findings", by["PY-WEAK-HASH "].id)
    assert "resolved_at" in weak.context
    cmp = guardian.compare("p1", first.id, second.id)
    assert weak.id in [x["id"] for x in cmp["resolved"]] and cmp["new"] == []
    main.write_text(original, encoding="utf-8")
    assessed(guardian, sample)
    assert "resolved_at" not in guardian.store.get("p1", "findings", weak.id).context


def test_fixed_findings_that_reappear_are_detected_again():
    old = finding(state="fix_verified")
    new = finding()
    merged = correlate.merge_history({old.id: old}, [new])
    assert merged[old.id].state == "detected" and "detected again" in " ".join(merged[old.id].priority_reasons)


def test_priority_uses_verification_and_exposure():
    public = finding(state="verified", context={"exposure": "public"}, route="GET /x")
    behind = finding(state="detected", context={"exposure": "authenticated"}, route="GET /y")
    assert correlate.prioritize(public)[0] == "P1"
    assert correlate.prioritize(behind)[0] in ("P3", "P4")
    assert any("authentication" in r for r in correlate.prioritize(behind)[1])


# 8 remediation plans ---------------------------------------------------------------------------------------------------------
def test_sql_injection_plan_has_a_scoped_fix_and_a_regression_test(guardian, sample):
    _, by = assessed(guardian, sample)
    f = by["PY-SQLI GET /api/users/search"]
    plan = guardian.create_plan("p1", sample, "u1", f.id)
    assert plan.origin == "security" and plan.origin_ref == f.id and plan.status.value == "awaiting_approval"
    t1, t2 = plan.tasks
    assert t1.strategy == "model" and t1.files == ["backend/main.py"] and SECRET_VALUE not in t1.request
    assert t2.strategy == "write_files" and t2.files == [f"tests/test_security_{f.id}.py"]
    test = t2.contents[t2.files[0]]
    assert "from backend.main import app" in test and "OR '1'='1" in test and "assert size(attack) <= size(base)" in test
    assert guardian.store.get("p1", "findings", f.id).state == "detected"     # a plan is not a fix
    with pytest.raises(GuardianError, match="open plan"):
        guardian.create_plan("p1", sample, "u1", f.id)


def test_changes_needing_a_human_decision_are_not_automated(guardian, sample):
    _, by = assessed(guardian, sample)
    with pytest.raises(GuardianError, match="human review"):
        guardian.create_plan("p1", sample, "u1", by["PY-WEAK-HASH "].id)
    with pytest.raises(GuardianError, match="human review"):
        guardian.create_plan("p1", sample, "u1", by["PY-MISSING-AUTH GET /api/users"].id)   # low confidence: design decision
    auth = guardian.create_plan("p1", sample, "u1", by["PY-MISSING-AUTH DELETE /api/users/{user_id}"].id)
    assert auth.security_review_required
    test = auth.tasks[1].contents[auth.tasks[1].files[0]]
    assert 'client.request("DELETE", "/api/users/1")' in test and "in (401, 403)" in test


def test_regression_tests_have_no_template_without_a_parameter():
    f = finding(route="GET /api/items", verifiable="sql_injection", context={"params": []})
    assert regression.generate(__import__("pathlib").Path("."), f) is None


# 9 the security gate ------------------------------------------------------------------------------------------------------------
def _gate(guardian, sample, before, after, monkeypatch, tmp_path):
    _, by = assessed(guardian, sample)
    f = by["PY-SQLI GET /api/users/search"]
    plan = guardian.create_plan("p1", sample, "u1", f.id)
    results = iter([before, after])
    monkeypatch.setattr(gs, "verify", lambda project, fs, stop, ev: {f.id: next(results)})
    return guardian.gate(plan, sample, tmp_path, "exe_1", lambda: False), f.id


def test_gate_accepts_only_a_reproduced_issue_that_no_longer_reproduces(guardian, sample, monkeypatch, tmp_path):
    g, fid = _gate(guardian, sample, Verification(method="m", status="verified", conclusion="3 vs 0"),
                   Verification(method="m", status="not_reproduced", conclusion="0 vs 0"), monkeypatch, tmp_path)
    assert g.decision == "improved" and guardian.store.get("p1", "findings", fid).state == "fix_verified"
    assert guardian.store.get("p1", "gates", "exe_1").decision == "improved"


@pytest.mark.parametrize("before, after, decision", [
    ("verified", "verified", "inconclusive"),             # still reproduces
    ("not_reproduced", "not_reproduced", "inconclusive"),  # never reproduced: the fix cannot be shown
    ("verified", "unavailable", "not_measured"),
])
def test_gate_never_claims_a_fix_without_evidence(guardian, sample, monkeypatch, tmp_path, before, after, decision):
    g, fid = _gate(guardian, sample, Verification(method="m", status=before), Verification(method="m", status=after),
                   monkeypatch, tmp_path)
    assert g.decision == decision and guardian.store.get("p1", "findings", fid).state not in ("fixed", "fix_verified")


def test_static_gate_for_rules_without_a_safe_test(guardian, sample, tmp_path):
    import shutil
    _, by = assessed(guardian, sample)
    f = by["PY-HARDCODED-KEY "]
    copy = tmp_path / "changed"
    shutil.copytree(sample, copy)
    main = copy / "backend" / "main.py"
    main.write_text(main.read_text(encoding="utf-8").replace(f'SECRET_KEY = "{SECRET_VALUE}"', 'SECRET_KEY = os.environ["SECRET_KEY"]'),
                    encoding="utf-8")
    plan = guardian.create_plan("p1", sample, "u1", f.id)
    g = guardian.gate(plan, sample, copy, "exe_2", lambda: False)
    assert g.decision == "improved" and "static re-check" in g.reasons[0]
    assert guardian.store.get("p1", "findings", f.id).state == "fixed"         # not "fix_verified": no dynamic proof


# 10 API ------------------------------------------------------------------------------------------------------------------------------
@pytest.fixture
def api(guardian, sample, monkeypatch):
    import backend.guardian.routes as routes
    import backend.routes.export as export
    from backend.auth.dependencies import get_current_user
    from backend.generation.store import global_generation_store
    monkeypatch.setattr(routes, "global_security_guardian", guardian)
    records = {"gen_mine": {"generation_id": "gen_mine", "user_id": "alice", "status": "completed", "project_path": str(sample)},
               "gen_theirs": {"generation_id": "gen_theirs", "user_id": "bob", "status": "completed", "project_path": str(sample)}}
    monkeypatch.setattr(global_generation_store, "get", lambda gid, default=None: records.get(gid, default))
    monkeypatch.setattr(export, "_safe_project_dir", lambda p: sample if p == str(sample) else None)
    app = FastAPI()
    app.include_router(routes.guardian_router)
    app.dependency_overrides[get_current_user] = lambda: {"id": "alice"}
    return TestClient(app)


def test_api_flow_with_ownership_filters_and_reports(api):
    base = "/api/projects/gen_mine/guardian"
    assert api.post("/api/projects/gen_theirs/guardian/assessments").status_code == 403
    assert api.get("/api/projects/missing/guardian/findings").status_code == 404
    assert api.get(f"{base}/report").status_code == 404                        # nothing to report before an assessment
    assert api.post(f"{base}/assessments").status_code == 202
    history = api.get(f"{base}/assessments").json()
    assert history["assessments"][0]["status"] == "completed" and history["active_job"] is None
    items = api.get(f"{base}/findings", params={"category": "injection"}).json()["items"]
    assert [f["rule_id"] for f in items] == ["PY-SQLI"]
    fid = items[0]["id"]
    assert api.get(f"{base}/findings/{fid}").json()["finding"]["evidence"]
    assert api.post(f"{base}/verifications", json={"finding_ids": [fid]}).status_code == 400    # not approved
    assert api.post(f"{base}/findings/{fid}/accept-risk", json={"note": ""}).status_code == 422
    assert api.post(f"{base}/findings/{fid}/plan").status_code == 201
    md = api.get(f"{base}/report")
    assert md.status_code == 200 and md.text.startswith("# Security Guardian report") and SECRET_VALUE not in md.text
    assert api.get(f"{base}/report", params={"format": "json"}).json()["findings"]
    assert api.get(f"{base}/report", params={"format": "html"}).status_code == 422


# 11 other modules use real assessments ------------------------------------------------------------------------------------------------
def test_readiness_security_check_uses_the_latest_real_assessment(guardian, sample):
    from backend.readiness.checks import global_readiness_check_collector
    check = lambda: next(c for c in global_readiness_check_collector.collect_all_checks("p1") if c.id == "chk_sec_01")  # noqa: E731
    assert check().status.value == "NOT_AVAILABLE" and not check().blocking
    assessed(guardian, sample)
    c = check()
    assert c.status.value == "FAIL" and c.blocking and "critical/high" in c.evidence
    assert gs.security_status("p1")["decision"] == "BLOCK"


def test_findings_needing_review_warn_but_do_not_block(guardian, tmp_path):
    from backend.readiness.checks import global_readiness_check_collector
    app = tmp_path / "public_api"
    (app / "backend").mkdir(parents=True)
    (app / "backend" / "main.py").write_text(
        "from fastapi import FastAPI\n\napp = FastAPI()\n\n\n@app.delete('/api/items/{item_id}')\n"
        "def delete_item(item_id: int):\n    return {'deleted': item_id}\n", encoding="utf-8")
    _, by = assessed(guardian, app)          # no authentication anywhere: whether it should be public is a decision
    assert by["PY-MISSING-AUTH DELETE /api/items/{item_id}"].state == "requires_review"
    status = gs.security_status("p1")
    assert status["decision"] == "REVIEW_NEEDED" and "needing review" in status["detail"]
    check = next(c for c in global_readiness_check_collector.collect_all_checks("p1") if c.id == "chk_sec_01")
    assert check.status.value == "WARN" and not check.blocking


def test_retired_sample_scans_are_gone():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    for rel in ("backend/readiness/checks.py", "backend/copilot/executor.py", "backend/incidents/remediation.py",
                "backend/architecture_simulator/evaluator.py"):
        assert '{"main.py": "pass"}' not in (root / rel).read_text(encoding="utf-8"), rel
    assert not (root / "backend" / "security" / "routes.py").exists()


def test_the_page_uses_the_real_api():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2] / "frontend" / "src"
    service = (root / "services" / "guardian.js").read_text(encoding="utf-8")
    page = (root / "pages" / "SecurityGuardianPage.jsx").read_text(encoding="utf-8")
    for path in ("/assessments", "/abort", "/findings", "/verifications", "/accept-risk", "/plan", "/gates", "/compare", "/report"):
        assert path in service
    assert "verifyGuardianFindings" in page and "consent" in page and "security_reviewed" in page
    for fake in ("Math.random", "mockData", "fakeScore", "sample_files"):
        assert fake not in page


# 12 genuine end to end in Docker ---------------------------------------------------------------------------------------------------------
def _docker_ok():
    try:
        from backend.execution.docker_test_sandbox import docker_available
        return docker_available()
    except Exception:
        return False


@pytest.mark.skipif(not _docker_ok(), reason="Docker is not available: the genuine verification was NOT run")
def test_genuine_verification_in_the_isolated_sandbox(guardian, sample):
    from backend.chaos.sandbox import _docker
    _, by = assessed(guardian, sample)
    keys = ["PY-SQLI GET /api/users/search", "PY-SENSITIVE-RESPONSE GET /api/users",
            "PY-MISSING-AUTH DELETE /api/users/{user_id}", "PY-CORS "]
    job = guardian.start_verification("p1", sample, "u1", [by[k].id for k in keys], approved=True)
    job = guardian.store.get("p1", "assessments", job.id)
    assert job.status == "completed", job.error
    for k in keys:
        f = guardian.store.get("p1", "findings", by[k].id)
        assert f.state == "verified", (k, f.verification.conclusion)
        assert f.verification.requests and f.verification.method
    sqli = guardian.store.get("p1", "findings", by[keys[0]].id)
    assert "3 result(s) vs 0" in sqli.verification.conclusion
    assert not _docker("ps", "-a", "-q", "--filter", "label=aiforge.chaos", timeout=30).stdout.split()


SQLI_FIX = ("    rows = conn.execute(f\"SELECT id, name, email FROM users WHERE name = '{name}'\").fetchall()",
            "    rows = conn.execute(\"SELECT id, name, email FROM users WHERE name = ?\", (name,)).fetchall()")


@pytest.mark.skipif(not _docker_ok(), reason="Docker is not available: the genuine remediation was NOT run")
def test_genuine_remediation_is_tested_reverified_and_applied(guardian, sample, monkeypatch):
    """Assessment -> verification -> plan -> approval -> isolated fix, project tests and the new regression
    test in Docker -> the same verification before/after -> applied. The 'model' is a fixed answer so the
    test does not depend on a local LLM; it receives the file with the secret line hidden."""
    monkeypatch.setenv("AIFORGE_TEST_SANDBOX", "docker")          # the project's tests run in the Docker sandbox
    _, by = assessed(guardian, sample)
    f = by["PY-SQLI GET /api/users/search"]
    guardian.start_verification("p1", sample, "u1", [f.id], approved=True)
    assert guardian.store.get("p1", "findings", f.id).state == "verified"
    plan = guardian.create_plan("p1", sample, "u1", f.id)
    prompts = []

    def model(system, prompt):
        prompts.append(prompt)
        shown = prompt.split("### backend/main.py\n```\n", 1)[1].split("\n```", 1)[0]
        return "### backend/main.py\n```python\n" + shown.replace(*SQLI_FIX) + "\n```\n"
    ap = guardian.autopilot
    ap.decide("p1", plan.id, "u1", "approved")
    e = ap.execute("p1", plan.id, "u1", sample, generate=model, include_tests=True)
    assert prompts and all(SECRET_VALUE not in p for p in prompts)
    assert e.status == "completed", (e.error, [(s.name, s.status, s.detail) for s in e.stages])
    tests_after = next(c for c in e.after if c.check_id == "tests")
    assert tests_after.status == "passed" and tests_after.counts.get("passed") == 5      # 4 existing + the regression test
    assert tests_after.environment.startswith("Docker")
    g = guardian.store.get("p1", "gates", e.id)
    assert g.decision == "improved" and g.original.status == "verified" and g.changed.status == "not_reproduced"
    assert guardian.store.get("p1", "findings", f.id).state == "fix_verified"
    main = (sample / "backend" / "main.py").read_text(encoding="utf-8")
    assert SQLI_FIX[1] in main and f'SECRET_KEY = "{SECRET_VALUE}"' in main      # the hidden line was restored
    assert (sample / f"tests/test_security_{f.id}.py").exists()
