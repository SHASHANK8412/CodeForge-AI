"""
AIForge Time Machine tests. Real Autopilot executions (write_files plans, the project's tests) produce the
ledger events; the Regression Detective then works from those recorded changes. Fast tests run the sample's
tests with the local sandbox (tests/conftest.py); the genuine test at the end runs them in Docker.

The scenario: three recorded AIForge changes are applied, each passing the tests that existed at the time.
The second one breaks an edge case nobody tested. A person then adds a test for that edge case: it fails.
"""

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.evolution.autopilot.models import Plan, PlanTask
from backend.evolution.autopilot.plans import STRATEGY_AGENT
from backend.evolution.autopilot.service import AutopilotService
from backend.evolution.autopilot.store import AutopilotStore
from backend.time_machine import state as st
from backend.time_machine.ledger import Event, Ledger, new_id
from backend.time_machine.recorder import emit, file_records, fingerprint
from backend.time_machine.service import JobStore, TimeMachine, TimeMachineError

CALC = '''def discount(price, percent):
    """Price after a percentage discount; never below zero."""
    return max(0.0, round(price * (1 - percent / 100), 2))
'''
CALC_MUL = CALC + '''

def multiply(a, b):
    return a * b
'''
CALC_BROKEN = CALC_MUL.replace("return max(0.0, round(price * (1 - percent / 100), 2))",
                               "return round(price * (1 - percent / 100), 2)")       # the floor at zero is gone
TESTS = '''from calc import discount


def test_discount():
    assert discount(100, 10) == 90.0
'''
EDGE_TEST = '''from calc import discount


def test_discount_never_negative():
    assert discount(50, 150) == 0.0
'''
SECRET = "sk-" + "abcdefghijklmnopqrstuvwxyz0123456789"


def write(root, files):
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "shop"
    write(root, {"calc.py": CALC, "tests/test_calc.py": TESTS, "README.md": "# Shop\n"})
    return root


@pytest.fixture
def tm(tmp_path, monkeypatch):
    import backend.evolution.autopilot.service as aps
    import backend.time_machine.recorder as rec
    ledger = Ledger(tmp_path / "ledger")
    monkeypatch.setattr(rec, "global_ledger", ledger)
    ap = AutopilotService(AutopilotStore(tmp_path / "ap"), background=False)
    monkeypatch.setattr(aps, "global_autopilot_service", ap)
    machine = TimeMachine(ledger, JobStore(tmp_path / "jobs"), background=False)
    machine.ap = ap
    return machine


def change(tm, project, files, title):
    """A real Autopilot execution of a write_files plan (approval, checks with the project's tests, apply)."""
    ap = tm.ap
    plan = Plan(id=f"pln_{abs(hash(title)) % 10**8}", project_id="p1", user_id="u1", objective=title, finding_ids=[],
                tasks=[PlanTask(id="t1", title=title, finding_ids=[], files=sorted(files), strategy="write_files",
                                agent=STRATEGY_AGENT["write_files"], modification=title, contents=files)],
                expected_files=sorted(files), agents=[], checks=[], risks=[], assumptions=[], approval_required=[],
                completion_criteria=[])
    ap.store.put("p1", "plans", plan)
    ap.decide("p1", plan.id, "u1", "approved")
    e = ap.execute("p1", plan.id, "u1", project, include_tests=True)
    assert e.status == "completed" and e.applied_to_project, (e.status, e.error)
    return e


def history(tm, project):
    e1 = change(tm, project, {"calc.py": CALC_MUL}, "add multiply")
    e2 = change(tm, project, {"calc.py": CALC_BROKEN}, "simplify discount")
    e3 = change(tm, project, {"docs/notes.md": "release notes\n"}, "add notes")
    write(project, {"tests/test_edge.py": EDGE_TEST})            # a person adds a test: not an AIForge change
    return e1, e2, e3


# 1 the ledger ------------------------------------------------------------------------------------------------------------
def test_events_are_appended_in_order_and_hash_chained(tmp_path):
    ledger = Ledger(tmp_path / "l")
    ids = [ledger.append(Event(id=new_id(), project_id="p1", type="task_created", source="test", summary=f"e{i}")).id
           for i in range(5)]
    events = ledger.events("p1")
    assert [e.id for e in events] == ids and [e.seq for e in events] == [1, 2, 3, 4, 5]
    assert events[1].prev_hash == events[0].hash and ledger.verify("p1") == {"valid": True, "events": 5}
    path = ledger._path("p1")
    lines = path.read_text(encoding="utf-8").splitlines()
    tampered = json.loads(lines[2])
    tampered["summary"] = "rewritten history"
    lines[2] = json.dumps(tampered, separators=(",", ":"))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    check = ledger.verify("p1")
    assert check["valid"] is False and check["broken_at"] == 3


