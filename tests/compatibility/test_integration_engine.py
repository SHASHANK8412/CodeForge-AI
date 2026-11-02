"""
Integration & Compatibility Engine tests. The analysis reads real sample projects; the generated contract tests really
run (under the explicit local sandbox opt-in, tests/conftest.py); the agents' model repair is replaced by fixed
answers. Each section is one of the required behaviours.
"""

import copy
import json
from pathlib import Path

import pytest

from backend.compatibility import analyzer, contract as ct, extract, repair, testgen
from backend.compatibility.models import SharedContract
from backend.compatibility.service import CompatibilityStore, ContractError, IntegrationEngine, final_status, markdown
from tests.compatibility.sample import (API_JS, APP_JSX, APP_JSX_BROKEN, BACKEND, CONTRACT, MODELS_PY, SCHEMA_SQL,
                                        SCHEMA_SQL_BROKEN, project, write)
from tests.test_pipeline_integration import _resume, pipeline  # noqa: F401 - the real generation graph, model calls replaced

ENV = [{"name": "VITE_API_URL", "component": "frontend", "required": False}]


def no_change(system, prompt):
    return "No change is needed."


def engine(tmp_path, generate=no_change, adjudicate=None):
    from backend.evolution.autopilot.service import AutopilotService
    from backend.evolution.autopilot.store import AutopilotStore
    ap = AutopilotService(AutopilotStore(tmp_path / "ap"), background=False)
    return IntegrationEngine(CompatibilityStore(tmp_path / "st"), background=False, generate=generate, adjudicate=adjudicate,
                             autopilot=ap), ap


def contract(**changes):
    c = copy.deepcopy(CONTRACT)
    c["environment"] = ENV
    c.update(changes)
    return c


def shared(payload=None) -> SharedContract:
    c = SharedContract(project_id="p1", **(payload or contract()))
    c.revision = c.compute_revision()
    return c


def findings_of(root: Path, payload=None, previous=None, adjudicate=None):
    snap = extract.snapshot(root)
    found, coverage, _ = analyzer.analyze(shared(payload), snap, previous, adjudicate)
    return found, coverage, snap


def one(found, rule, target, agent=None):
    """The finding for rule + target (+ the responsible agent, when both sides have one)."""
    hits = [f for f in found if f.rule == rule and f.target == target and (agent is None or f.responsible_agent == agent)]
    assert hits, f"no {rule} on {target}" + (f" for {agent}" if agent else "") + f"; found {[(f.rule, f.target, f.responsible_agent) for f in found]}"
    return hits[0]


def has(found, rule, target) -> bool:
    return any(f.rule == rule and f.target == target for f in found)


# 1 matching frontend and backend ---------------------------------------------------------------------------------------------
def test_matching_components_are_compatible_after_their_contract_tests_ran(tmp_path):
    proj = project(tmp_path / "p")
    found, coverage, snap = findings_of(proj)
    blocking = [f for f in found if f.status != "info" and f.severity in ("critical", "high")]
    assert not blocking, blocking
    calls = {(c["method"], c["path"]) for c in snap["frontend"]["calls"]}
    assert calls == {("GET", "/api/tasks"), ("POST", "/api/tasks"), ("GET", "/api/tasks/{}")}, "axios baseURL resolved"
    assert all(c["auth_header"] for c in snap["frontend"]["calls"]), "the interceptor's Authorization header is seen"
    eng, _ = engine(tmp_path)
    eng.register("p1", contract(), "alice", "initial")
    r = eng.start_verify("p1", proj, "alice")
    assert r.status == "COMPATIBLE", (r.report["why"], r.report["warnings"])
    assert r.report["tests_executed"] == r.report["tests_generated"] == r.report["tests_passed"] > 10
    assert {t.kind for t in r.tests} >= {"endpoint_exists", "valid_request", "missing_required_field", "unauthenticated",
                                         "frontend_request", "db_schema", "db_roundtrip"}
    assert not r.repairs and not r.delivery


def test_analysis_alone_is_never_reported_as_compatible(tmp_path):
    proj = project(tmp_path / "p")
    eng, _ = engine(tmp_path)
    eng.register("p1", contract(), "alice", "initial")
    r = eng.analyze("p1", proj, "alice")
    assert r.status == "COMPATIBLE_WITH_WARNINGS"
    assert any("tests were not executed" in w for w in r.report["warnings"])
    eng2, _ = engine(tmp_path / "other")
    assert eng2.analyze("p1", proj, "alice").status == "BLOCKED", "no contract: nothing can be established"


# 2 missing endpoints -------------------------------------------------------------------------------------------------------------
def test_a_missing_endpoint_is_found_statically_and_by_the_contract_tests(tmp_path):
    backend = BACKEND.split('@app.get("/api/tasks/{task_id}"')[0]
    proj = project(tmp_path / "p", backend=backend)
    found, _, _ = findings_of(proj)
    f = one(found, "missing_endpoint", "GET /api/tasks/{task_id}")
    assert f.responsible_agent == "backend" and f.severity == "high" and f.repairable
    eng, _ = engine(tmp_path)
    eng.register("p1", contract(), "alice", "initial")
    r = eng.start_verify("p1", proj, "alice", {"max_repair_attempts": 0})
    assert r.status == "INCOMPATIBLE"
    exists = next(t for t in r.tests if t.kind == "endpoint_exists" and t.target == "GET /api/tasks/{task_id}")
    assert exists.status == "failed" and "no route serves" in exists.detail


