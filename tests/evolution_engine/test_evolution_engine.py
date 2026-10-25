"""
AIForge Evolution Engine tests. The sample (sample_project.py) is a FastAPI + sqlite3 app with a real N+1
endpoint. Fast tests replace only the Docker-bound steps (the project's test run and the latency measurement)
with doubles that answer from the candidate's actual code; discovery, planning, workspaces, the model call
path, the Security Guardian analysis, selection, memory, approval and promotion logic run for real. The tests
at the end run the genuine pipeline in Docker.
"""

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import backend.evolution_engine.service as es
from backend.evolution.autopilot.models import CheckResult, now_iso
from backend.evolution.autopilot.service import AutopilotService
from backend.evolution.autopilot.store import AutopilotStore
from backend.evolution_engine import memory, selection
from backend.evolution_engine.models import Candidate, Weights
from backend.evolution_engine.service import EvolutionEngine, EvolutionError, EvolutionStore, source_revision
from backend.performance.engineer.models import EndpointStats, Measurement, Resources
from tests.evolution_engine.sample_project import CANDIDATES, HEAD, JOIN, MAIN, scripted_model, write_sample

TARGET = "GET /api/authors"


@pytest.fixture
def sample(tmp_path):
    return write_sample(tmp_path / "library")


@pytest.fixture
def engine(tmp_path, monkeypatch):
    ap = AutopilotService(AutopilotStore(tmp_path / "ap"), background=False)
    ee = EvolutionEngine(EvolutionStore(tmp_path / "ev"), autopilot=ap, background=False, generate=scripted_model())
    monkeypatch.setattr(es, "global_evolution_engine", ee)      # memory and the Autopilot gate look it up
    return ee


def _check(check_id, status, **counts):
    return CheckResult(check_id=check_id, label=check_id, environment="double (test)", started_at=now_iso(),
                       finished_at=now_iso(), status=status, counts=counts, output="")


