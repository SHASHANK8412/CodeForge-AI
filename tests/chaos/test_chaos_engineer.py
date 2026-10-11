"""
AIForge Chaos Engineer: scenarios, safety preflight, approval, injection/restore/recovery, evidence,
scoring, inconclusive and aborted runs, cleanup, repair through Autopilot (apply / reject / roll back),
API validation, and one genuine end-to-end experiment in Docker.

Most tests use FakeSandbox, a deterministic model of the sample shop's behaviour (no containers). The
end-to-end test runs the real sandbox and is skipped (reported as skipped) when Docker is not available.
"""

import itertools

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

import backend.chaos.service as chaos_service
from backend.chaos import evaluate
from backend.chaos.models import AssessmentConfig, Criterion, DependencySpec, Limits, ScenarioResult, Target
from backend.chaos.scenarios import SCENARIOS, Aborted, run_scenario
from backend.chaos.service import ChaosEngineer, ChaosError, ChaosStore, compare_runs
from backend.evolution.autopilot.service import AutopilotService
from backend.evolution.autopilot.store import AutopilotStore

from tests.chaos.sample_project import INVENTORY_ROUTES, write_sample

DEP = DependencySpec(name="inventory", env_var="INVENTORY_URL", routes=INVENTORY_ROUTES)


class FakeSandbox:
    """Models the sample shop: /api/products needs the dependency, /health and /api/catalog do not."""
    instances = []

    def __init__(self, project, config, label="env", resilient=False, fail_setup=False):
        self.config, self.calls, self.dep_mode, self.resilient = config, [], "ok", resilient
        self.fail_setup = fail_setup
        FakeSandbox.instances.append(self)

    def setup(self):
        self.calls.append("setup")
        if self.fail_setup:
            from backend.chaos.sandbox import SandboxError
            raise SandboxError("dependency install failed")
        return ["created internal network"]

    def cleanup(self):
        self.calls.append("cleanup")
        return ["removed 3 container(s)"]

    def openapi_endpoints(self, limit=6):
        return [Target(path="/api/catalog"), Target(path="/api/products"), Target(path="/health")]

    def wait_healthy(self, health, budget):
        return 0.5

    def stop_dependency(self, name):
        self.calls.append(f"stop {name}")
        self.dep_mode = "down"

    def start_dependency(self, name):
        self.calls.append(f"start {name}")
        if self.dep_mode == "down":
            self.dep_mode = "ok"

    def control(self, name, mode, delay_ms=0):
        self.calls.append(f"control {name} {mode}")
        self.dep_mode = mode
        return "{}"

    def restart_app(self):
        self.calls.append("restart")

    def app_state(self):
        return {"running": True, "oom_killed": False}

    def app_stats(self):
        return 1.0, 40.0

    def app_logs(self, tail=80):
        return "INFO: started; token=" + "sk-" + "a" * 30

    def probe(self, endpoints, count=1, concurrency=1, timeout=10.0):
        out = []
        for t in endpoints:
            for _ in range(count):
                ep = f"{t.method} {t.path}"
                if t.path != "/api/products" or self.dep_mode == "ok":
                    out.append({"ep": ep, "status": 200, "ms": 5.0, "body": "{}"})
                elif self.dep_mode == "slow":
                    out.append({"ep": ep, "status": 200 if not self.resilient else 200,
                                "ms": 6000.0 if not self.resilient else 900.0, "body": "[]"})
                elif self.resilient:
                    out.append({"ep": ep, "status": 200, "ms": 8.0, "body": '[{"stock": null}]'})
                else:
                    out.append({"ep": ep, "status": 500, "ms": 9.0,
                                "body": 'Traceback (most recent call last):\n  File "/tmp/app/main.py", line 24'})
        return out


def ctx(sb, stop=lambda: False, limits=None):
    return {"endpoints": sb.openapi_endpoints(), "health": Target(path="/health"), "limits": limits or Limits(),
            "should_stop": stop, "dependency": "inventory", "on_step": lambda s, t: None}


@pytest.fixture
def sample(tmp_path):
    return write_sample(tmp_path / "shop")