# 3 incorrect HTTP methods / paths ------------------------------------------------------------------------------------------------
def test_wrong_methods_and_paths_are_attributed_to_the_side_that_departs(tmp_path):
    found, _, _ = findings_of(project(tmp_path / "p", app=APP_JSX_BROKEN))
    fe = one(found, "incorrect_http_method", "PUT /api/tasks")
    assert fe.responsible_agent == "frontend" and fe.evidence["call"] == "frontend/src/App.jsx:11"
    path = one(found, "incorrect_url_path", "GET /tasks")
    assert path.responsible_agent == "frontend" and path.evidence["contract_path"] == "/api/tasks"
    # the backend serves create as PUT: the backend departs; and where both components agree on PUT, which the contract
    # lacks, that is a contract decision - not a repair of either side
    put_backend = BACKEND.replace('@app.post("/api/tasks"', '@app.put("/api/tasks"')
    found2, _, _ = findings_of(project(tmp_path / "q", app=APP_JSX_BROKEN, backend=put_backend))
    assert one(found2, "incorrect_http_method", "POST /api/tasks", "backend").repairable
    both = one(found2, "frontend_call_not_in_contract", "PUT /api/tasks")
    assert both.responsible_agent == "architect" and both.status == "needs_contract_decision" and not both.repairable


def test_a_vite_proxy_rewrite_is_followed(tmp_path):
    vite = "export default { server: { proxy: { '/api': { target: 'http://localhost:8000', rewrite: (path) => path.replace(/^\\/api/, '') } } } };\n"
    app = APP_JSX_BROKEN.replace("`${API}/tasks`", "'/api/tasks'")
    snap = extract.snapshot(write(tmp_path / "p", {"frontend/vite.config.js": vite, "frontend/src/App.jsx": app}))
    call = next(c for c in snap["frontend"]["calls"] if c["method"] == "GET")
    assert call["path"] == "/tasks" and call["browser_path"] == "/api/tasks", "the backend receives the rewritten path"


# 4 request schema mismatches -----------------------------------------------------------------------------------------------------
def test_request_schema_mismatches_on_both_sides(tmp_path):
    backend = BACKEND.replace("class TaskIn(BaseModel):\n    title: str\n    done: bool = False",
                              "class TaskIn(BaseModel):\n    name: str\n    done: bool")
    proj = project(tmp_path / "p", backend=backend, extra={"frontend/src/api.js": API_JS.replace("{ title, done: false }", "{ taskName: title }")})
    found, _, _ = findings_of(proj)
    be_missing = one(found, "request_field_mismatch", "POST /api/tasks", "backend")
    assert be_missing.responsible_agent == "backend" and "'title'" in be_missing.expected
    assert one(found, "missing_required_field", "POST /api/tasks", "backend").expected.startswith("the contract")
    assert one(found, "optional_field_inconsistency", "POST /api/tasks").severity == "high", "done is optional in the contract"
    keys = {f.key for f in found}
    assert "request_field_mismatch|POST /api/tasks|frontend/src/api.js:13:unknown" in keys
    assert "missing_required_field|POST /api/tasks|frontend/src/api.js:13:missing" in keys


# 5 response schema mismatches -----------------------------------------------------------------------------------------------------
def test_response_schema_mismatches_and_the_taskname_title_case(tmp_path):
    backend = BACKEND.replace("class Task(BaseModel):\n    id: int\n    title: str\n    done: bool",
                              "class Task(BaseModel):\n    id: int\n    title: str")
    proj = project(tmp_path / "p", backend=backend, app=APP_JSX_BROKEN)
    found, _, _ = findings_of(proj)
    be = one(found, "response_field_mismatch", "GET /api/tasks", "backend")
    assert be.responsible_agent == "backend" and "'done'" in be.expected
    fe = next(f for f in found if f.rule == "response_field_mismatch" and f.responsible_agent == "frontend")
    assert fe.evidence["field"] == "taskName" and set(fe.evidence["candidates"]) == {"title", "done"}
    assert fe.basis == "static_heuristic" and "likely" not in fe.evidence, "no name matches: undecided without the model"
    # an ambiguous read is settled by the model only as advice, labelled as such
    found2, _, _ = findings_of(proj, adjudicate=lambda s, p: '{"field": "title", "reason": "the task name"}')
    fe2 = next(f for f in found2 if f.rule == "response_field_mismatch" and f.responsible_agent == "frontend")
    assert fe2.evidence["likely"] == "title" and fe2.evidence["likely_by"] == "model suggestion (advisory)"
    # a model answer outside the candidates is ignored
    found3, _, _ = findings_of(proj, adjudicate=lambda s, p: '{"field": "rm -rf"}')
    assert "likely" not in next(f for f in found3 if f.rule == "response_field_mismatch" and f.responsible_agent == "frontend").evidence