def test_events_are_validated_and_corrections_are_new_events(tmp_path):
    ledger = Ledger(tmp_path / "l")
    with pytest.raises(ValueError):
        ledger.append(Event(id=new_id(), project_id="p1", type="made_up", source="x"))
    with pytest.raises(ValueError):
        ledger.append(Event(id=new_id(), project_id="p1", type="correction", source="x"))
    first = ledger.append(Event(id=new_id(), project_id="p1", type="test_executed", source="x", outcome="failure"))
    ledger.append(Event(id=new_id(), project_id="p1", type="correction", source="user u1", refs={"corrects": first.id},
                        summary="the failure was an infrastructure outage"))
    assert len(ledger.events("p1")) == 2 and ledger.get("p1", first.id).outcome == "failure"     # never rewritten
    with pytest.raises(ValueError):
        ledger.append(Event(id=new_id(), project_id="../etc", type="task_created", source="x"))


def test_secrets_are_redacted_before_they_reach_disk(tmp_path):
    ledger = Ledger(tmp_path / "l")
    emit("p1", "agent_completed", "Backend Agent", f"used key {SECRET}", data={"prompt": f"token={SECRET}", "nested": [SECRET]},
         config={"api_key": SECRET}, error=f"failed with {SECRET}", ledger=ledger)
    raw = (tmp_path / "l" / "ledger" / "p1.jsonl").read_text(encoding="utf-8")
    assert SECRET not in raw and "REDACTED" in raw
    sha, stored = ledger.put_blob(f"KEY = '{SECRET}'\n")
    assert stored is False and not ledger.has_blob(sha)                # a secret-bearing file is hashed, not stored


def test_content_store_detects_damage(tmp_path):
    ledger = Ledger(tmp_path / "l")
    sha, ok = ledger.put_blob("print('hi')\n")
    assert ok and ledger.get_blob(sha) == "print('hi')\n"
    (tmp_path / "l" / "blobs" / sha[:2] / sha).write_text("print('changed')\n", encoding="utf-8")
    assert ledger.get_blob(sha) is None                                 # integrity check fails: not served


def test_query_filters_and_bounded_pages(tmp_path):
    ledger = Ledger(tmp_path / "l")
    for i in range(30):
        emit("p1", "test_executed" if i % 3 == 0 else "agent_started", "Autopilot" if i % 2 else "Guardian", f"event {i}",
             task_id=f"t{i % 4}", ledger=ledger)
    page = ledger.query("p1", limit=1000)
    assert page["limit"] == 200 and page["total"] == 30 and page["items"][0].summary == "event 29"
    assert ledger.query("p1", types=["test_executed"])["total"] == 10
    assert ledger.query("p1", task_id="t1", limit=3, offset=3)["items"][0].task_id == "t1"


def test_recording_never_breaks_the_caller(tmp_path):
    assert emit("../bad", "task_created", "x", ledger=Ledger(tmp_path / "l")) is None


def test_fingerprints_match_reconstructed_states(project, tmp_path):
    ledger = Ledger(tmp_path / "l")
    revision, commit = fingerprint(project)
    files, unstored = st.current_map(project, ledger)
    assert st.revision_of(files) == revision and commit is None and unstored == []
    folder, missing = st.materialize(files, ledger)
    assert missing == [] and fingerprint(folder)[0] == revision


# 2 recorded history from real subsystems ----------------------------------------------------------------------------------
def test_autopilot_executions_are_recorded_with_file_versions(tm, project):
    e1 = change(tm, project, {"calc.py": CALC_MUL}, "add multiply")
    events = tm.ledger.events("p1")
    types = [e.type for e in events]
    assert types == ["approval_granted", "agent_started", "test_executed", "test_executed", "patch_applied", "task_completed"]
    applied = events[4]
    assert applied.refs["execution_id"] == e1.id and applied.files[0]["path"] == "calc.py"
    nl = lambda t: t.replace("\r\n", "\n")  # noqa: E731 - the ledger keeps exact bytes (CRLF on Windows checkouts)
    assert nl(tm.ledger.get_blob(applied.files[0]["after"])) == CALC_MUL and nl(tm.ledger.get_blob(applied.files[0]["before"])) == CALC
    assert tm.ledger.get_blob(applied.files[0]["after"]).encode() == (project / "calc.py").read_bytes()
    assert applied.revision == fingerprint(project)[0]
    assert events[1].parents == [events[0].id]                          # recorded link: approval -> execution
    assert all(e.parents for e in events[2:])