@pytest.fixture
def services(tmp_path, monkeypatch):
    ap = AutopilotService(AutopilotStore(tmp_path / "ap"), background=False)
    ce = ChaosEngineer(ChaosStore(tmp_path / "chaos"), autopilot=ap, background=False)
    monkeypatch.setattr(chaos_service, "global_chaos_engineer", ce)
    import backend.execution.docker_test_sandbox as sandbox
    monkeypatch.setattr(sandbox, "docker_available", lambda: True)
    monkeypatch.setattr("backend.chaos.sandbox._docker", lambda *a, **k: type("R", (), {"stdout": "", "returncode": 0})())
    FakeSandbox.instances = []
    monkeypatch.setattr(chaos_service, "Sandbox", FakeSandbox)
    return ap, ce


def config(*scenarios, dependencies=(DEP,), **kw):
    return AssessmentConfig(scenarios=list(scenarios), dependencies=list(dependencies), **kw)


# 1 ------------------------------------------------------------------------------------------------
def test_scenarios_are_registered_with_full_procedures():
    assert {"dependency_unavailable", "dependency_errors", "dependency_slow", "malformed_response", "app_restart",
            "request_burst"} == set(SCENARIOS)
    for s in SCENARIOS.values():
        assert s.preconditions and s.procedure and s.expected and s.safety and s.cleanup and s.verification
        assert 0 < s.max_seconds <= 300 and callable(s.run)


# 2 ------------------------------------------------------------------------------------------------
def test_preflight_refuses_unsafe_or_impossible_experiments(sample, services):
    _, ce = services
    prod = ce.create("p1", sample, "u1", config("dependency_unavailable", environment="production"))
    assert prod.status == "refused" and "production" in prod.error
    no_dep = ce.create("p1", sample, "u1", config("dependency_unavailable", dependencies=()))
    assert no_dep.status == "refused" and "stub dependency" in no_dep.error
    import backend.execution.docker_test_sandbox as sandbox
    sandbox.docker_available = lambda: False                     # restored by monkeypatch in the fixture
    no_docker = ce.create("p1", sample, "u1", config("app_restart"))
    assert no_docker.status == "refused" and "Docker" in no_docker.error
    with pytest.raises(ChaosError):
        ce.create("p1", sample, "u1", config("delete_production_database"))
    assert FakeSandbox.instances == []                           # nothing ran


# 3 ------------------------------------------------------------------------------------------------
def test_experiments_need_explicit_approval(sample, services):
    _, ce = services
    a = ce.create("p1", sample, "u1", config("dependency_unavailable"))
    assert a.status == "awaiting_approval" and FakeSandbox.instances == []
    assert any("waiting for explicit approval" in e["action"] for e in a.audit)
    done = ce.approve("p1", a.id, sample, "u1")
    assert done.status == "completed" and done.approved_by == "u1" and FakeSandbox.instances
    with pytest.raises(ChaosError):
        ce.approve("p1", a.id, sample, "u1")                     # not twice
    refused = ce.create("p1", sample, "u1", config("dependency_unavailable", environment="production"))
    with pytest.raises(ChaosError):
        ce.approve("p1", refused.id, sample, "u1")


# 4 ------------------------------------------------------------------------------------------------
def test_invalid_configurations_are_rejected():
    for bad in ({"name": "App", "env_var": "X_URL"}, {"name": "app", "env_var": "X_URL"},
                {"name": "inv", "env_var": "PATH"}, {"name": "inv", "env_var": "lower"},
                {"name": "inv", "env_var": "X_URL", "routes": {"../etc": {}}}):
        with pytest.raises(ValidationError):
            DependencySpec(**bad)
    for path in ("http://evil.example/", "/../../etc/passwd", "relative"):
        with pytest.raises(ValidationError):
            Target(path=path)
    with pytest.raises(ValidationError):
        Limits(memory_mb=64 * 1024)
    with pytest.raises(ValidationError):
        Limits(max_concurrency=500)
    with pytest.raises(ValidationError):
        AssessmentConfig(scenarios=["app_restart"], dependencies=[DEP] * 4)