def test_a_naming_convention_mismatch_is_decided_without_a_model(tmp_path):
    payload = contract()
    for e in payload["api"]["endpoints"]:
        for r in e["responses"].values():
            s = r["schema"]
            inner = s.get("items") or s                    # the same TASK schema object is shared by the operations
            if "title" in inner["properties"]:
                inner["properties"]["task_name"] = inner["properties"].pop("title")
                inner["required"] = ["id", "task_name", "done"]
    app = APP_JSX_BROKEN.replace("`${API}/tasks`", "`${API}/api/tasks`")
    found, _, _ = findings_of(project(tmp_path / "p", app=app), payload=payload)
    fe = next(f for f in found if f.rule == "response_field_mismatch" and f.responsible_agent == "frontend")
    assert fe.evidence["likely"] == "task_name" and fe.evidence["likely_by"] == "same name in another naming convention"


# 6 database field mismatches ------------------------------------------------------------------------------------------------------
def test_database_mismatches(tmp_path):
    proj = project(tmp_path / "p", schema=SCHEMA_SQL_BROKEN, extra={"backend/models.py": MODELS_PY})
    found, _, _ = findings_of(proj)
    assert one(found, "db_nullability_mismatch", "entity Task.title").evidence["source"] == "schema"
    assert one(found, "db_field_type_mismatch", "entity Task.done").actual.startswith("string")
    assert one(found, "db_missing_relationship", "entity Task.owner_id").responsible_agent == "database"
    assert has(found, "db_extra_required_column", "entity Task.priority"), "the ORM model rejects contract-shaped records"
    assert has(found, "db_model_schema_drift", "table tasks.priority") and has(found, "db_model_schema_drift", "table tasks.done")


def test_missing_migrations_and_identifier_formats(tmp_path):
    migration = "def upgrade():\n    op.create_table('users', sa.Column('id', sa.Integer()), sa.Column('email', sa.String()))\n"
    proj = project(tmp_path / "p", schema=None, extra={"backend/models.py": MODELS_PY, "alembic.ini": "[alembic]\n",
                                                      "migrations/versions/0001_init.py": migration})
    found, _, _ = findings_of(proj)
    assert has(found, "db_missing_migration", "table tasks")
    payload = contract()
    payload["entities"][0]["fields"][0] = {"name": "id", "type": "string", "format": "uuid", "primary_key": True}
    found2, _, _ = findings_of(project(tmp_path / "q"), payload=payload)
    assert one(found2, "db_identifier_format_mismatch", "GET /api/tasks/{task_id} {task_id}").responsible_agent == "backend"
    assert one(found2, "db_identifier_format_mismatch", "entity Task.id").evidence["source"] == "schema"


# 7 authentication inconsistencies -------------------------------------------------------------------------------------------------
def test_authentication_inconsistencies(tmp_path):
    backend = BACKEND.replace("def create_task(body: TaskIn, user=Depends(get_current_user)):", "def create_task(body: TaskIn):")
    proj = project(tmp_path / "p", backend=backend, app=APP_JSX_BROKEN.replace("`${API}/api/tasks`, { method: 'PUT'", "`${API}/api/tasks`, { method: 'POST'"))
    found, _, _ = findings_of(proj)
    be = one(found, "auth_mismatch", "POST /api/tasks", "backend")
    assert be.severity == "critical" and be.responsible_agent == "backend"
    fe = [f for f in found if f.rule == "auth_mismatch" and f.responsible_agent == "frontend"]
    assert fe and fe[0].evidence["call"] == "frontend/src/App.jsx:11"
    eng, _ = engine(tmp_path)
    eng.register("p1", contract(), "alice", "initial")
    r = eng.start_verify("p1", project(tmp_path / "q", backend=backend), "alice", {"max_repair_attempts": 0})
    unauth = next(t for t in r.tests if t.kind == "unauthenticated")
    assert unauth.status == "failed" and "not rejected" in unauth.detail and r.status == "INCOMPATIBLE"


# 8 contract versions ----------------------------------------------------------------------------------------------------------------
def test_contract_versions_are_explicit_and_traceable(tmp_path):
    eng, _ = engine(tmp_path)
    v1, ch1, _ = eng.register("p1", contract(), "alice", "initial contract")
    assert (v1.version, v1.parent_version, ch1.from_version, ch1.to_version) == (1, None, None, 1)
    same, change, warnings = eng.register("p1", contract(), "bob", "again")
    assert same.version == 1 and change is None and "unchanged" in warnings[0]
    payload = contract()
    payload["api"]["endpoints"][0]["description"] = "list every task"
    v2, ch2, _ = eng.register("p1", payload, "bob", "describe the list operation")
    assert (v2.version, v2.parent_version, v2.author, v2.reason) == (2, 1, "bob", "describe the list operation")
    assert eng.version("p1", 1).revision == v1.revision, "earlier versions are kept unchanged"
    assert [c.to_version for c in eng.changes("p1")] == [1, 2]
    with pytest.raises(ContractError):
        eng.register("p1", payload, "bob", "  ")
    bad = contract()
    bad["api"]["endpoints"].append(copy.deepcopy(bad["api"]["endpoints"][0]))
    bad["entities"][0]["fields"][3]["references"] = "Nope.id"
    with pytest.raises(ContractError) as e:
        eng.register("p1", bad, "bob", "broken")
    assert any("duplicates" in x for x in e.value.errors) and any("Nope.id" in x for x in e.value.errors)
    assert eng.current("p1").version == 2


