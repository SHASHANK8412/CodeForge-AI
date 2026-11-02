"""
AIForge Autopilot: analysis, findings, plans, approved execution with validation, and the API.

Model calls are replaced by stubs; the static tools (ast, ruff, bandit, the secret scanner) run
for real against small projects written to a temporary folder.
"""

import json
import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.evolution.autopilot import validation
from backend.evolution.autopilot.codebase import build_project_map
from backend.evolution.autopilot.findings import filter_findings
from backend.evolution.autopilot.models import CheckResult, FindingStatus, PlanStatus
from backend.evolution.autopilot.plans import PlanError
from backend.evolution.autopilot.redact import redact
from backend.evolution.autopilot.service import AutopilotService
from backend.evolution.autopilot.store import AutopilotStore

SECRET = "sk-" + "abcdefghijklmnopqrstuvwxyz0123456789"
MAIN = (
    "import os\n"
    "import requests\n"
    "from fastapi import FastAPI\n"
    "from app.models import Item\n"
    "\n"
    "app = FastAPI()\n"
    "\n"
    "\n"
    "@app.get('/items')\n"
    "def list_items():\n"
    "    return requests.get('http://example.invalid')\n"
)
MODELS = (
    "from pydantic import BaseModel\n"
    "\n"
    "\n"
    "class Item(BaseModel):\n"
    "    name: str\n"
)
UTIL = (
    "def parse(value):\n"
    "    try:\n"
    "        return int(value)\n"
    "    except:\n"
    "        return None\n"
)
UTIL_FIXED = UTIL.replace("    except:\n", "    except ValueError:\n")


def write(root, files):
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "shop"
    write(root, {"app/__init__.py": "", "app/main.py": MAIN, "app/models.py": MODELS, "app/util.py": UTIL,
                 "requirements.txt": "fastapi\npydantic\n",
                 "frontend/src/App.jsx": "export default function App() {\n  fetch('/items')\n  return null\n}\n",
                 "frontend/package.json": json.dumps({"dependencies": {"react": "19"}})})
    return root


@pytest.fixture
def svc(tmp_path):
    return AutopilotService(AutopilotStore(tmp_path / "store"), background=False)


def analyze(svc, project, pid="p1"):
    analysis = svc.start_analysis(pid, project, "u1")
    analysis = svc.store.get(pid, "analyses", analysis.id)
    assert analysis.status == "completed", analysis.error
    return analysis


def findings_by_rule(svc, pid="p1"):
    out = {}
    for f in svc.store.list(pid, "findings"):
        out.setdefault(f.rule_id, []).append(f)
    return out


def approved_plan(svc, ids, pid="p1"):
    plan = svc.create_plan(pid, "u1", ids)
    return svc.decide(pid, plan.id, "u1", "approved")


# 1 ------------------------------------------------------------------------------------------------
def test_project_map_is_built_from_the_code(project):
    m = build_project_map(project)
    assert {"method": "GET", "path": "/items", "handler": "list_items", "file": "app/main.py", "line": 10} in m["routes"]
    assert any(x["name"] == "Item" and x["kind"] == "schema" for x in m["models"])
    assert any(c["name"] == "App" for c in m["components"])
    assert "FastAPI" in m["stack"] and "React" in m["stack"]
    assert "app/main.py" in m["entry_points"]
    assert m["api_calls"] == [{"target": "/items", "file": "frontend/src/App.jsx"}]


# 2 ------------------------------------------------------------------------------------------------
def test_scan_skips_dependencies_secrets_and_links(project):
    write(project, {"node_modules/x/index.js": "x", ".venv/lib/a.py": "x", ".env": f"KEY={SECRET}\n"})
    files = build_project_map(project)["files"]
    assert not [f for f in files if f.startswith(("node_modules", ".venv")) or f == ".env"]
    try:
        os.symlink(project.parent, project / "link")
    except (OSError, NotImplementedError):
        return
    assert not [f for f in build_project_map(project)["files"] if f.startswith("link")]