# 5 ------------------------------------------------------------------------------------------------
@pytest.fixture
def api(services, sample, monkeypatch):
    import backend.chaos.routes as routes
    import backend.routes.export as export
    from backend.auth.dependencies import get_current_user
    from backend.generation.store import global_generation_store
    _, ce = services
    monkeypatch.setattr(routes, "global_chaos_engineer", ce)
    records = {"gen_mine": {"generation_id": "gen_mine", "user_id": "alice", "status": "completed", "project_path": str(sample)},
               "gen_theirs": {"generation_id": "gen_theirs", "user_id": "bob", "status": "completed", "project_path": str(sample)}}
    monkeypatch.setattr(global_generation_store, "get", lambda gid, default=None: records.get(gid, default))
    monkeypatch.setattr(export, "_safe_project_dir", lambda p: sample if p == str(sample) else None)
    app = FastAPI()
    app.include_router(routes.chaos_router)
    app.dependency_overrides[get_current_user] = lambda: {"id": "alice"}
    return TestClient(app)


BODY = {"scenarios": ["dependency_unavailable"], "dependencies": [{"name": "inventory", "env_var": "INVENTORY_URL",
                                                                   "routes": INVENTORY_ROUTES}]}


def test_project_access_is_enforced(api):
    assert api.post("/api/projects/gen_theirs/chaos/assessments", json=BODY).status_code == 403
    assert api.get("/api/projects/missing/chaos/assessments").status_code == 404
    assert api.get("/api/projects/..%2F..%2Fetc/chaos/findings").status_code == 404


# 6 ------------------------------------------------------------------------------------------------
def test_scenario_time_limit_makes_it_inconclusive(monkeypatch):
    clock = itertools.count(0, 50)                              # every clock read advances 50 s
    monkeypatch.setattr("backend.chaos.scenarios.time.monotonic", lambda: next(clock))
    monkeypatch.setattr("backend.chaos.scenarios.time.sleep", lambda s: None)
    sb = FakeSandbox(None, config("dependency_unavailable"))
    r = run_scenario(sb, "dependency_unavailable", ctx(sb, limits=Limits(max_scenario_seconds=20)))
    assert r.status == "inconclusive" and "time limit" in r.error


# 7, 8, 9, 10 ------------------------------------------------------------------------------------------
def test_injection_restore_recovery_and_evidence():
    sb = FakeSandbox(None, config("dependency_unavailable"))
    r = run_scenario(sb, "dependency_unavailable", ctx(sb))
    assert sb.calls.index("stop inventory") < sb.calls.index("start inventory")          # injected, then restored
    assert [o.phase for o in r.observations] == ["baseline", "failure", "recovery"]
    assert r.affected_endpoints == ["GET /api/products"] and "GET /api/catalog" in r.unaffected_endpoints
    assert r.detect_seconds is not None and r.recovery_seconds is not None
    crit = {c.id: c for c in r.criteria}
    assert crit["containment"].status == "passed" and crit["recovers"].status == "passed"
    assert crit["controlled_errors"].status == "failed" and "500" in crit["controlled_errors"].evidence
    assert crit["no_internal_details"].status == "failed" and "stack trace" in crit["no_internal_details"].evidence
    assert r.status == "failed" and len(r.procedure) >= 4
    slow = FakeSandbox(None, config("dependency_slow"))
    rs = run_scenario(slow, "dependency_slow", ctx(slow))
    assert {c.id: c.status for c in rs.criteria}["fails_fast"] == "failed"
    assert "control inventory slow" in slow.calls and "control inventory ok" in slow.calls


# 11 -----------------------------------------------------------------------------------------------
def test_resilience_score_counts_only_evaluated_criteria():
    def res(status, *crits):
        return ScenarioResult(scenario="x", status=status, criteria=[
            Criterion(id=i, category=c, description="d", status=s, evidence="e") for i, c, s in crits])
    s = evaluate.score([res("failed", ("a", "timeout", "passed"), ("b", "timeout", "failed")),
                        res("passed", ("c", "recovery", "passed"), ("d", "data_integrity", "not_evaluated"))])
    assert s["categories"]["timeout"]["score"] == 50.0 and s["categories"]["recovery"]["score"] == 100.0
    assert s["categories"]["data_integrity"]["score"] is None and s["categories"]["data_integrity"]["not_evaluated"] == 1
    assert s["overall"] == 75.0 and s["scenarios_failed"] == 1 and s["scenarios_passed"] == 1
    assert evaluate.score([])["overall"] is None