def test_timeline_graph_and_replay(tm, project):
    e1, e2, _ = history(tm, project)
    page = tm.timeline("p1", types=["patch_applied"])
    assert page["total"] == 3 and page["integrity"]["valid"]
    g = tm.graph("p1", task_id=e2.id)
    kinds = {e["kind"] for e in g["edges"]}
    assert "recorded" in kinds and all(e["kind"] in g["legend"] for e in g["edges"])
    assert any(n["type"] == "approval_granted" for n in g["nodes"])     # a recorded ancestor outside the task
    full = tm.graph("p1")
    assert any(e["kind"] == "file" and "calc.py" in e["note"] for e in full["edges"])
    r = tm.replay("p1", e2.id)
    assert r["complete"] and "nothing was re-executed" in r["mode"]
    diff = next(d for s in r["steps"] for d in s["diffs"])
    assert diff["available"] and "-    return max(0.0" in diff["diff"]
    with pytest.raises(KeyError):
        tm.replay("p1", "exe_unknown")


def test_replay_reports_unstored_content(tm, project):
    write(project, {"config.py": "X = 1\n"})
    change(tm, project, {"config.py": f"API_KEY = '{SECRET}'\n"}, "configure key")
    r = tm.replay("p1", tm.ledger.query("p1", types=["patch_applied"])["items"][0].task_id)
    d = r["steps"][-2]["diffs"][0] if r["steps"][-2]["diffs"] else next(x for s in r["steps"] for x in s["diffs"])
    assert d["available"] is False and SECRET not in json.dumps(r)


# 3 checkpoints and restoration --------------------------------------------------------------------------------------------
def test_preview_never_offers_to_overwrite_unrecorded_work(tm, project):
    cp = tm.checkpoint("p1", project, "u1", "before work")
    change(tm, project, {"calc.py": CALC_MUL}, "add multiply")
    write(project, {"README.md": "# Shop\nedited by a person\n"})
    pv = tm.preview("p1", project, {"checkpoint_id": cp.id})
    by = {r["path"]: r for r in pv["rows"]}
    assert by["calc.py"]["action"] == "restore" and by["README.md"]["action"] == "conflict"
    assert pv["restore"] == 1 and pv["conflicts"] == 1


def test_restore_needs_approval_of_the_exact_preview(tm, project):
    cp = tm.checkpoint("p1", project, "u1", "before work")
    change(tm, project, {"calc.py": CALC_MUL}, "add multiply")
    write(project, {"README.md": "# Shop\nedited by a person\n"})
    pv = tm.preview("p1", project, {"checkpoint_id": cp.id})
    with pytest.raises(TimeMachineError, match="approve"):
        tm.restore("p1", project, "u1", {"checkpoint_id": cp.id}, pv["token"], approved=False)
    write(project, {"docs/new.md": "made after the preview\n"})
    with pytest.raises(TimeMachineError, match="changed since the preview"):
        tm.restore("p1", project, "u1", {"checkpoint_id": cp.id}, pv["token"], approved=True)
    pv = tm.preview("p1", project, {"checkpoint_id": cp.id})
    out = tm.restore("p1", project, "u1", {"checkpoint_id": cp.id}, pv["token"], approved=True)
    assert out["restored"] == ["calc.py"] and set(out["conflicts_left"]) == {"README.md", "docs/new.md"}
    assert (project / "calc.py").read_text(encoding="utf-8") == CALC
    assert "edited by a person" in (project / "README.md").read_text(encoding="utf-8")      # preserved
    assert (project / "docs" / "new.md").exists()                                              # preserved
    assert out["tests"]["status"] == "passed" and tm.ledger.get("p1", out["recovery_checkpoint"]).type == "checkpoint_created"


def test_isolated_restore_leaves_the_project_alone(tm, project):
    cp = tm.checkpoint("p1", project, "u1", "start")
    change(tm, project, {"calc.py": CALC_MUL}, "add multiply")
    before = fingerprint(project)[0]
    out = tm.restore_isolated("p1", project, "u1", {"checkpoint_id": cp.id})
    assert out["tests"]["status"] == "passed" and out["revision"] == cp.revision and fingerprint(project)[0] == before