def _stats(medians):
    med = sorted(medians)[len(medians) // 2]
    return EndpointStats(method="GET", path="/api/authors", requests=180, errors=0, error_rate_pct=0.0, median_ms=med,
                         p95_ms=med * 1.3, throughput_rps=round(1000 / med * 2, 2), rep_medians_ms=medians)


@pytest.fixture
def docker_doubles(monkeypatch):
    """Test results and latency derived from the code in each workspace (what Docker would observe)."""
    from backend.evolution.autopilot import validation
    from backend.performance.engineer import runner
    seen = {"tests": [], "measured": None, "test_runs": {}}
    behaviour = {"flaky_once": False, "tests_blocked": False, "measure": "ok"}

    def outcome(ws):
        code = (ws / "backend" / "main.py").read_text(encoding="utf-8")
        seen["tests"].append(code)
        if behaviour["tests_blocked"] and code != MAIN:
            return _check("tests", "blocked")
        key = str(ws)
        seen["test_runs"][key] = seen["test_runs"].get(key, 0) + 1
        broken = "grouped" in code                                    # the candidate that drops authors
        if behaviour["flaky_once"] and code != MAIN and seen["test_runs"][key] == 1:
            return _check("tests", "failed", passed=2, failed=1)
        return _check("tests", "failed", passed=1, failed=2) if broken else _check("tests", "passed", passed=3)

    def run_checks(ws, include_tests=True, disposable=False):
        return [_check("python_syntax", "passed", files=2, errors=0), _check("quality_gate", "passed", errors=0),
                _check("security_static", "passed", high=0), outcome(ws)]

    def measure(versions, workload, stop=None, on_stage=None):
        seen["measured"] = sorted(versions)
        out = {}
        for label, ws in versions.items():
            code = (ws / "backend" / "main.py").read_text(encoding="utf-8")
            m = Measurement(label=label, status="measured", startup_seconds=1.0,
                            resources=Resources(samples=5, cpu_avg_pct=40.0, mem_max_mb=70.0))
            if behaviour["measure"] == "unavailable":
                m.status, m.error = "unavailable", "Docker is not available"
            elif behaviour["measure"] == "single":
                m.endpoints = [_stats([80.0] if "LEFT JOIN" not in code else [10.0])]
            else:
                m.endpoints = [_stats([84.6, 85.1, 75.6] if "LEFT JOIN" not in code else [8.8, 21.0, 9.8])]
            out[label] = m
        from backend.performance.engineer.models import Environment
        return out, Environment(method="double (test)")
    monkeypatch.setattr(validation, "run_checks", run_checks)
    monkeypatch.setattr(validation, "check_tests", lambda ws, disposable=False: outcome(ws))
    monkeypatch.setattr(runner, "measure", measure)
    return seen, behaviour


def experiment(engine, sample, **kw):
    ops = engine.discover("p1", sample)
    op = next(o for o in ops if o.experimentable)
    return engine.create_experiment("p1", sample, "u1", op.id, **kw)


def ran(engine, sample, **kw):
    exp = experiment(engine, sample, **kw)
    engine.run("p1", sample, "u1", exp.id, approved=True)
    return engine.store.get("p1", "experiments", exp.id)


# 1 discovery and planning ---------------------------------------------------------------------------------------------
def test_discovery_finds_the_measurable_n_plus_one_with_evidence(engine, sample):
    ops = engine.discover("p1", sample)
    op = ops[0]
    assert op.experimentable and op.endpoint == TARGET and op.category == "n_plus_one"
    assert op.evidence[0]["kind"] == "static" and "SELECT title FROM books" in op.evidence[0]["detail"]
    assert op.expected_benefit.startswith("prediction") and op.possible_regressions and op.priority > 0
    assert op.components[0] == "backend/main.py"
    others = [o for o in ops if not o.experimentable]
    assert others and all("not reached from a route" in o.not_experimentable_reason for o in others)   # seeding loops


def test_discovery_never_writes_into_the_project(engine, sample):
    before = sorted(p.relative_to(sample).as_posix() for p in sample.rglob("*"))
    engine.discover("p1", sample)
    assert sorted(p.relative_to(sample).as_posix() for p in sample.rglob("*")) == before


def test_a_project_without_tests_cannot_be_experimented_on(engine, sample):
    (sample / "tests" / "test_authors.py").unlink()
    op = next(o for o in engine.discover("p1", sample) if o.endpoint == TARGET)
    assert not op.experimentable and "no tests" in op.not_experimentable_reason
    exp = engine.create_experiment("p1", sample, "u1", op.id)
    assert exp.status == "rejected" and exp.outcome == "failed" and "no tests" in exp.outcome_reasons[0]
    with pytest.raises(EvolutionError):
        engine.run("p1", sample, "u1", exp.id, approved=True)


def test_plans_are_complete_and_bounded(engine, sample):
    exp = experiment(engine, sample, max_candidates=2)
    p = exp.plan
    assert exp.status == "planned" and [s.id for s in p.strategies] == ["join_query", "batch_in_query"]
    assert p.target_endpoints == [TARGET] and p.workload.repetitions >= 2 and p.thresholds.noise_factor >= 1
    assert p.allowed_files == ["backend/main.py"] and p.cleanup and p.safety and p.max_seconds > 0
    assert p.context["data_access"] == "raw_sql"
    assert experiment(engine, sample, max_candidates=4).status == "rejected"
    with pytest.raises(EvolutionError):
        engine.run("p1", sample, "u1", exp.id, approved=False)


# 2 isolated candidates and evaluation -------------------------------------------------------------------------------------
def test_candidates_are_isolated_and_the_project_is_untouched(engine, sample, docker_doubles):
    seen, _ = docker_doubles
    before = source_revision(sample)
    exp = ran(engine, sample)
    assert exp.status == "evaluated" and exp.source_revision == before == source_revision(sample)
    tested = seen["tests"]
    assert MAIN in tested and any("LEFT JOIN" in t and "grouped" not in t for t in tested)
    assert any("grouped" in t and "LEFT JOIN" not in t for t in tested)        # c2 never saw c1's change
    c1, c2 = exp.candidates
    assert c1.patch_hash != c2.patch_hash and set(c1.changes) == {"backend/main.py"}
    assert seen["measured"] == ["baseline", "c1"]                                 # c2 failed a mandatory check first
    assert "cleaned up 3 workspace(s)" in exp.audit[-1]["action"] or any("cleaned up 3" in a["action"] for a in exp.audit)


def test_the_regressing_candidate_is_rejected_and_the_measured_one_selected(engine, sample, docker_doubles):
    exp = ran(engine, sample)
    c1, c2 = exp.candidates
    assert c2.eligible is False and c2.failure_kind == "candidate_defect"
    assert any("tests passed before the change and fail after it" in r for r in c2.rejection_reasons)
    assert "reproduced on a re-run" in " ".join(c2.correctness["notes"])
    assert c1.eligible and c1.performance["decision"] == "improved" and exp.selected == "c1"
    assert exp.outcome == "awaiting_approval"
    bd = c1.score_breakdown
    assert set(bd) == {"performance", "security", "reliability", "maintainability", "resource_efficiency"}
    assert abs(sum(v["contribution"] for v in bd.values()) - c1.score) < 0.05
    assert c1.resilience["status"] == "not_evaluated"                              # not invented


def test_flaky_tests_are_not_counted_as_a_defect(engine, sample, docker_doubles):
    _, behaviour = docker_doubles
    behaviour["flaky_once"] = True
    exp = ran(engine, sample, max_candidates=1)
    c1 = exp.candidates[0]
    assert c1.correctness["flaky"] and c1.failure_kind == "flaky" and not c1.eligible
    assert exp.outcome == "inconclusive"
    rec = next(r for r in engine.store.list(memory.MEMORY_KEY, "memory") if r.experiment_id == exp.id)
    assert rec.result == "inconclusive"                                           # not held against the strategy


def test_infrastructure_failures_are_not_candidate_defects(engine, sample, docker_doubles):
    _, behaviour = docker_doubles
    behaviour["tests_blocked"] = True
    exp = ran(engine, sample, max_candidates=1)
    assert exp.candidates[0].failure_kind == "infrastructure" and exp.outcome == "inconclusive"


def test_missing_measurements_are_never_scored(engine, sample, docker_doubles):
    _, behaviour = docker_doubles
    behaviour["measure"] = "unavailable"
    exp = ran(engine, sample, max_candidates=1)
    c1 = exp.candidates[0]
    assert c1.performance["decision"] == "not_measured" and c1.score is None and not c1.eligible
    assert c1.failure_kind == "infrastructure" and exp.outcome == "inconclusive"


def test_a_single_repetition_is_not_evidence(engine, sample, docker_doubles):
    _, behaviour = docker_doubles
    behaviour["measure"] = "single"
    exp = ran(engine, sample, max_candidates=1)
    c1 = exp.candidates[0]
    assert c1.performance["evidence"] == "insufficient" and exp.outcome == "inconclusive" and exp.selected is None


# 3 deterministic selection --------------------------------------------------------------------------------------------------
def _cand(cid, change, security=None, accepted=True, decision="improved"):
    rows = [{"endpoint": TARGET, "median_change_pct": change, "verdict": "faster" if decision == "improved" else "no_clear_change",
             "after": {"error_rate_pct": 0.0, "rep_medians_ms": [1, 1, 1]}}]
    return Candidate(id=cid, strategy=cid, status="evaluated", changes={"backend/main.py": cid},
                     correctness={"accepted": accepted, "regressions": [] if accepted else ["tests failed"], "unverified": []},
                     security={"status": "evaluated", "new_serious": security or [], "new_other": []},
                     performance={"decision": decision, "reasons": ["r"], "target_rows": rows, "resources": {},
                                  "evidence": "sufficient"},
                     maintainability={"changed_lines": 10, "branches_delta": 0})


def test_a_faster_candidate_with_a_security_regression_cannot_win(engine, sample):
    exp = experiment(engine, sample)
    exp.candidates = [_cand("fast_insecure", -90.0, security=["SQL built from strings (backend/main.py:40)"]),
                      _cand("safe", -40.0), _cand("broken", -95.0, accepted=False)]
    selected, outcome, _ = selection.select(exp)
    assert selected == "safe" and outcome == "awaiting_approval"
    by = {c.id: c for c in exp.candidates}
    assert not by["fast_insecure"].eligible and "security" in by["fast_insecure"].rejection_reasons[0]
    assert not by["broken"].eligible and by["broken"].failure_kind == "candidate_defect"


def test_weights_change_the_ranking_but_never_the_constraints(engine, sample):
    exp = experiment(engine, sample)
    a, b = _cand("a", -60.0), _cand("b", -50.0)
    b.maintainability = {"changed_lines": 2, "branches_delta": -1}
    a.maintainability = {"changed_lines": 40, "branches_delta": 1}
    exp.candidates = [a, b]
    assert selection.select(exp)[0] == "a"                                        # default weights favour speed
    exp.plan.weights = Weights(performance=0.1, security=0.1, reliability=0.1, maintainability=0.7, resource_efficiency=0.0)
    assert selection.select(exp)[0] == "b"
    exp.candidates = [_cand("only", -10.0, decision="inconclusive")]
    sel, outcome, _ = selection.select(exp)
    assert sel is None and outcome in ("no_improvement", "inconclusive")          # never a validated improvement


# 4 engineering memory ----------------------------------------------------------------------------------------------------------
def test_memory_records_failures_and_stops_repeating_them(engine, sample, docker_doubles):
    exp = ran(engine, sample)
    records = [r for r in engine.store.list(memory.MEMORY_KEY, "memory") if r.experiment_id == exp.id]
    by = {r.strategy: r for r in records}
    assert by["join_query"].result == "won" and by["join_query"].evidence_quality in ("strong", "moderate")
    assert by["batch_in_query"].result == "rejected" and by["batch_in_query"].failure_kind == "candidate_defect"
    assert "not a general rule" in by["join_query"].scope
    again = experiment(engine, sample)                                             # same file, same problem
    assert [s.id for s in again.plan.strategies][0] == "join_query"
    assert [s["strategy"] for s in again.plan.suppressed_strategies] == ["batch_in_query"]
    assert "won 1 past experiment" in again.plan.strategies[0].memory_note
    op = again.opportunity
    retry = engine.create_experiment("p1", sample, "u1", op.id, overrides={"batch_in_query": "now with a LEFT JOIN on authors"})
    assert "batch_in_query" in [s.id for s in retry.plan.strategies]


def test_memory_applicability_levels():
    from backend.evolution_engine.models import MemoryRecord
    r = MemoryRecord(id="m", experiment_id="e", project_id="p1", category="n_plus_one",
                     context={"file": "backend/main.py", "data_access": "raw_sql"}, strategy="join_query", result="won")
    assert memory.applicability(r, "p1", "n_plus_one", {"file": "backend/main.py", "data_access": "raw_sql"}) == "direct"
    assert memory.applicability(r, "p2", "n_plus_one", {"file": "app.py", "data_access": "raw_sql"}) == "related"
    assert memory.applicability(r, "p2", "n_plus_one", {"file": "app.py", "data_access": "sqlalchemy"}) == "weak"
    assert memory.applicability(r, "p1", "caching", {"file": "backend/main.py"}) is None


def test_experiments_persist_across_restarts(engine, sample, docker_doubles, tmp_path):
    exp = ran(engine, sample)
    reloaded = EvolutionEngine(EvolutionStore(tmp_path / "ev"), background=False)
    again = reloaded.store.get("p1", "experiments", exp.id)
    assert again.source_revision == exp.source_revision and again.candidates[0].patch_hash == exp.candidates[0].patch_hash
    assert again.outcome == "awaiting_approval"


def test_interrupted_experiments_are_closed_after_a_restart(engine, sample, tmp_path):
    exp = experiment(engine, sample)
    engine.store.update("p1", "experiments", exp.id, lambda e: setattr(e, "status", "running"))
    assert EvolutionStore(tmp_path / "ev").close_interrupted() == 1
    e = engine.store.get("p1", "experiments", exp.id)
    assert e.status == "failed" and "interrupted" in e.error


# 5 approval and promotion -------------------------------------------------------------------------------------------------------
def test_approval_is_bound_to_the_revision_and_the_patch(engine, sample, docker_doubles):
    exp = ran(engine, sample)
    with pytest.raises(EvolutionError):
        engine.approve("p1", sample, "u1", exp.id, candidate_id="c2")             # not the selected candidate
    with pytest.raises(EvolutionError):
        engine.promote("p1", sample, "u1", exp.id)                                # not approved yet
    engine.approve("p1", sample, "u1", exp.id)
    (sample / "README.md").write_text("changed after the approval\n", encoding="utf-8")
    with pytest.raises(EvolutionError, match="stale"):
        engine.promote("p1", sample, "u1", exp.id)
    e = engine.store.get("p1", "experiments", exp.id)
    assert e.approval.valid is False and e.promotion.status == "stale" and "MAIN" not in (sample / "backend/main.py").read_text()
    assert (sample / "backend" / "main.py").read_text(encoding="utf-8") == MAIN   # nothing applied


def test_a_changed_patch_invalidates_the_approval(engine, sample, docker_doubles):
    exp = ran(engine, sample)
    engine.approve("p1", sample, "u1", exp.id)

    def tamper(e):
        e.candidates[0].changes = {"backend/main.py": HEAD + JOIN + "\n# tampered\n"}
    engine.store.update("p1", "experiments", exp.id, tamper)
    with pytest.raises(EvolutionError, match="patch changed"):
        engine.promote("p1", sample, "u1", exp.id)


def _fake_execution(engine, sample, monkeypatch, applied=True, write=None, verdict=None):
    """Autopilot execution double: applies the plan's files the way the executor does (or not)."""
    from backend.evolution.autopilot.executor import apply_all
    ap = engine.autopilot

    def execute(project_id, plan_id, user_id, project_dir, generate=None, include_tests=True):
        from backend.evolution.autopilot.models import Execution
        plan = ap.store.get(project_id, "plans", plan_id)
        assert plan.status.value == "approved" and plan.origin == "evolution"
        if applied:
            apply_all(project_dir, write or plan.tasks[0].contents, "test")
        e = Execution(id="exe_t", plan_id=plan_id, project_id=project_id, user_id=user_id,
                      status="completed" if applied else "rejected", applied_to_project=applied,
                      verdict=verdict or {"evolution": {"decision": "improved", "reasons": ["faster"]}},
                      error=None if applied else "tests passed before the change and fail after it")
        ap.store.put(project_id, "executions", e)
        return e
    monkeypatch.setattr(ap, "execute", execute)


def test_promotion_applies_and_final_tests_confirm(engine, sample, docker_doubles, monkeypatch):
    exp = ran(engine, sample)
    engine.approve("p1", sample, "u1", exp.id)
    _fake_execution(engine, sample, monkeypatch)
    engine.promote("p1", sample, "u1", exp.id)
    e = engine.store.get("p1", "experiments", exp.id)
    assert e.promotion.status == "promoted" and e.outcome == "validated_improvement" and e.promotion.final_tests.status == "passed"
    assert "LEFT JOIN" in (sample / "backend" / "main.py").read_text(encoding="utf-8")
    rec = next(r for r in engine.store.list(memory.MEMORY_KEY, "memory") if r.experiment_id == exp.id and r.selected)
    assert rec.final_outcome == "validated_improvement"


def test_failing_final_tests_roll_the_promotion_back(engine, sample, docker_doubles, monkeypatch):
    exp = ran(engine, sample)
    engine.approve("p1", sample, "u1", exp.id)
    # the promoted code differs from what was evaluated (e.g. the project's environment): final tests fail
    _fake_execution(engine, sample, monkeypatch, write={"backend/main.py": CANDIDATES["batch_in_query"]})
    engine.promote("p1", sample, "u1", exp.id)
    e = engine.store.get("p1", "experiments", exp.id)
    assert e.promotion.status == "rolled_back" and e.promotion.rolled_back and e.outcome == "regression"
    assert (sample / "backend" / "main.py").read_text(encoding="utf-8") == MAIN   # exact previous contents


def test_a_rejected_autopilot_execution_leaves_the_project_unchanged(engine, sample, docker_doubles, monkeypatch):
    exp = ran(engine, sample)
    engine.approve("p1", sample, "u1", exp.id)
    _fake_execution(engine, sample, monkeypatch, applied=False)
    engine.promote("p1", sample, "u1", exp.id)
    e = engine.store.get("p1", "experiments", exp.id)
    assert e.promotion.status == "rejected" and e.outcome == "regression"
    assert (sample / "backend" / "main.py").read_text(encoding="utf-8") == MAIN


def test_the_executor_routes_evolution_plans_through_the_re_measure_gate():
    from backend.evolution.autopilot.executor import MEASURED_GATES, stages_for
    from backend.evolution.autopilot.models import Plan
    plan = Plan(id="p", project_id="p", user_id="u", objective="o", finding_ids=[], tasks=[], expected_files=[], agents=[],
                checks=[], risks=[], assumptions=[], approval_required=[], completion_criteria=[], origin="evolution")
    assert MEASURED_GATES["evolution"][1] == "backend.evolution_engine.service"
    assert stages_for(plan).index("evolution re-measure (before/after)") == stages_for(plan).index("apply") - 1


# 6 API ----------------------------------------------------------------------------------------------------------------------------
@pytest.fixture
def api(engine, sample, monkeypatch):
    import backend.evolution_engine.routes as routes
    import backend.routes.export as export
    from backend.auth.dependencies import get_current_user
    from backend.generation.store import global_generation_store
    monkeypatch.setattr(routes, "global_evolution_engine", engine)
    records = {"gen_mine": {"generation_id": "gen_mine", "user_id": "alice", "status": "completed", "project_path": str(sample)},
               "gen_theirs": {"generation_id": "gen_theirs", "user_id": "bob", "status": "completed", "project_path": str(sample)}}
    monkeypatch.setattr(global_generation_store, "get", lambda gid, default=None: records.get(gid, default))
    monkeypatch.setattr(export, "_safe_project_dir", lambda p: sample if p == str(sample) else None)
    app = FastAPI()
    app.include_router(routes.evolution_engine_router)
    app.dependency_overrides[get_current_user] = lambda: {"id": "alice"}
    return TestClient(app)


def test_api_flow_with_access_checks(api, docker_doubles):
    base = "/api/projects/gen_mine/evolution-engine"
    assert api.post("/api/projects/gen_theirs/evolution-engine/opportunities/discover").status_code == 403
    assert api.get("/api/projects/missing/evolution-engine/experiments").status_code == 404
    ops = api.post(f"{base}/opportunities/discover").json()["opportunities"]
    op = next(o for o in ops if o["experimentable"])
    assert api.post(f"{base}/experiments", json={"opportunity_id": "op_missing"}).status_code == 404
    assert api.post(f"{base}/experiments", json={"opportunity_id": op["id"], "max_candidates": 5}).status_code == 422
    assert api.post(f"{base}/experiments", json={"opportunity_id": op["id"], "overrides": {"x": "short"}}).status_code == 400
    exp = api.post(f"{base}/experiments", json={"opportunity_id": op["id"]}).json()["experiment"]
    assert api.post(f"{base}/experiments/{exp['id']}/run", json={}).status_code == 400          # not approved
    assert api.post(f"{base}/experiments/{exp['id']}/run", json={"approved": True}).status_code == 202
    detail = api.get(f"{base}/experiments/{exp['id']}").json()["experiment"]
    assert detail["outcome"] == "awaiting_approval" and detail["selected"] == "c1"
    assert api.post(f"{base}/experiments/{exp['id']}/promote").status_code == 409               # approval first
    assert api.post(f"{base}/experiments/{exp['id']}/approve", json={}).json()["experiment"]["approval"]["candidate_id"] == "c1"
    memory_rows = api.get(f"{base}/memory").json()["memory"]
    assert {m["strategy"] for m in memory_rows} == {"join_query", "batch_in_query"}


def test_the_page_uses_the_real_api():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2] / "frontend" / "src"
    service = (root / "services" / "evolutionEngine.js").read_text(encoding="utf-8")
    page = (root / "pages" / "EvolutionEnginePage.jsx").read_text(encoding="utf-8")
    for path in ("/opportunities/discover", "/experiments", "/run", "/abort", "/approve", "/promote", "/memory"):
        assert path in service
    assert "consent" in page and "approved: true" in service
    for fake in ("Math.random", "mockData", "fakeScore", "|| 96"):
        assert fake not in page