# 12 -----------------------------------------------------------------------------------------------
def test_unhealthy_baseline_and_unevaluable_gates_are_inconclusive():
    sb = FakeSandbox(None, config("dependency_unavailable"))
    sb.probe = lambda eps, *a, **k: [{"ep": f"{t.method} {t.path}", "status": 503, "ms": 1.0, "body": ""} for t in eps]
    r = run_scenario(sb, "dependency_unavailable", ctx(sb))
    assert r.status == "inconclusive" and "not healthy before" in r.error and "stop inventory" not in sb.calls
    passed = [ScenarioResult(scenario="s", criteria=[Criterion(id="c", category="timeout", description="", status="passed", evidence="")])]
    nev = [ScenarioResult(scenario="s", criteria=[Criterion(id="c", category="timeout", description="", status="not_evaluated", evidence="")])]
    assert compare_runs(nev, passed, "c")[0] == "inconclusive"
    assert compare_runs(passed, passed, "c")[0] == "inconclusive"     # nothing to improve: not claimed


# 13 -----------------------------------------------------------------------------------------------
def test_abort_stops_and_cleans_up(sample, services):
    _, ce = services
    a = ce.create("p1", sample, "u1", config("dependency_unavailable", "app_restart"))
    ce.store.update("p1", "assessments", a.id, lambda x: setattr(x, "abort_requested", True))
    ce.store.update("p1", "assessments", a.id, lambda x: setattr(x, "status", "awaiting_approval"))
    done = ce.approve("p1", a.id, sample, "u1")
    assert done.status == "aborted" and "sandbox was removed" in done.error
    assert FakeSandbox.instances[-1].calls[-1] == "cleanup"
    sb = FakeSandbox(None, config("dependency_unavailable"))
    with pytest.raises(Aborted):
        run_scenario(sb, "dependency_unavailable", ctx(sb, stop=lambda: True))
    waiting = ce.create("p1", sample, "u1", config("app_restart"))
    assert ce.abort("p1", waiting.id, "u1").status == "aborted"


# 14 -----------------------------------------------------------------------------------------------
def test_cleanup_runs_after_exceptions(sample, services, monkeypatch):
    _, ce = services
    monkeypatch.setattr(chaos_service, "Sandbox", lambda p, c, l: FakeSandbox(p, c, l, fail_setup=True))
    a = ce.approve("p1", ce.create("p1", sample, "u1", config("dependency_unavailable")).id, sample, "u1")
    assert a.status == "failed" and "dependency install failed" in a.error
    assert FakeSandbox.instances[-1].calls == ["setup", "cleanup"]
    assert a.score["overall"] is None                           # nothing evaluated, nothing scored


def _repairable(ce, sample):
    a = ce.approve("p1", ce.create("p1", sample, "u1", config("dependency_unavailable")).id, sample, "u1")
    f = next(x for x in ce.store.list("p1", "findings") if x.criterion == "controlled_errors")
    return a, f


FIXED = None


def _fix_reply(sample):
    main = (sample / "backend/main.py").read_text(encoding="utf-8")
    fixed = main.replace(
        '    stock = fetch_stock()\n',
        '    try:\n        stock = fetch_stock()\n    except Exception:\n        stock = {}\n').replace(
        'urllib.request.urlopen(INVENTORY_URL + "/stock")', 'urllib.request.urlopen(INVENTORY_URL + "/stock", timeout=2)')
    return lambda system, prompt: "### backend/main.py\n```python\n" + fixed + "```\n"


# 15 -----------------------------------------------------------------------------------------------
def test_a_verified_repair_is_applied(sample, services, monkeypatch):
    ap, ce = services
    a, f = _repairable(ce, sample)
    assert f.root_cause_level == "probable" and f.file == "backend/main.py" and "urlopen" in f.root_cause
    plan = ce.create_plan("p1", sample, "u1", f.id)
    assert plan.origin == "chaos" and plan.expected_files == ["backend/main.py"] and plan.status.value == "awaiting_approval"
    ap.decide("p1", plan.id, "u1", "approved")
    # the gate's second run is the repaired copy: model it as resilient
    sandboxes = iter([False, True])
    monkeypatch.setattr(chaos_service, "Sandbox", lambda p, c, l: FakeSandbox(p, c, l, resilient=next(sandboxes)))
    e = ap.execute("p1", plan.id, "u1", sample, generate=_fix_reply(sample), include_tests=False)
    assert e.status == "completed", e.error
    assert e.verdict["chaos"]["decision"] == "improved" and e.applied_to_project
    assert "timeout=2" in (sample / "backend/main.py").read_text(encoding="utf-8")
    finding = ce.store.get("p1", "findings", f.id)
    assert finding.status == "verified" and finding.root_cause_level == "confirmed"
    gate = ce.store.get("p1", "gates", e.id)
    assert gate.decision == "improved" and gate.results and gate.candidate_results