def test_the_contract_is_derived_from_the_architecture(tmp_path):
    from tests.test_pipeline_integration import ARCHITECTURE, PLAN
    from backend.services.validator import global_stage_validator
    _, _, arch = global_stage_validator.validate_architecture(ARCHITECTURE)
    c = ct.derive("p1", arch, PLAN)
    assert [ct.op_key(e.method, e.path) for e in c.api.endpoints] == ["GET /health", "POST /notes", "GET /notes/{note_id}", "GET /notes"]
    notes = c.entities[0]
    assert notes.name == "notes" and [(f.name, f.type, f.primary_key) for f in notes.fields] == [("id", "integer", True), ("text", "string", False)]
    assert "request_schema" in c.unspecified["POST /notes"] and "auth" in c.unspecified["GET /notes"], "nothing is assumed"
    assert "Create a note" in c.requirements
    assert not ct.validate(c)[0]
    sl = ct.slice_for(c, "frontend")
    assert {o["operation"] for o in sl["operations"]} >= {"POST /notes"} and "entities" not in sl
    assert "Shared integration contract v" in ct.render(ct.slice_for(c, "backend"), "backend")


# 9 / 10 breaking and backward-compatible changes --------------------------------------------------------------------------------------
def test_breaking_changes_name_the_affected_components_and_code(tmp_path):
    eng, _ = engine(tmp_path)
    eng.register("p1", contract(), "alice", "initial")
    eng.analyze("p1", project(tmp_path / "p"), "alice")              # the code locations the change affects
    payload = contract()
    get_one = payload["api"]["endpoints"].pop(2)
    payload["api"]["endpoints"][1]["request_schema"]["properties"]["priority"] = {"type": "integer"}
    payload["api"]["endpoints"][1]["request_schema"]["required"].append("priority")
    del payload["api"]["endpoints"][0]["responses"]["200"]["schema"]["items"]["properties"]["done"]
    _, change, _ = eng.register("p1", payload, "bob", "drop single-task reads; tasks need a priority")
    items = {i.kind: i for i in change.items}
    assert change.breaking and items["endpoint_removed"].breaking and get_one["path"] in items["endpoint_removed"].target
    handler = BACKEND.splitlines().index("def get_task(task_id: int):") + 1
    assert items["endpoint_removed"].affected_code == [f"backend/main.py:{handler}", "frontend/src/api.js:14"]
    assert items["request_field_added"].breaking and "422" in items["request_field_added"].why
    assert items["response_field_removed"].breaking and "frontend" in items["response_field_removed"].affected_components
    assert eng.diff("p1", 1, 2)["breaking"] is True


def test_backward_compatible_changes_are_not_breaking(tmp_path):
    old = shared()
    payload = contract()
    payload["api"]["endpoints"][1]["request_schema"]["properties"]["notes"] = {"type": "string"}
    payload["api"]["endpoints"][0]["responses"]["200"]["schema"]["items"]["properties"]["created_at"] = {"type": "string", "format": "date-time"}
    payload["api"]["endpoints"].append({"method": "DELETE", "path": "/api/tasks/{task_id}", "auth": "bearer",
                                        "responses": {"204": {"content_type": "application/json", "schema": None}}})
    payload["entities"][0]["fields"].append({"name": "notes", "type": "string", "required": False, "nullable": True})
    items = ct.diff(old, shared(payload))
    assert {i.kind for i in items} == {"request_field_added", "response_field_added", "endpoint_added", "entity_field_added"}
    assert not any(i.breaking for i in items), [i for i in items if i.breaking]


# 11 automatic repair coordination ------------------------------------------------------------------------------------------------------
def test_repairs_are_routed_upstream_first_targeted_and_delivered_for_approval(tmp_path):
    proj = project(tmp_path / "p", app=APP_JSX_BROKEN, schema=SCHEMA_SQL_BROKEN)
    before = {p.relative_to(proj).as_posix(): p.read_text(encoding="utf-8") for p in proj.rglob("*") if p.is_file()}
    eng, ap = engine(tmp_path, adjudicate=lambda s, p: '{"field": "title"}')
    eng.register("p1", contract(), "alice", "initial")
    r = eng.start_verify("p1", proj, "alice", {"max_repair_attempts": 5})
    agents = [x.agent for x in r.repairs if x.files_changed]
    assert agents[0] == "database" and "frontend" in agents, "upstream (data model) first"
    strategies = " ".join(x.strategy for x in r.repairs)
    assert "schema_sql_" in strategies and "frontend_call_path" in strategies and "frontend_call_method" in strategies
    assert "frontend_body_key" in strategies and "frontend_read_field" in strategies
    repaired = {f.rule for f in r.findings if f.status == "repaired"}
    assert {"incorrect_url_path", "incorrect_http_method", "db_field_type_mismatch", "db_missing_relationship"} <= repaired
    still = [f for f in r.findings if f.status == "open"]
    assert [f.rule for f in still] == ["auth_mismatch"], "the missing token needs the agent's model repair (none here)"
    assert r.status == "INCOMPATIBLE"
    # the project is untouched; the kept repairs are an Autopilot plan awaiting approval
    assert {p.relative_to(proj).as_posix(): p.read_text(encoding="utf-8") for p in proj.rglob("*") if p.is_file()} == before
    plan = ap.store.get("p1", "plans", r.delivery["autopilot_plan_id"])
    fixed = plan.tasks[0].contents["frontend/src/App.jsx"]
    assert "`${API}/api/tasks`).then" in fixed and "method: 'POST'" in fixed and "title: name" in fixed and "t.title" in fixed
    assert "REFERENCES users(id)" in plan.tasks[0].contents["database/schema.sql"]
    assert r.delivery["base_hashes"]["frontend/src/App.jsx"] and r.report["tests_failed"] == 0