# 3 ------------------------------------------------------------------------------------------------
def test_syntax_error_is_a_critical_confirmed_finding(svc, project):
    write(project, {"app/broken.py": "def f(:\n    pass\n"})
    analyze(svc, project)
    syntax = findings_by_rule(svc)["PY-SYNTAX"]
    assert len(syntax) == 1 and syntax[0].severity.value == "critical" and syntax[0].confidence.value == "confirmed"
    assert syntax[0].priority == "P1" and syntax[0].file == "app/broken.py"
    # reported once, not again by the quality gate
    assert not [f for f in svc.store.list("p1", "findings") if f.file == "app/broken.py" and "syntax" in f.rule_id.lower()
                and f.rule_id != "PY-SYNTAX"]


# 4 ------------------------------------------------------------------------------------------------
def test_undeclared_dependency_is_found_and_declared_ones_are_not(svc, project):
    analyze(svc, project)
    deps = findings_by_rule(svc)["DEP-PY-UNDECLARED"]
    assert [d.title for d in deps] == ["Python package 'requests' is imported but not declared"]
    assert deps[0].fix_strategy == "add_requirements"


# 5 ------------------------------------------------------------------------------------------------
def test_secrets_are_reported_but_never_stored_in_clear(svc, project, tmp_path):
    write(project, {"app/config.py": f"API_KEY = '{SECRET}'\n"})
    analyze(svc, project)
    secrets = findings_by_rule(svc)["SEC-SECRET"]
    assert secrets and secrets[0].severity.value == "critical" and secrets[0].fix_strategy == "manual"
    stored = (tmp_path / "store" / "p1.json").read_text(encoding="utf-8")
    assert SECRET not in stored
    assert SECRET not in redact(f"token={SECRET} https://user:hunter22@db.example/x")
    assert "hunter22" not in redact("postgres://user:hunter22@db.example/x")


# 6 ------------------------------------------------------------------------------------------------
def test_finding_ids_are_stable_across_runs_and_unrelated_edits(svc, project):
    analyze(svc, project)
    bare = findings_by_rule(svc)["MAINT-BARE-EXCEPT"][0]
    write(project, {"app/util.py": "# a comment added above\n\n" + UTIL})
    analysis = analyze(svc, project)
    assert bare.id in analysis.finding_ids
    moved = svc.store.get("p1", "findings", bare.id)
    assert moved.line_start == bare.line_start + 2 and moved.first_seen == bare.first_seen


# 7 ------------------------------------------------------------------------------------------------
def test_history_resolves_fixed_findings_and_keeps_dismissals(svc, project):
    analyze(svc, project)
    by_rule = findings_by_rule(svc)
    bare, dep = by_rule["MAINT-BARE-EXCEPT"][0], by_rule["DEP-PY-UNDECLARED"][0]
    svc.dismiss("p1", dep.id)
    write(project, {"app/util.py": UTIL_FIXED})
    analysis = analyze(svc, project)
    assert svc.store.get("p1", "findings", bare.id).status == FindingStatus.RESOLVED
    assert svc.store.get("p1", "findings", dep.id).status == FindingStatus.DISMISSED
    assert analysis.summary["resolved_since_last"] >= 1


# 8 ------------------------------------------------------------------------------------------------
def test_priorities_follow_severity_and_confidence_with_reasons(svc, project):
    write(project, {"app/broken.py": "def f(:\n    pass\n",
                    "app/loop.py": "import requests\n\ndef f(ids):\n    for i in ids:\n        requests.get(i)\n"})
    analyze(svc, project)
    by_rule = findings_by_rule(svc)
    assert by_rule["PY-SYNTAX"][0].priority == "P1"
    perf = by_rule["PERF-CALL-IN-LOOP"][0]
    assert perf.confidence.value == "suspected" and perf.priority == "P4"
    assert "confidence suspected" in perf.priority_reasons and "needs a person to fix" in perf.priority_reasons


# 9 ------------------------------------------------------------------------------------------------
def test_findings_can_be_filtered_and_paginated(svc, project):
    analyze(svc, project)
    items = svc.store.list("p1", "findings")
    maint = filter_findings(items, category="maintainability")
    assert maint["total"] >= 1 and all(f.category.value == "maintainability" for f in maint["items"])
    assert filter_findings(items, file="app/util.py")["total"] >= 1
    page = filter_findings(items, limit=1, offset=1)
    assert page["total"] == len(items) and len(page["items"]) == 1
    assert filter_findings(items, q="requests")["total"] >= 1