# 16, 17 -------------------------------------------------------------------------------------------
def test_a_repair_that_does_not_help_is_rolled_back(sample, services, monkeypatch):
    ap, ce = services
    _, f = _repairable(ce, sample)
    plan = ce.create_plan("p1", sample, "u1", f.id)
    ap.decide("p1", plan.id, "u1", "approved")
    monkeypatch.setattr(chaos_service, "Sandbox", lambda p, c, l: FakeSandbox(p, c, l, resilient=False))
    before = (sample / "backend/main.py").read_text(encoding="utf-8")
    e = ap.execute("p1", plan.id, "u1", sample, generate=_fix_reply(sample), include_tests=False)
    assert e.status == "inconclusive" and not e.applied_to_project
    assert (sample / "backend/main.py").read_text(encoding="utf-8") == before
    assert ce.store.get("p1", "findings", f.id).status == "not_improved"


def test_correctness_regressions_stop_before_the_experiment(sample, services, monkeypatch):
    ap, ce = services
    _, f = _repairable(ce, sample)
    plan = ce.create_plan("p1", sample, "u1", f.id)
    ap.decide("p1", plan.id, "u1", "approved")
    count = len(FakeSandbox.instances)
    broken = lambda s, p: "### backend/main.py\n```python\nfrom fastapi import FastAPI\napp = FastAPI()\nx = missing_name\n```\n"
    e = ap.execute("p1", plan.id, "u1", sample, generate=broken, include_tests=False)
    assert e.status == "rejected" and len(FakeSandbox.instances) == count            # no experiment ran
    assert any(s.name.startswith("chaos") and s.status == "skipped" for s in e.stages)
    from backend.chaos.models import ChaosFinding
    ce.store.put("p1", "findings", ChaosFinding(id="cf_static", project_id="p1", category="timeout", component="x",
                                                severity="low", kind="static_suspicion", title="t", evidence="e",
                                                file="backend/main.py", line=24))
    with pytest.raises(ChaosError):
        ce.create_plan("p1", sample, "u1", "cf_static")                  # suspicions are not repairable


def test_gate_detects_regressions():
    def run(*statuses):
        return [ScenarioResult(scenario="s", criteria=[Criterion(id=i, category="x", description="", status=s, evidence=s)
                                                        for i, s in statuses])]
    assert compare_runs(run(("a", "failed"), ("b", "passed")), run(("a", "passed"), ("b", "failed")), "a")[0] == "regressed"
    assert compare_runs(run(("a", "failed"), ("b", "passed")), run(("a", "passed"), ("b", "passed")), "a")[0] == "improved"
    assert compare_runs(run(("a", "failed")), run(("a", "failed")), "a")[0] == "inconclusive"


# 18 -----------------------------------------------------------------------------------------------
def test_api_validation_and_flow(api):
    base = "/api/projects/gen_mine/chaos"
    assert api.post(f"{base}/assessments", json={"scenarios": ["nope"]}).status_code == 400
    assert api.post(f"{base}/assessments", json={**BODY, "limits": {"max_concurrency": 999}}).status_code == 422
    bad_dep = {**BODY, "dependencies": [{"name": "inventory", "env_var": "PATH"}]}
    assert api.post(f"{base}/assessments", json=bad_dep).status_code == 422
    pre = api.post(f"{base}/preflight", json=BODY).json()
    assert pre["passed"] and {c["check"] for c in pre["checks"]} >= {"environment is an isolated sandbox", "Docker is available"}
    a = api.post(f"{base}/assessments", json=BODY).json()["assessment"]
    assert a["status"] == "awaiting_approval"
    done = api.post(f"{base}/assessments/{a['id']}/approve").json()["assessment"]
    assert done["status"] == "completed" and done["score"]["overall"] is not None
    assert api.post(f"{base}/assessments/{a['id']}/approve").status_code == 409
    hist = api.get(f"{base}/assessments").json()["assessments"]
    assert hist[0]["failed"] == ["dependency_unavailable"]
    assert api.get(f"{base}/compare", params={"first": a["id"], "second": "cha_missing"}).status_code == 404
    findings = api.get(f"{base}/findings").json()["items"]
    assert findings[0]["kind"] == "reproduced"
    scen = api.get("/api/chaos/scenarios").json()
    assert {e["id"]: e["supported"] for e in scen["environments"]} == {"sandbox": True, "production": False}