# 4 the Regression Detective -----------------------------------------------------------------------------------------------
def test_the_detective_finds_and_confirms_the_breaking_change(tm, project):
    _, e2, _ = history(tm, project)
    before = fingerprint(project)[0]
    job = tm.investigate("p1", project, "u1")
    r = tm.jobs.get("p1", "jobs", job.id).result
    assert r["current"]["status"] == "failed" and "tests/test_edge.py::test_discount_never_negative" in r["current"]["failing"]
    assert r["verdict"] == "confirmed", r
    assert r["suspect"]["task_id"] == e2.id and r["suspect"]["files"] == ["calc.py"]
    assert r["proposal"]["tests_after_revert"] == "passed" and len(r["changes"]) == 3
    assert "oldest reconstructable state" in r["known_good"]["how"]      # the new test changed every recorded revision
    assert fingerprint(project)[0] == before                               # investigating changed nothing
    steps = tm.jobs.get("p1", "jobs", job.id).steps
    assert all(s["status"] in ("passed", "failed") for s in steps) and len(steps) == r["test_runs"]
    ev = tm.ledger.query("p1", types=["investigation_completed"])["items"][0]
    assert ev.parents == [r["suspect"]["change"]]
    # the proposed revert touches only the file that change wrote; the person's test stays
    pv = tm.preview("p1", project, {"revert_change_id": r["suspect"]["change"]})
    assert [x["path"] for x in pv["rows"] if x["action"] == "restore"] == ["calc.py"]
    out = tm.restore("p1", project, "u1", {"revert_change_id": r["suspect"]["change"]}, pv["token"], approved=True)
    assert out["tests"]["status"] == "passed" and (project / "tests" / "test_edge.py").exists()
    assert "def multiply" in (project / "calc.py").read_text(encoding="utf-8")       # the later change is kept


def test_no_failure_means_nothing_is_claimed(tm, project):
    change(tm, project, {"calc.py": CALC_MUL}, "add multiply")
    job = tm.investigate("p1", project, "u1")
    r = tm.jobs.get("p1", "jobs", job.id).result
    assert r["verdict"] == "not_reproduced" and "suspect" not in r


def test_unrecorded_edits_limit_the_investigation(tm, project):
    change(tm, project, {"calc.py": CALC_MUL}, "add multiply")
    write(project, {"calc.py": CALC_MUL + "\nraise RuntimeError('edited by hand')\n"})
    job = tm.investigate("p1", project, "u1")
    r = tm.jobs.get("p1", "jobs", job.id).result
    assert r["verdict"] == "inconclusive" and any("cannot be reconstructed" in x for x in r["limitations"])


# 5 experimental rerun -----------------------------------------------------------------------------------------------------
def test_rerun_is_isolated_and_compared_with_the_record(tm, project):
    e2 = change(tm, project, {"calc.py": CALC_BROKEN}, "simplify discount")
    change(tm, project, {"docs/notes.md": "notes\n"}, "add notes")
    before = fingerprint(project)[0]
    job = tm.rerun("p1", project, "u1", e2.id)
    r = tm.jobs.get("p1", "jobs", job.id).result
    assert "NOT a reproduction" in r["mode"] and r["rerun_status"] == "completed" and r["identical_output"] is True
    assert r["tests"]["recorded"]["status"] == r["tests"]["rerun"]["status"] == "passed"
    assert fingerprint(project)[0] == before
    assert all(e.task_id != r.get("rerun_history") for e in tm.ledger.events("p1"))   # rerun events kept separate
    assert tm.ledger.query("p1", types=["patch_applied"])["total"] == 2


# 6 API -------------------------------------------------------------------------------------------------------------------
@pytest.fixture
def api(tm, project, monkeypatch):
    import backend.routes.export as export
    import backend.time_machine.routes as routes
    from backend.auth.dependencies import get_current_user
    from backend.generation.store import global_generation_store
    monkeypatch.setattr(routes, "global_time_machine", tm)
    records = {"gen_mine": {"generation_id": "gen_mine", "user_id": "alice", "status": "completed", "project_path": str(project)},
               "gen_theirs": {"generation_id": "gen_theirs", "user_id": "bob", "status": "completed", "project_path": str(project)}}
    monkeypatch.setattr(global_generation_store, "get", lambda gid, default=None: records.get(gid, default))
    monkeypatch.setattr(export, "_safe_project_dir", lambda p: project if p == str(project) else None)
    app = FastAPI()
    app.include_router(routes.time_machine_router)
    app.dependency_overrides[get_current_user] = lambda: {"id": "alice"}
    return TestClient(app)