# 10 -----------------------------------------------------------------------------------------------
def test_plan_orders_tasks_and_refuses_closed_findings(svc, project):
    write(project, {"app/config.py": f"API_KEY = '{SECRET}'\n"})
    analyze(svc, project)
    by_rule = findings_by_rule(svc)
    ids = [by_rule["MAINT-BARE-EXCEPT"][0].id, by_rule["SEC-SECRET"][0].id, by_rule["DEP-PY-UNDECLARED"][0].id]
    plan = svc.create_plan("p1", "u1", ids, "harden")
    assert plan.status == PlanStatus.AWAITING_APPROVAL
    assert plan.tasks[0].strategy == "manual" and "secret" in plan.tasks[0].title.lower()   # security first
    assert set(plan.expected_files) == {"app/main.py", "requirements.txt", "app/util.py"}
    assert any("requirements" in a for a in plan.approval_required)
    assert {svc.store.get("p1", "findings", i).status for i in ids} == {FindingStatus.PLANNED}
    svc.dismiss("p1", by_rule["PY-F401"][0].id)
    with pytest.raises(PlanError):
        svc.create_plan("p1", "u1", [by_rule["PY-F401"][0].id])
    with pytest.raises(PlanError):
        svc.create_plan("p1", "u1", ["fnd_does_not_exist"])


# 11 -----------------------------------------------------------------------------------------------
def test_nothing_runs_without_approval(svc, project):
    analyze(svc, project)
    plan = svc.create_plan("p1", "u1", [findings_by_rule(svc)["PY-F401"][0].id])
    with pytest.raises(PlanError):
        svc.execute("p1", plan.id, "u1", project, include_tests=False)
    rejected = svc.decide("p1", plan.id, "u1", "rejected", "not now")
    assert rejected.status == PlanStatus.REJECTED and rejected.decisions[-1].note == "not now"
    with pytest.raises(PlanError):
        svc.decide("p1", plan.id, "u1", "approved")
    assert (project / "app/main.py").read_text(encoding="utf-8") == MAIN


# 12 -----------------------------------------------------------------------------------------------
def test_deterministic_fixes_are_applied_validated_and_verified(svc, project):
    analyze(svc, project)
    by_rule = findings_by_rule(svc)
    ids = [f.id for f in by_rule["PY-F401"]] + [by_rule["DEP-PY-UNDECLARED"][0].id]
    plan = approved_plan(svc, ids)
    execution = svc.execute("p1", plan.id, "u1", project, include_tests=False)
    report = svc.report("p1", execution.id)
    assert report["status"] == "completed" and report["applied_to_project"]
    assert "import os" not in (project / "app/main.py").read_text(encoding="utf-8")
    assert (project / "requirements.txt").read_text(encoding="utf-8").split() == ["fastapi", "pydantic", "requests"]
    assert set(execution.verified_findings) == set(ids) and not execution.unresolved_findings
    assert report["verdict"]["evidence"] == "static checks only - tests did not run"
    assert "tests" not in report["checks"]["executed"]
    assert "-import os" in execution.diff
    assert svc.store.get("p1", "plans", plan.id).status == PlanStatus.COMPLETED


# 13 -----------------------------------------------------------------------------------------------
def test_a_change_that_regresses_a_check_is_rejected_and_not_applied(svc, project):
    analyze(svc, project)
    plan = approved_plan(svc, [findings_by_rule(svc)["MAINT-BARE-EXCEPT"][0].id])
    bad = lambda system, prompt: ("### app/util.py\n```python\ndef parse(value):\n    try:\n        return int(valu)\n"
                                  "    except ValueError:\n        return None\n```\n")
    execution = svc.execute("p1", plan.id, "u1", project, generate=bad, include_tests=False)
    assert execution.status == "rejected" and not execution.applied_to_project
    assert any("quality-gate errors" in r for r in execution.verdict["regressions"])
    assert (project / "app/util.py").read_text(encoding="utf-8") == UTIL
    assert svc.store.get("p1", "findings", plan.finding_ids[0]).status == FindingStatus.FIX_FAILED