def test_contract_decisions_come_first_and_the_contract_is_never_changed_to_fit(tmp_path):
    backend = BACKEND + '\n\n@app.delete("/api/tasks/{task_id}")\ndef delete_task(task_id: int):\n    _tasks.pop(task_id, None)\n    return {}\n'
    app = APP_JSX + "\nexport const remove = (id) => fetch(`/api/tasks/${id}`, { method: 'DELETE' });\n"
    proj = project(tmp_path / "p", backend=backend, app=app)
    eng, _ = engine(tmp_path)
    c1, _, _ = eng.register("p1", contract(), "alice", "initial")
    r = eng.start_verify("p1", proj, "alice")
    d = next(f for f in r.findings if f.rule == "frontend_call_not_in_contract")
    assert d.status == "needs_contract_decision" and d.responsible_agent == "architect" and not d.repairable
    assert eng.current("p1").revision == c1.revision and len(eng.versions("p1")) == 1, "the contract was not changed"
    assert r.status == "INCOMPATIBLE" and any("frontend_call_not_in_contract" in w for w in r.report["why"])


def test_an_implementation_repair_on_an_undecided_operation_is_deferred():
    from backend.compatibility.models import CompatFinding
    decision = CompatFinding(id="a", key="k1", rule="frontend_call_not_in_contract", severity="high", target="GET /api/x",
                             responsible_agent="architect", status="needs_contract_decision")
    impl = CompatFinding(id="b", key="k2", rule="auth_mismatch", severity="high", target="GET /api/x", responsible_agent="frontend",
                         status="open", repairable=True)
    other = CompatFinding(id="c", key="k3", rule="db_missing_field", severity="high", target="entity Task.title",
                          responsible_agent="database", status="open", repairable=True)
    agent, group, deferred = repair.pick([decision, impl, other], set())
    assert agent == "database" and group == [other] and deferred == [impl]


# 12 repair attempt limits and repeated failures --------------------------------------------------------------------------------------
def test_repair_attempts_are_bounded_and_a_surviving_finding_is_not_retried(tmp_path):
    backend = BACKEND.replace("def create_task(body: TaskIn, user=Depends(get_current_user)):", "def create_task(body: TaskIn):")
    calls = []

    def counting(system, prompt):
        calls.append(prompt)
        return "I cannot change this."
    eng, _ = engine(tmp_path, generate=counting)
    eng.register("p1", contract(), "alice", "initial")
    r = eng.start_verify("p1", project(tmp_path / "p", backend=backend), "alice", {"max_repair_attempts": 3})
    attempts = [x for x in r.repairs if x.outcome != "deferred"]
    assert len(attempts) == 1 and attempts[0].outcome == "no_fix" and len(calls) == 1, "the same finding is not attempted twice"
    assert "Shared integration contract" in calls[0] and "auth_mismatch" in calls[0]
    assert any("no repairable finding left" in a["text"] for a in r.activity)
    r0 = eng.start_verify("p1", project(tmp_path / "q", backend=backend), "alice", {"max_repair_attempts": 0})
    assert not r0.repairs
    with pytest.raises(ContractError):
        eng.start_verify("p1", tmp_path / "q", "alice", {"max_repair_attempts": 9})


def test_a_repair_that_makes_things_worse_is_rolled_back(tmp_path):
    # the frontend agent's "fix" for the missing token adds a call to an operation that does not exist: a regression
    app = APP_JSX + "\nexport const add = (title) => fetch('/api/tasks', { method: 'POST', body: JSON.stringify({ title }) });\n"
    worse = app + "export const stats = () => fetch('/api/statz');\n"

    def destructive(system, prompt):
        return f"### frontend/src/App.jsx\n```jsx\n{worse}```\n"
    eng, _ = engine(tmp_path, generate=destructive)
    eng.register("p1", contract(), "alice", "initial")
    r = eng.start_verify("p1", project(tmp_path / "p", app=app), "alice", {"max_repair_attempts": 2})
    first = next(x for x in r.repairs if x.agent == "frontend")
    assert first.rolled_back and first.outcome == "regressed" and first.files_changed == ["frontend/src/App.jsx"]
    assert first.new_findings and not first.resolved
    assert not r.delivery, "nothing rolled back is delivered"
    assert [f.rule for f in r.findings if f.status == "open"] == ["auth_mismatch"], "the run reports the state before the repair"