# 19 -----------------------------------------------------------------------------------------------
def test_the_page_uses_the_real_api():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2] / "frontend" / "src"
    service = (root / "services" / "chaos.js").read_text(encoding="utf-8")
    page = (root / "pages" / "ChaosEngineerPage.jsx").read_text(encoding="utf-8")
    for path in ("/assessments", "/approve", "/abort", "/preflight", "/findings", "/gates", "/compare"):
        assert path in service
    assert "approveChaosAssessment" in page and "consent" in page          # explicit approval in the UI
    for fake in ("Math.random", "setTimeout(() => setProgress", "mockData", "fakeScore"):
        assert fake not in page


# 20 -----------------------------------------------------------------------------------------------
def _docker_ok():
    try:
        from backend.execution.docker_test_sandbox import docker_available
        return docker_available()
    except Exception:
        return False


@pytest.mark.skipif(not _docker_ok(), reason="Docker is not available: the genuine end-to-end experiment was NOT run")
def test_genuine_experiment_in_docker(sample, monkeypatch):
    """A real disposable app and dependency: inject, observe, restore, verify recovery, clean up."""
    from backend.chaos.sandbox import Sandbox, _docker
    cfg = config("dependency_unavailable", limits=Limits(max_scenario_seconds=120))
    sb = Sandbox(sample, cfg, "e2e")
    try:
        sb.setup()
        assert sb.wait_healthy(Target(path="/health"), 60) is not None
        c = {"endpoints": sb.openapi_endpoints(), "health": Target(path="/health"), "limits": cfg.limits,
             "should_stop": lambda: False, "dependency": "inventory", "on_step": lambda s, t: None}
        r = run_scenario(sb, "dependency_unavailable", c)
        crit = {x.id: x for x in r.criteria}
        assert r.affected_endpoints == ["GET /api/products"]                 # the failure was observed
        assert crit["controlled_errors"].status == "failed" and "500" in crit["controlled_errors"].evidence
        assert crit["containment"].status == "passed"                        # /health and /api/catalog kept working
        assert crit["recovers"].status == "passed" and r.recovery_seconds is not None
        egress = _docker("exec", sb.probe_c, "python", "-c",
                         "import urllib.request;urllib.request.urlopen('http://example.com',timeout=5)", timeout=30)
        assert egress.returncode != 0                                         # no route out of the sandbox
    finally:
        sb.cleanup()
    left = _docker("ps", "-a", "-q", "--filter", f"label=aiforge.chaos={sb.id}", timeout=30).stdout.split()
    assert left == [] and _docker("network", "inspect", sb.network, timeout=30).returncode != 0


def test_gate_recognises_a_failure_that_no_longer_affects_the_endpoint():
    """Regression from a real run: a complete fix leaves no affected endpoint, so the criterion about
    affected endpoints is not evaluated afterwards; the gate must still see the improvement."""
    before = [ScenarioResult(scenario="s", affected_endpoints=["GET /api/products"], criteria=[
        Criterion(id="controlled_errors", category="error_handling", description="", status="failed", evidence="500")])]
    after = [ScenarioResult(scenario="s", affected_endpoints=[], criteria=[
        Criterion(id="controlled_errors", category="error_handling", description="", status="not_evaluated",
                  evidence="no endpoint was affected")])]
    decision, reasons = compare_runs(before, after, "controlled_errors")
    assert decision == "improved" and "no longer affects" in reasons[0]
    still = [ScenarioResult(scenario="s", affected_endpoints=["GET /api/products"], criteria=after[0].criteria)]
    assert compare_runs(before, still, "controlled_errors")[0] == "inconclusive"