# 14 -----------------------------------------------------------------------------------------------
def test_changes_outside_the_plan_need_approval(svc, project):
    analyze(svc, project)
    plan = approved_plan(svc, [findings_by_rule(svc)["MAINT-BARE-EXCEPT"][0].id])
    reply = ("### app/util.py\n```python\n" + UTIL_FIXED + "```\n### app/helpers.py\n```python\nX = 1\n```\n")
    execution = svc.execute("p1", plan.id, "u1", project, generate=lambda s, p: reply, include_tests=False)
    assert execution.status == "needs_approval" and "app/helpers.py" in execution.error
    assert not (project / "app/helpers.py").exists()
    assert svc.store.get("p1", "plans", plan.id).status == PlanStatus.AWAITING_APPROVAL
    with pytest.raises(PlanError):
        svc.decide("p1", plan.id, "u1", "approved", extra_files=["../outside.py"])
    svc.decide("p1", plan.id, "u1", "approved", extra_files=["app/helpers.py"])
    execution = svc.execute("p1", plan.id, "u1", project, generate=lambda s, p: reply, include_tests=False)
    assert execution.status == "completed", execution.error
    assert (project / "app/helpers.py").exists() and (project / "app/util.py").read_text(encoding="utf-8") == UTIL_FIXED


# 15 -----------------------------------------------------------------------------------------------
def test_user_edits_made_during_a_run_are_never_overwritten(svc, project):
    analyze(svc, project)
    plan = approved_plan(svc, [findings_by_rule(svc)["MAINT-BARE-EXCEPT"][0].id])
    user_version = UTIL + "\n# edited by the user meanwhile\n"

    def model(system, prompt):
        (project / "app/util.py").write_text(user_version, encoding="utf-8")
        return "### app/util.py\n```python\n" + UTIL_FIXED + "```\n"
    execution = svc.execute("p1", plan.id, "u1", project, generate=model, include_tests=False)
    assert execution.status == "failed" and "changed while Autopilot was working" in execution.error
    assert (project / "app/util.py").read_text(encoding="utf-8") == user_version


# 16 -----------------------------------------------------------------------------------------------
def test_cancelling_a_run_leaves_the_project_untouched(svc, project):
    analyze(svc, project)
    plan = approved_plan(svc, [findings_by_rule(svc)["MAINT-BARE-EXCEPT"][0].id])

    def model(system, prompt):
        running = [e for e in svc.store.list("p1", "executions") if e.status == "running"][0]
        svc.cancel_execution("p1", running.id)
        return "### app/util.py\n```python\n" + UTIL_FIXED + "```\n"
    execution = svc.execute("p1", plan.id, "u1", project, generate=model, include_tests=False)
    assert execution.status == "cancelled" and not execution.applied_to_project
    assert (project / "app/util.py").read_text(encoding="utf-8") == UTIL
    assert svc.store.get("p1", "plans", plan.id).status == PlanStatus.CANCELLED


# 17 -----------------------------------------------------------------------------------------------
def test_tests_that_cannot_run_are_blocked_not_passed(project, monkeypatch):
    import backend.execution.docker_test_sandbox as sandbox
    write(project, {"tests/test_util.py": "from app.util import parse\n\ndef test_parse():\n    assert parse('1') == 1\n"})
    monkeypatch.setenv("AIFORGE_TEST_SANDBOX", "auto")
    monkeypatch.setattr(sandbox, "docker_available", lambda: False)
    result = validation.check_tests(project)
    assert result.status == "blocked" and result.counts == {}
    assert "Docker" in result.output
    assert not (project / "tests" / "__init__.py").exists()          # ran in a copy, project untouched


def _check(check_id, status, **counts):
    return CheckResult(check_id=check_id, label=check_id, environment="test", started_at="t", finished_at="t",
                       status=status, counts=counts)