# 7 genuine end to end in Docker -----------------------------------------------------------------------------------------------------
def _docker_ok():
    try:
        from backend.execution.docker_test_sandbox import docker_available
        return docker_available()
    except Exception:
        return False


@pytest.mark.skipif(not _docker_ok(), reason="Docker is not available: the genuine experiment was NOT run")
def test_genuine_experiment_and_promotion_in_docker(engine, sample, monkeypatch):
    """Discover the real N+1 -> two candidates (fixed answers instead of the local model) -> tests in the Docker
    sandbox, Security Guardian re-check, side-by-side latency measurement -> the candidate that drops authors is
    rejected by the tests, the JOIN is measured faster and selected -> the project is unchanged until approval ->
    promotion through Autopilot (checks, the same re-measurement, apply) -> final tests -> memory."""
    monkeypatch.setenv("AIFORGE_TEST_SANDBOX", "docker")
    before = source_revision(sample)
    exp = ran(engine, sample, max_candidates=2)
    assert exp.status == "evaluated", (exp.error, exp.outcome_reasons)
    c1, c2 = exp.candidates
    assert c2.failure_kind == "candidate_defect" and not c2.eligible
    assert c2.correctness["tests"]["environment"].startswith("Docker") and c2.correctness["tests"]["counts"].get("failed")
    assert c1.correctness["accepted"] and c1.security["status"] == "evaluated" and not c1.security["new_serious"]
    target = c1.performance["target_rows"][0]
    assert target["before"]["median_ms"] > target["after"]["median_ms"] and len(target["after"]["rep_medians_ms"]) >= 2
    assert c1.performance["decision"] == "improved", c1.performance["reasons"]
    assert exp.selected == "c1" and exp.outcome == "awaiting_approval"
    assert source_revision(sample) == before                                       # untouched before approval
    engine.approve("p1", sample, "u1", exp.id)
    engine.promote("p1", sample, "u1", exp.id)
    e = engine.store.get("p1", "experiments", exp.id)
    assert e.promotion.status == "promoted", (e.promotion.error, e.promotion.gate, e.outcome_reasons)
    assert e.promotion.gate["decision"] == "improved" and e.promotion.final_tests.status == "passed"
    assert e.outcome == "validated_improvement" and "LEFT JOIN" in (sample / "backend" / "main.py").read_text(encoding="utf-8")
    ex = engine.autopilot.store.get("p1", "executions", e.promotion.execution_id)
    assert next(c for c in ex.after if c.check_id == "tests").environment.startswith("Docker")
    from backend.chaos.sandbox import _docker
    assert not _docker("ps", "-a", "-q", "--filter", "name=aiforge", timeout=30).stdout.split()
    rec = next(r for r in engine.store.list(memory.MEMORY_KEY, "memory") if r.experiment_id == exp.id and r.selected)
    assert rec.final_outcome == "validated_improvement" and rec.measured["median_change_pct"] < 0
    print(json.dumps({"median_before_ms": target["before"]["median_ms"], "median_after_ms": target["after"]["median_ms"],
                      "change_pct": target["median_change_pct"], "noise_pct": target["noise_pct"]}))