def test_workflow_repairs_only_touch_files_this_generation_wrote(tmp_path):
    proj = project(tmp_path / "p", app=APP_JSX_BROKEN)
    eng, _ = engine(tmp_path)
    eng.register("p1", contract(), "alice", "initial")
    r = eng.workflow_check("p1", proj, owned=["backend/main.py"], allow_model=False)
    rejected = [x for rec in r.repairs for x in rec.rejected_paths]
    assert rejected and all(x["reason"].startswith("not written by this generation") for x in rejected)
    assert (proj / "frontend/src/App.jsx").read_text(encoding="utf-8") == APP_JSX_BROKEN
    r2 = eng.workflow_check("p1", proj, owned=["frontend/src/App.jsx"], allow_model=False)
    assert "frontend/src/App.jsx" in r2.delivery["written"]
    assert "`${API}/api/tasks`).then" in (proj / "frontend/src/App.jsx").read_text(encoding="utf-8"), "written back in the workflow"


# 13 / 14 integration test generation and execution ---------------------------------------------------------------------------------
def test_generated_tests_take_their_expectations_from_the_contract(tmp_path):
    backend = BACKEND.replace('@app.post("/api/tasks", response_model=Task, status_code=201)', '@app.post("/api/tasks", response_model=Task)')
    proj = project(tmp_path / "p", backend=backend)
    from backend.execution_guardian import checks as chk
    tests, files = testgen.generate(shared(), extract.snapshot(proj), chk.detect(proj))
    source = files[testgen.TEST_FILE]
    compile(source, testgen.TEST_FILE, "exec")
    assert '\\"201\\"' in source or '"201"' in source, "the contract's status, not the implementation's"
    assert len([t for t in tests if t.kind == "endpoint_exists"]) == 3
    eng, _ = engine(tmp_path)
    eng.register("p1", contract(), "alice", "initial")
    r = eng.start_verify("p1", proj, "alice", {"max_repair_attempts": 0})
    post = next(t for t in r.tests if t.kind == "valid_request" and t.target == "POST /api/tasks")
    assert post.status == "failed" and "expected status ['201']" in post.detail
    assert ("incorrect_status_code", "POST /api/tasks") in {(f.rule, f.target) for f in r.findings}


def test_tests_that_could_not_run_are_never_reported_as_passed(tmp_path, monkeypatch):
    import backend.execution.docker_test_sandbox as sandbox
    monkeypatch.setattr(sandbox, "sandbox_mode", lambda: "docker")
    monkeypatch.setattr(sandbox, "docker_available", lambda: False)
    eng, _ = engine(tmp_path)
    eng.register("p1", contract(), "alice", "initial")
    r = eng.start_verify("p1", project(tmp_path / "p"), "alice")
    assert r.status == "BLOCKED" and r.test_execution["status"] == "BLOCKED"
    assert all(t.status == "not_run" for t in r.tests) and r.report["tests_passed"] == 0
    assert "Docker is not available" in r.report["why"][0]


def test_without_an_app_the_api_tests_fail_instead_of_passing(tmp_path):
    proj = project(tmp_path / "p", backend="print('no app here')\n")
    eng, _ = engine(tmp_path)
    eng.register("p1", contract(), "alice", "initial")
    r = eng.start_verify("p1", proj, "alice", {"max_repair_attempts": 0})
    api_tests = [t for t in r.tests if t.kind in ("endpoint_exists", "valid_request")]
    assert api_tests and all(t.status in ("failed", "error") for t in api_tests) and r.status == "INCOMPATIBLE"


# 15 contract drift ------------------------------------------------------------------------------------------------------------------
def test_contract_drift_is_detected_and_classified(tmp_path):
    eng, _ = engine(tmp_path)
    eng.register("p1", contract(), "alice", "initial")
    proj = project(tmp_path / "p")
    assert eng.analyze("p1", proj, "alice").status == "COMPATIBLE_WITH_WARNINGS"
    renamed = BACKEND.replace("    done: bool\n\n\n@app.get", "    completed: bool\n\n\n@app.get") \
        + '\n\n@app.get("/api/stats")\ndef stats():\n    return {"count": len(_tasks)}\n'
    (proj / "backend/main.py").write_text(renamed, encoding="utf-8")
    r = eng.analyze("p1", proj, "alice")
    drift = {f.target: f for f in r.findings if f.rule == "contract_drift"}
    rename = drift["GET /api/tasks response.done"]
    assert rename.breaking is True and rename.status == "open" and "renamed to 'completed'" in rename.actual
    assert "frontend/src/api.js:10" in rename.evidence["consumers"]
    added = drift["GET /api/stats"]
    assert added.breaking is False and added.status == "info"
    assert r.status == "INCOMPATIBLE"