# 18 -----------------------------------------------------------------------------------------------
def test_comparison_rules():
    passed = [_check("tests", "passed", passed=4)]
    assert validation.compare(passed, [_check("tests", "failed", passed=3, failed=1)])["regressions"]
    assert validation.compare([_check("tests", "failed", passed=3, failed=1)],
                              [_check("tests", "failed", passed=2, failed=2)])["regressions"]
    better = validation.compare([_check("tests", "failed", passed=3, failed=1)], [_check("tests", "passed", passed=4)])
    assert better["accepted"] and better["notes"]
    lost = validation.compare(passed, [_check("tests", "blocked")])
    assert not lost["accepted"] and lost["unverified"]
    never = validation.compare([_check("tests", "blocked")], [_check("tests", "blocked"), _check("quality_gate", "passed")])
    assert never["accepted"] and never["evidence"] == "static checks only - tests did not run"
    assert validation.compare([_check("security_static", "passed", high=0)],
                              [_check("security_static", "failed", high=1)])["regressions"]
    assert validation._test_counts("===== 3 passed, 1 failed, 2 errors in 0.5s =====", "python") == \
        {"passed": 3, "failed": 1, "errors": 2}
    assert validation._test_counts("collected 0 items", "python") == {}


# 19 -----------------------------------------------------------------------------------------------
def test_secret_values_are_never_sent_to_the_model(svc, project):
    secret_line = f"TOKEN = '{SECRET}'"
    write(project, {"app/util.py": UTIL + f"\n{secret_line}\n"})
    analyze(svc, project)
    plan = approved_plan(svc, [findings_by_rule(svc)["MAINT-BARE-EXCEPT"][0].id])
    prompts = []

    def model(system, prompt):
        # the model sees a marker instead of the secret line and keeps it
        prompts.append(prompt)
        marker = next(line for line in prompt.splitlines() if "AIFORGE_HIDDEN_LINE_1" in line)
        return "### app/util.py\n```python\n" + UTIL_FIXED + "\n" + marker + "\n```\n"

    execution = svc.execute("p1", plan.id, "u1", project, generate=model, include_tests=False)
    assert prompts and all(SECRET not in p for p in prompts)
    assert execution.status == "completed", execution.error
    assert (project / "app/util.py").read_text(encoding="utf-8") == UTIL_FIXED + f"\n{secret_line}\n"
    assert SECRET not in execution.diff


def test_a_model_that_alters_a_hidden_secret_line_is_rejected(svc, project):
    write(project, {"app/util.py": UTIL + f"\nTOKEN = '{SECRET}'\n"})
    analyze(svc, project)
    plan = approved_plan(svc, [findings_by_rule(svc)["MAINT-BARE-EXCEPT"][0].id])
    prompts = []

    def model(system, prompt):
        prompts.append(prompt)      # drops the hidden line: the secret cannot be restored, so nothing is applied
        return "### app/util.py\n```python\n" + UTIL_FIXED + "```\n"

    execution = svc.execute("p1", plan.id, "u1", project, generate=model, include_tests=False)
    assert len(prompts) == 2 and "AIFORGE_HIDDEN_LINE" in prompts[1] and "removed or changed" in prompts[1]
    assert all(SECRET not in p for p in prompts)
    assert execution.task_results[0].status == "failed" and "hidden from the model" in execution.task_results[0].detail
    assert execution.status == "failed" and not execution.applied_to_project
    assert (project / "app/util.py").read_text(encoding="utf-8") == UTIL + f"\nTOKEN = '{SECRET}'\n"


def test_jobs_interrupted_by_a_restart_are_closed(tmp_path):
    from backend.evolution.autopilot.models import Analysis, Execution
    store = AutopilotStore(tmp_path / "store")
    store.put("p1", "analyses", Analysis(id="ana_1", project_id="p1", user_id="u1", status="running"))
    store.put("p1", "executions", Execution(id="exe_1", plan_id="pln_1", project_id="p1", user_id="u1", status="running"))
    store.put("p1", "executions", Execution(id="exe_2", plan_id="pln_1", project_id="p1", user_id="u1", status="completed"))
    AutopilotService(store, background=True)            # what the server does at start-up
    assert store.get("p1", "analyses", "ana_1").status == "failed"
    assert "interrupted" in store.get("p1", "executions", "exe_1").error
    assert store.get("p1", "executions", "exe_2").status == "completed"