def test_api_access_history_and_restore_flow(api, tm):
    base = "/api/projects/gen_mine/time-machine"
    assert api.get("/api/projects/gen_theirs/time-machine/events").status_code == 403
    assert api.get("/api/projects/missing/time-machine/events").status_code == 404
    emit("gen_mine", "task_created", "Generation pipeline", "generation requested", ledger=tm.ledger)
    page = api.get(f"{base}/events", params={"limit": 500}).json()
    assert page["limit"] == 200 and page["total"] == 1 and page["integrity"]["valid"]
    eid = page["items"][0]["id"]
    assert api.get(f"{base}/events/{eid}").json()["event"]["type"] == "task_created"
    assert api.get(f"{base}/events/tme_missing").status_code == 404
    cp = api.post(f"{base}/checkpoints", json={"name": "start"}).json()["checkpoint"]
    assert api.get(f"{base}/checkpoints").json()["checkpoints"][0]["id"] == cp["id"]
    pv = api.post(f"{base}/restore/preview", json={"checkpoint_id": cp["id"]}).json()
    assert pv["rows"] == []
    r = api.post(f"{base}/restore", json={"checkpoint_id": cp["id"], "token": pv["token"], "approved": False})
    assert r.status_code == 400
    assert api.post(f"{base}/investigations").status_code == 202
    jobs = api.get(f"{base}/jobs").json()["jobs"]
    assert jobs and jobs[0]["kind"] == "investigation" and api.get(f"{base}/graph").json()["legend"]


def test_the_page_uses_the_real_api():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2] / "frontend" / "src"
    service = (root / "services" / "timeMachine.js").read_text(encoding="utf-8")
    page = (root / "pages" / "TimeMachinePage.jsx").read_text(encoding="utf-8")
    for path in ("/events", "/graph", "/replay", "/checkpoints", "/restore/preview", "/restore", "/investigations", "/reruns", "/jobs"):
        assert path in service
    assert "approved: true" in service and "token" in page
    for fake in ("Math.random", "mockData", "fakeScore"):
        assert fake not in page


# 7 genuine: the project's tests in Docker ------------------------------------------------------------------------------------
def _docker_ok():
    try:
        from backend.execution.docker_test_sandbox import docker_available
        return docker_available()
    except Exception:
        return False


@pytest.mark.skipif(not _docker_ok(), reason="Docker is not available: the genuine investigation was NOT run")
def test_genuine_regression_investigation_in_docker(tm, project, monkeypatch):
    """Recorded AIForge changes (tests in the Docker sandbox) -> a person's new test fails -> the Detective reproduces
    the failure in an isolated copy, bisects the recorded changes and confirms the cause -> a checkpoint is restored
    into a separate folder and tested there -> the project stays as it was until an approved restore."""
    monkeypatch.setenv("AIFORGE_TEST_SANDBOX", "docker")
    cp = tm.checkpoint("p1", project, "u1", "before the AIForge changes")
    _, e2, _ = history(tm, project)
    before = fingerprint(project)[0]
    job = tm.investigate("p1", project, "u1")
    r = tm.jobs.get("p1", "jobs", job.id).result
    steps = tm.jobs.get("p1", "jobs", job.id).steps
    assert all(s["environment"].startswith("Docker") for s in steps if s.get("environment")), steps
    assert r["verdict"] == "confirmed" and r["suspect"]["task_id"] == e2.id, r
    iso = tm.restore_isolated("p1", project, "u1", {"checkpoint_id": cp.id})
    assert iso["tests"]["environment"].startswith("Docker") and iso["tests"]["status"] == "passed"   # taken before the new test
    assert fingerprint(project)[0] == before                                                       # untouched
    pv = tm.preview("p1", project, {"revert_change_id": r["suspect"]["change"]})
    out = tm.restore("p1", project, "u1", {"revert_change_id": r["suspect"]["change"]}, pv["token"], approved=True)
    assert out["tests"]["status"] == "passed" and out["tests"]["environment"].startswith("Docker")
    print(json.dumps({"verdict": r["verdict"], "test_runs": r["test_runs"], "suspect": r["suspect"]["summary"]}))