def test_a_change_the_contract_made_is_not_drift(tmp_path):
    eng, _ = engine(tmp_path)
    eng.register("p1", contract(), "alice", "initial")
    proj = project(tmp_path / "p")
    eng.analyze("p1", proj, "alice")
    (proj / "backend/main.py").write_text(BACKEND + '\n\n@app.get("/api/stats")\ndef stats():\n    return {"count": 0}\n', encoding="utf-8")
    payload = contract()
    payload["api"]["endpoints"].append({"method": "GET", "path": "/api/stats", "auth": "none",
                                        "responses": {"200": {"content_type": "application/json", "schema": None}}})
    eng.register("p1", payload, "alice", "statistics endpoint")
    r = eng.analyze("p1", proj, "alice")
    assert not [f for f in r.findings if f.rule == "contract_drift"]


# 16 API authorization -------------------------------------------------------------------------------------------------------------
@pytest.fixture
def api(tmp_path, monkeypatch):
    import backend.compatibility.routes as routes
    import backend.routes.export as export
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from backend.auth.dependencies import get_current_user
    from backend.generation.store import global_generation_store
    proj = project(tmp_path / "proj", app=APP_JSX_BROKEN)
    eng, ap = engine(tmp_path)
    monkeypatch.setattr(routes, "global_integration_engine", eng)
    records = {"mine": {"generation_id": "mine", "user_id": "alice", "status": "completed", "project_path": str(proj)},
               "theirs": {"generation_id": "theirs", "user_id": "bob", "status": "completed", "project_path": str(proj)}}
    monkeypatch.setattr(global_generation_store, "get", lambda gid, default=None: records.get(gid, default))
    monkeypatch.setattr(export, "_safe_project_dir", lambda p: proj if p == str(proj) else None)
    from tests.test_pipeline_integration import ARCHITECTURE, PLAN
    from backend.services.validator import global_stage_validator
    _, _, arch = global_stage_validator.validate_architecture(ARCHITECTURE)
    monkeypatch.setattr(routes, "_architecture", lambda pid: {"architecture": arch, "plan": PLAN} if pid == "mine" else {})
    app = FastAPI()
    app.include_router(routes.integration_router)
    app.dependency_overrides[get_current_user] = lambda: {"id": "alice"}
    return TestClient(app), app, proj


def test_the_api_enforces_authentication_and_project_ownership(api, monkeypatch):
    client, app, _ = api
    for method, url in (("post", "/api/projects/theirs/contract"), ("get", "/api/projects/theirs/contract"),
                        ("post", "/api/projects/theirs/integration/analyze"), ("post", "/api/projects/theirs/integration/verify"),
                        ("get", "/api/projects/theirs/integration/runs"), ("get", "/api/projects/theirs/contract/diff")):
        body = {"contract": contract(), "reason": "mine now"} if url.endswith("/contract") and method == "post" else {}
        assert getattr(client, method)(url, **({"json": body} if method == "post" else {})).status_code == 403, url
    assert client.get("/api/projects/unknown/contract").status_code == 404
    assert client.get("/api/projects/..%2F..%2Fetc/contract").status_code in (403, 404)
    from backend.auth.dependencies import get_current_user
    app.dependency_overrides.pop(get_current_user)
    # without credentials: the local default user may not open alice's project; with auth required, 401
    assert client.get("/api/projects/mine/contract").status_code == 403
    monkeypatch.setenv("AIFORGE_REQUIRE_AUTH", "1")
    for method, url in (("get", "/api/projects/mine/contract"), ("post", "/api/projects/mine/integration/analyze"),
                        ("post", "/api/projects/mine/integration/verify"), ("get", "/api/projects/mine/integration/runs")):
        assert getattr(client, method)(url, **({"json": {}} if method == "post" else {})).status_code == 401, url


def test_the_api_flow(api):
    client, _, _ = api
    base = "/api/projects/mine"
    assert client.get(f"{base}/contract").status_code == 404
    assert client.post(f"{base}/integration/verify", json={}).status_code == 422, "no contract yet"
    assert client.post(f"{base}/contract", json={"contract": contract(), "reason": "x"}).status_code == 422, "reason too short"
    bad = client.post(f"{base}/contract", json={"contract": {"api": {"endpoints": []}}, "reason": "empty contract"})
    assert bad.status_code == 422 and "no API operation" in json.dumps(bad.json())
    derived = client.post(f"{base}/contract/derive", json={})
    assert derived.status_code == 201 and derived.json()["contract"]["source"] == "architect"
    r = client.post(f"{base}/contract", json={"contract": contract(), "reason": "the task API, precisely"})
    assert r.status_code == 201 and r.json()["contract"]["version"] == 2 and r.json()["change"]["breaking"] is True
    assert client.get(f"{base}/contract?version=1").json()["contract"]["source"] == "architect"
    assert client.get(f"{base}/contract?agent=database").json()["slice"]["entities"][0]["name"] == "Task"
    assert client.get(f"{base}/contract?agent=hacker").status_code == 422
    assert [v["version"] for v in client.get(f"{base}/contract/versions").json()["versions"]] == [2, 1]
    assert client.get(f"{base}/contract/diff?from=1&to=2").json()["items"]
    assert client.get(f"{base}/contract/diff?from=7").status_code == 404
    a = client.post(f"{base}/integration/analyze").json()
    assert a["run"]["status"] == "INCOMPATIBLE" and a["run"]["kind"] == "analyze"
    assert client.post(f"{base}/integration/verify", json={"settings": {"max_repair_attempts": 99}}).status_code == 422
    v = client.post(f"{base}/integration/verify", json={"settings": {"max_repair_attempts": 2}})
    assert v.status_code == 202
    rid = v.json()["run_id"]
    run = client.get(f"{base}/integration/runs/{rid}").json()["run"]
    assert run["status"] in ("INCOMPATIBLE", "COMPATIBLE_WITH_WARNINGS", "COMPATIBLE") and run["tests"] and "implementation" not in run
    assert client.get(f"{base}/integration/runs").json()["runs"][0]["id"] == rid
    assert client.get(f"{base}/integration/runs/{rid}/report").json()["run_id"] == rid
    md = client.get(f"{base}/integration/runs/{rid}/report?format=markdown").text
    assert "# Compatibility report" in md and "## Contract tests" in md and "## Not checked" in md
    assert client.get(f"{base}/integration/runs/{rid}/report?format=xml").status_code == 422
    assert client.get(f"{base}/integration/runs/int_missing").status_code == 404
    assert client.post(f"{base}/integration/runs/{rid}/cancel").status_code == 200