# 20 -----------------------------------------------------------------------------------------------
@pytest.fixture
def api(tmp_path, project, monkeypatch):
    import backend.evolution.routes as routes
    from backend.auth.dependencies import get_current_user
    from backend.generation.store import global_generation_store
    import backend.routes.export as export
    service = AutopilotService(AutopilotStore(tmp_path / "api-store"), background=False)
    monkeypatch.setattr(routes, "global_autopilot_service", service)
    records = {
        "gen_mine": {"generation_id": "gen_mine", "user_id": "alice", "status": "completed",
                     "project_path": str(project), "created_at": "2026-10-01"},
        "gen_theirs": {"generation_id": "gen_theirs", "user_id": "bob", "status": "completed",
                       "project_path": str(project), "created_at": "2026-10-02"},
    }
    monkeypatch.setattr(global_generation_store, "get", lambda gid, default=None: records.get(gid, default))
    monkeypatch.setattr(global_generation_store, "list_all", lambda: list(records.values()))
    monkeypatch.setattr(export, "_safe_project_dir", lambda p: project if p == str(project) else None)
    app = FastAPI()
    app.include_router(routes.autopilot_evolution_router)
    app.dependency_overrides[get_current_user] = lambda: {"id": "alice"}
    return TestClient(app)


def test_api_flow_with_ownership_and_path_checks(api, project):
    base = "/api/projects/gen_mine/evolution"
    assert [p["project_id"] for p in api.get("/api/evolution/projects").json()["projects"]] == ["gen_mine"]
    assert api.post("/api/projects/gen_theirs/evolution/analyses", json={}).status_code == 403
    assert api.get("/api/projects/..%2F..%2Fetc/evolution/findings").status_code == 404
    assert api.get("/api/projects/nope/evolution/findings").status_code == 404

    analysis = api.post(f"{base}/analyses", json={}).json()["analysis"]
    assert api.get(f"{base}/analyses/latest").json()["analysis"]["id"] == analysis["id"]
    page = api.get(f"{base}/findings", params={"category": "quality", "limit": 50}).json()
    unused = [f for f in page["items"] if f["rule_id"] == "PY-F401"]
    assert unused and page["total"] >= len(unused)
    assert api.get(f"{base}/findings/{unused[0]['id']}").json()["finding"]["evidence"]

    plan = api.post(f"{base}/plans", json={"finding_ids": [unused[0]["id"]]}).json()["plan"]
    assert api.post(f"{base}/plans/{plan['id']}/execute", json={"run_tests": False}).status_code == 409
    assert api.post(f"{base}/plans/{plan['id']}/approve", json={}).json()["plan"]["status"] == "approved"
    execution = api.post(f"{base}/plans/{plan['id']}/execute", json={"run_tests": False}).json()["execution"]
    report = api.get(f"{base}/executions/{execution['id']}/report").json()["report"]
    assert report["status"] == "completed" and report["applied_to_project"]
    assert report["verified_findings"][0]["id"] == unused[0]["id"]
    assert "import os" not in (project / "app/main.py").read_text(encoding="utf-8")
    assert api.get("/api/projects/gen_theirs/evolution/executions").status_code == 403
    assert api.patch(f"{base}/findings/fnd_missing", json={"dismissed": True}).status_code == 404


def test_a_regression_gets_one_bounded_repair_attempt(svc, project):
    analyze(svc, project)
    plan = approved_plan(svc, [findings_by_rule(svc)["MAINT-BARE-EXCEPT"][0].id])
    prompts = []

    def model(system, prompt):
        prompts.append(prompt)
        if len(prompts) == 1:                       # first answer introduces an undefined name
            return "### app/util.py\n```python\n" + UTIL_FIXED.replace("int(value)", "int(valu)") + "```\n"
        return "### app/util.py\n```python\n" + UTIL_FIXED + "```\n"
    execution = svc.execute("p1", plan.id, "u1", project, generate=model, include_tests=False)
    assert execution.status == "completed", execution.error
    assert len(prompts) == 2 and "regress" in prompts[1] and "quality-gate errors" in prompts[1]
    assert any("repair attempt 1: the checks pass" in n for n in execution.verdict["notes"])
    assert (project / "app/util.py").read_text(encoding="utf-8") == UTIL_FIXED