# 17 report generation ---------------------------------------------------------------------------------------------------------------
def test_the_report_reflects_what_ran_and_hides_secrets(tmp_path):
    app = APP_JSX_BROKEN.replace("`${API}/tasks`", "'/tasks?api_key=sk-test-1234567890abcdef'")
    eng, _ = engine(tmp_path)
    eng.register("p1", contract(), "alice", "initial")
    r = eng.start_verify("p1", project(tmp_path / "p", app=app), "alice", {"max_repair_attempts": 0})
    rep = r.report
    for k in ("project_id", "contract_version", "components_analyzed", "findings", "findings_by_severity", "repairs",
              "tests_executed", "tests_passed", "tests_failed", "unresolved", "status", "coverage", "limitations"):
        assert k in rep, k
    assert rep["status"] == "INCOMPATIBLE" and rep["tests_executed"] == len(r.tests) and rep["tests_failed"] >= 1
    assert all(f["evidence"] is not None and f["expected"] and f["recommended_fix"] for f in rep["findings"])
    text = json.dumps(rep) + markdown(rep)
    assert "1234567890abcdef" not in text and "[REDACTED]" in text


def test_final_status_rules():
    from backend.compatibility.models import CompatFinding, IntegrationRun
    c = shared()
    run = IntegrationRun(id="r", project_id="p1", user_id="u", kind="verify", test_execution={"status": "PASSED", "counts": {"passed": 3}})
    assert final_status(run, c)[0] == "COMPATIBLE"
    assert final_status(run, None)[0] == "BLOCKED"
    low = CompatFinding(id="x", key="k", rule="error_response_mismatch", severity="low", target="t")
    assert final_status(run.model_copy(update={"findings": [low]}), c)[0] == "COMPATIBLE_WITH_WARNINGS"
    high = low.model_copy(update={"severity": "high"})
    assert final_status(run.model_copy(update={"findings": [high]}), c)[0] == "INCOMPATIBLE"
    assert final_status(run.model_copy(update={"test_execution": {"status": "BLOCKED"}}), c)[0] == "BLOCKED"
    assert final_status(run.model_copy(update={"kind": "analyze", "test_execution": {}}), c)[0] == "COMPATIBLE_WITH_WARNINGS"


# 18 existing workflow -------------------------------------------------------------------------------------------------------------
def test_the_generation_workflow_builds_against_and_checks_the_shared_contract(pipeline):
    import asyncio
    from backend.compatibility.service import global_integration_engine
    fx = pipeline
    graph = fx.graph
    config = {"configurable": {"thread_id": "gen_aice_1"}}
    asyncio.run(graph.ainvoke({"prompt": "Build a notes board", "user_prompt": "Build a notes board", "project_id": "notes_board",
                               "generation_id": "gen_aice_1", "session_id": "gen_aice_1", "files": {}, "fixes": [],
                               "retry_count": 0, "max_iterations": 3}, config=config))
    values = graph.get_state(config).values
    assert values["contract"]["status"] == "established" and values["contract"]["version"] == 1
    assert values["approval_request"]["contract"]["operations"] == ["GET /health", "POST /notes", "GET /notes/{note_id}", "GET /notes"]
    _resume(graph, config, {"approval_status": "approved", "approval_required": False, "status": "RUNNING",
                            "current_step": "dispatch_parallel"})
    for agent in ("backend", "frontend", "database"):
        assert "Shared integration contract v1" in fx.prompts[agent], agent
    values = graph.get_state(config).values
    comp = values["compatibility"]
    assert comp["id"] and comp["status"] in ("COMPATIBLE_WITH_WARNINGS", "INCOMPATIBLE", "BLOCKED")
    assert comp["status"] != "COMPATIBLE", "the architecture leaves request bodies and auth unspecified: not fully verified"
    run = global_integration_engine.get("gen_aice_1", comp["id"])
    assert run.source == "workflow" and run.tests and run.test_execution["status"] in ("PASSED", "SKIPPED", "FAILED")
    assert values["approval_request"]["compatibility"]["id"] == comp["id"]
    assert any("Integration & Compatibility" in e for e in values["stream_events"])
