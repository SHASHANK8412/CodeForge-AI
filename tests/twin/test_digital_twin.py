"""
AIForge Digital Twin: graph extraction, impact analysis, risk, test selection, read-only simulation,
approval through Autopilot, prediction versus actual, API, persistence.

Deterministic fixtures; model calls are stubs. Static tools run for real.
"""

import hashlib
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.evolution.autopilot.plans import PlanError
from backend.evolution.autopilot.service import AutopilotService
from backend.evolution.autopilot.store import AutopilotStore
from backend.twin.graph import build_graph, find_cycles, routes_match
from backend.twin.index import GraphIndex
from backend.twin.service import TwinService, TwinStore

FILES = {
    "backend/__init__.py": "",
    "backend/main.py": ("from fastapi import FastAPI\nfrom backend.routes import router\n\n"
                        "app = FastAPI()\napp.include_router(router)\n"),
    "backend/routes.py": ("from fastapi import APIRouter, Depends\nfrom backend.models import Item\n"
                          "from backend.auth import current_user\nfrom .db import get_db\n\n"
                          "router = APIRouter(prefix='/api')\n\n\n"
                          "@router.get('/items/{item_id}')\ndef read_item(item_id: int, user=Depends(current_user)):\n"
                          "    return {'id': item_id, 'model': Item.__name__}\n"),
    "backend/models.py": ("from sqlalchemy.orm import declarative_base\n\nBase = declarative_base()\n\n\n"
                          "class Item(Base):\n    __tablename__ = 'items'\n"),
    "backend/auth.py": "from backend import models\n\n\ndef current_user():\n    return models.Item\n",
    "backend/db.py": "def get_db():\n    return None\n",
    "backend/broken_import.py": "from backend.missing_module import thing\n",
    "backend/cycle_a.py": "from backend import cycle_b\n",
    "backend/cycle_b.py": "from backend import cycle_a\n",
    "requirements.txt": "fastapi\nsqlalchemy\n",
    ".env.example": "DATABASE_URL=sqlite:///./app.db\n",
    "tests/test_routes.py": ("from fastapi.testclient import TestClient\nfrom backend.main import app\n"
                             "from backend.routes import read_item\n\n\ndef test_item():\n"
                             "    assert TestClient(app).get('/api/items/1').status_code == 200\n"),
    "tests/test_models.py": "def test_models_load():\n    assert True\n",
    "frontend/package.json": json.dumps({"dependencies": {"react": "19", "axios": "1"}}),
    "frontend/src/main.jsx": ("import { createRoot } from 'react-dom/client'\nimport App from './App'\n"
                              "createRoot(document.getElementById('root')).render(<App />)\n"),
    "frontend/src/App.jsx": ("import ItemCard from './components/ItemCard'\nimport { api } from '@/api'\n\n"
                             "export default function App() {\n  return <ItemCard />\n}\n"),
    "frontend/src/components/ItemCard.jsx": ("import { useEffect } from 'react'\n\n"
                                             "export default function ItemCard({ id }) {\n"
                                             "  useEffect(() => { fetch(`${API}/api/items/${id}`) }, [id])\n"
                                             "  return <div />\n}\n"),
    "frontend/src/api.ts": "import axios from 'axios'\nimport { gone } from './nope'\nexport const api = axios.create()\n",
}


def write(root, files):
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "shop"
    write(root, FILES)
    return root


@pytest.fixture
def services(tmp_path):
    ap = AutopilotService(AutopilotStore(tmp_path / "ap"), background=False)
    tw = TwinService(TwinStore(tmp_path / "tw"), autopilot=ap, background=False)
    return ap, tw


NO_DOCKER = {"docker": False, "oxlint": False, "bandit": True}


def edges(b, type_=None):
    return {(e.source, e.target, e.type, e.certainty) for e in b.edges.values() if type_ is None or e.type == type_}


def analyzed(tw, project, pid="p1"):
    g = tw.start_analysis(pid, project, "u1")
    g = tw.store.get(pid, "graphs", g.id)
    assert g.status == "completed", g.error
    return g


def simulate(tw, project, request, pid="p1", **kw):
    from backend.twin import simulate as sim
    original = sim.tooling
    sim.tooling = lambda: NO_DOCKER
    try:
        report = tw.simulate(pid, project, "u1", request, **kw)
    finally:
        sim.tooling = original
    report = tw.store.get(pid, "reports", report.id)
    assert report.status == "completed", report.error
    return report


def file_hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


# 1 ------------------------------------------------------------------------------------------------
def test_python_imports_symbols_routes_and_models(project):
    b = build_graph(project)
    imp = edges(b, "imports")
    assert ("file:backend/routes.py", "file:backend/models.py", "imports", "established") in imp
    assert ("file:backend/routes.py", "file:backend/db.py", "imports", "established") in imp       # relative import
    assert ("file:backend/main.py", "file:backend/routes.py", "imports", "established") in imp
    uses = edges(b, "uses")
    assert ("file:backend/routes.py", "model:backend/models.py#Item", "uses", "established") in uses
    assert ("file:backend/auth.py", "model:backend/models.py#Item", "uses", "established") in uses   # models.Item
    route = b.nodes["route:backend/routes.py#GET /api/items/{item_id}"]
    assert route.meta["handler"] == "read_item" and route.meta["route"] == "/api/items/{item_id}"
    assert b.nodes["model:backend/models.py#Item"].meta["kind"] == "orm"
    assert ("file:backend/routes.py", "package:fastapi", "depends_on", "established") in edges(b, "depends_on")
    for e in b.edges.values():
        assert e.evidence                                       # every edge carries its evidence


# 2 ------------------------------------------------------------------------------------------------
def test_javascript_typescript_imports_components_and_api_calls(project):
    b = build_graph(project)
    assert ("file:frontend/src/App.jsx", "file:frontend/src/components/ItemCard.jsx", "imports", "established") in edges(b)
    assert ("file:frontend/src/App.jsx", "file:frontend/src/api.ts", "imports", "inferred") in edges(b)   # '@/' alias
    assert ("file:frontend/src/App.jsx", "component:frontend/src/components/ItemCard.jsx#ItemCard", "renders",
            "established") in edges(b)
    assert ("file:frontend/src/components/ItemCard.jsx", "route:backend/routes.py#GET /api/items/{item_id}",
            "calls_api", "inferred") in edges(b)
    assert ("file:frontend/src/api.ts", "package:axios", "depends_on", "established") in edges(b)
    assert b.nodes["file:frontend/src/api.ts"].language == "javascript"
    assert routes_match("/items/{item_id}", "`${API}/api/items/${id}`") and not routes_match("/users", "/api/items/1")


# 3 ------------------------------------------------------------------------------------------------
def test_direct_dependents(project, services):
    _, tw = services
    index = GraphIndex(analyzed(tw, project))
    dependents = dict(index.dependents("backend/models.py"))
    assert {"backend/routes.py", "backend/auth.py"} <= set(dependents)
    assert dependents["backend/routes.py"].certainty == "established"
    assert "tests/test_models.py" in dependents and dependents["tests/test_models.py"].certainty == "inferred"


# 4 ------------------------------------------------------------------------------------------------
def test_transitive_dependents_with_chains(project, services):
    _, tw = services
    index = GraphIndex(analyzed(tw, project))
    closure = index.reverse_closure(["backend/models.py"])
    assert closure["backend/main.py"]["depth"] == 2
    assert closure["backend/main.py"]["chain"] == ["backend/models.py", "backend/routes.py", "backend/main.py"]
    # backend -> frontend through an inferred URL match: the chain is marked inferred
    assert closure["frontend/src/components/ItemCard.jsx"]["established"] is False


# 5 ------------------------------------------------------------------------------------------------
def test_unresolved_imports_are_reported_not_invented(project):
    b = build_graph(project)
    reasons = {(u["file"], u["module"]): u["reason"] for u in b.unresolved}
    assert ("backend/broken_import.py", "backend.missing_module") in reasons
    assert ("frontend/src/api.ts", "./nope") in reasons
    assert not any(e.target.endswith("missing_module.py") for e in b.edges.values())
    assert not [u for u in b.unresolved if u["module"] == "backend.routes.router"]      # assigned names count


# 6 ------------------------------------------------------------------------------------------------
def test_circular_imports_are_detected(project, services):
    _, tw = services
    g = analyzed(tw, project)
    assert ["file:backend/cycle_a.py", "file:backend/cycle_b.py"] in g.cycles
    assert find_cycles(["a", "b", "c"], [("a", "b"), ("b", "c")]) == []


# 7 ------------------------------------------------------------------------------------------------
def test_paths_outside_the_project_are_rejected(project, tmp_path):
    (tmp_path / "secret.py").write_text("TOKEN = 1\n", encoding="utf-8")
    write(project, {"frontend/src/escape.js": "import x from '../../../../secret'\n",
                    "backend/escape.py": "from .... import secret\n"})
    b = build_graph(project)
    assert not any("secret" in (n.path or "") for n in b.nodes.values())
    assert any(u["file"] == "frontend/src/escape.js" for u in b.unresolved)
    assert any(u["file"] == "backend/escape.py" and "above the project" in u["reason"] for u in b.unresolved)


# 8 ------------------------------------------------------------------------------------------------
def test_large_projects_hit_resource_limits(project, monkeypatch):
    import backend.evolution.autopilot.codebase as codebase
    write(project, {"backend/huge.py": "x = 1\n" * 50_000})
    monkeypatch.setattr(codebase, "MAX_FILE_BYTES", 10_000)
    b = build_graph(project)
    assert "backend/huge.py" in b.too_large and any("too large" in l for l in b.limits)
    monkeypatch.setattr(codebase, "MAX_FILES", 5)
    b = build_graph(project)
    assert len(b.files) == 5 and any("more than 5 files" in l for l in b.limits)
    assert not any(n.path and n.path.startswith(".venv") for n in b.nodes.values())


# 9 ------------------------------------------------------------------------------------------------
def test_impact_of_a_backend_api_change(project, services):
    _, tw = services
    analyzed(tw, project)
    report = simulate(tw, project, "Return the item owner from the item endpoint", target_files=["backend/routes.py"])
    o = report.options[0]
    assert o.modify_scope == ["backend/routes.py"] and o.seeds[0]["source"] == "chosen by you"
    assert {d["path"] for d in o.direct} >= {"backend/main.py", "frontend/src/components/ItemCard.jsx"}
    api = o.apis[0]
    assert api["route"] == "GET /api/items/{item_id}" and api["frontend_callers"] == ["frontend/src/components/ItemCard.jsx"]
    assert "public_api" in o.change_kinds
    assert any(i["symbol"] == "read_item" for i in o.interfaces_at_risk)
    assert any(m["model"] == "Item" and m["relation"] == "used by backend/routes.py" for m in o.models)


# 10 -----------------------------------------------------------------------------------------------
def test_impact_of_a_frontend_component_change(project, services):
    _, tw = services
    analyzed(tw, project)
    o = simulate(tw, project, "Show a spinner in the item card",
                 target_files=["frontend/src/components/ItemCard.jsx"]).options[0]
    assert [d["path"] for d in o.direct] == ["frontend/src/App.jsx"] and o.direct[0]["via"] == "renders"
    assert "frontend/src/main.jsx" in [t["path"] for t in o.transitive]
    assert o.components[0]["component"] == "ItemCard" and o.components[0]["rendered_by"] == ["frontend/src/App.jsx"]
    assert "frontend_ui" in o.change_kinds and not o.apis


# 11 -----------------------------------------------------------------------------------------------
def test_risk_is_explained_and_auth_needs_security_review(project, services):
    _, tw = services
    analyzed(tw, project)
    small = simulate(tw, project, "Rename a local variable", target_files=["backend/db.py"]).options[0]
    auth = simulate(tw, project, "Add Google login to the auth module", target_files=["backend/auth.py"]).options[0]
    for o in (small, auth):
        assert o.risk_points == sum(f.points for f in o.risk_factors)
        assert all(f.reason for f in o.risk_factors)
    assert small.risk in ("low", "medium") and not small.security_review
    assert auth.security_review and auth.risk in ("high", "critical")
    assert any(f.factor == "authentication/authorization" for f in auth.risk_factors)
    assert any("Security review" in s for s in auth.validation_steps)


# 12 -----------------------------------------------------------------------------------------------
def test_tests_are_selected_with_reasons(project, services):
    _, tw = services
    analyzed(tw, project)
    o = simulate(tw, project, "Change the item route", target_files=["backend/routes.py"]).options[0]
    by_path = {t.path: t for t in o.tests}
    assert by_path["tests/test_routes.py"].certainty == "established"
    assert any("imports backend/routes.py" in r for r in by_path["tests/test_routes.py"].reasons)
    assert any("integration test" in r for r in by_path["tests/test_routes.py"].reasons)
    o2 = simulate(tw, project, "Change the item model", target_files=["backend/models.py"]).options[0]
    models_test = {t.path: t for t in o2.tests}["tests/test_models.py"]
    assert models_test.certainty == "inferred" and "named after" in models_test.reasons[0]
    o3 = simulate(tw, project, "Restyle the app shell", target_files=["frontend/src/App.jsx"]).options[0]
    assert o3.untested == ["frontend/src/App.jsx"]
    assert any("No tests cover" in s for s in o3.validation_steps) or o3.tests


# 13 -----------------------------------------------------------------------------------------------
def test_simulation_is_read_only(project, services):
    _, tw = services
    analyzed(tw, project)
    before = file_hashes(project)
    report = simulate(tw, project, "Add Google login", target_files=["backend/auth.py"],
                      alternatives=["Put Google login in a new oauth service"])
    assert file_hashes(project) == before
    assert report.files_written == 0 and len(report.options) == 2
    assert any("not mean the change is safe" in a for a in report.assumptions)


# 14 -----------------------------------------------------------------------------------------------
def test_reports_become_autopilot_plans_that_need_approval(project, services):
    ap, tw = services
    analyzed(tw, project)
    report = simulate(tw, project, "Add Google login", target_files=["backend/auth.py"])
    plan = tw.create_plan("p1", report.id, "u1")
    assert plan.status.value == "awaiting_approval" and plan.origin == "digital_twin" and plan.origin_ref == report.id
    assert plan.expected_files == ["backend/auth.py"] and plan.tasks[0].request.startswith("Add Google login")
    assert plan.security_review_required
    with pytest.raises(PlanError):
        ap.decide("p1", plan.id, "u1", "approved")                     # security review not confirmed
    with pytest.raises(PlanError):
        tw.create_plan("p1", report.id, "u1")                           # one open plan per report
    approved = ap.decide("p1", plan.id, "u1", "approved", security_reviewed=True)
    assert approved.status.value == "approved" and "security review confirmed" in approved.decisions[-1].note
    assert tw.store.get("p1", "reports", report.id).plan_id == plan.id


# 15 -----------------------------------------------------------------------------------------------
def test_prediction_is_compared_with_the_actual_change(project, services):
    ap, tw = services
    analyzed(tw, project)
    report = simulate(tw, project, "Add an owner field", target_files=["backend/routes.py", "backend/models.py"])
    plan = tw.create_plan("p1", report.id, "u1")
    ap.decide("p1", plan.id, "u1", "approved")
    routes = (project / "backend/routes.py").read_text(encoding="utf-8")
    reply = "### backend/routes.py\n```python\n" + routes + "OWNER_FIELD = 'owner'\n```\n"
    execution = ap.execute("p1", plan.id, "u1", project, generate=lambda s, p: reply, include_tests=False)
    assert execution.status == "completed", execution.error
    outcome = tw.outcome("p1", report.id)
    assert outcome.actual_files == ["backend/routes.py"] and outcome.unexpected_files == []
    assert outcome.predicted_not_changed == ["backend/models.py"]
    assert outcome.precision == 1.0 and outcome.recall == 0.5
    acc = tw.accuracy("p1")
    assert acc["compared"] == 1 and acc["mean_recall"] == 0.5


def test_unexpected_files_stop_the_run_and_are_recorded(project, services):
    ap, tw = services
    analyzed(tw, project)
    report = simulate(tw, project, "Add an owner field", target_files=["backend/routes.py"])
    plan = tw.create_plan("p1", report.id, "u1")
    ap.decide("p1", plan.id, "u1", "approved")
    reply = ("### backend/routes.py\n```python\nX = 1\n```\n### backend/owner.py\n```python\nOWNER = 1\n```\n")
    execution = ap.execute("p1", plan.id, "u1", project, generate=lambda s, p: reply, include_tests=False)
    assert execution.status == "needs_approval" and not (project / "backend/owner.py").exists()
    outcome = tw.outcome("p1", report.id)
    assert outcome.unexpected_files == ["backend/owner.py"] and outcome.out_of_scope_files == ["backend/owner.py"]
    assert outcome.actual_files == ["backend/owner.py", "backend/routes.py"] and outcome.precision == 0.5
    assert any("not applied" in limit for limit in outcome.limitations)


# 16 -----------------------------------------------------------------------------------------------
def test_missing_docker_and_planner_model_are_reported(project, services):
    _, tw = services
    analyzed(tw, project)

    def broken_model(system, prompt):
        raise ConnectionError("ollama is not running")
    report = simulate(tw, project, "Change the item route", use_model=True, generate=broken_model)
    o = report.options[0]
    assert report.planner["status"].startswith("unavailable")
    assert any("planner model was unavailable" in u for u in o.uncertainties)
    assert "backend/routes.py" in o.modify_scope and o.seeds[0]["source"] == "keyword match"
    assert any("Docker is not available" in u for u in o.uncertainties)
    assert any("Docker is not available" in s for s in o.validation_steps)

    def model(system, prompt):
        return json.dumps({"modify": ["backend/routes.py", "backend/invented.py"], "create": ["backend/owner.py", "../x.py"],
                           "change_kinds": ["public_api"], "notes": "ok"})
    report = simulate(tw, project, "Add owner", use_model=True, generate=model)
    o = report.options[0]
    assert o.modify_scope == ["backend/routes.py"] and o.seeds[0]["source"] == "planner model"
    assert o.create_scope == ["backend/"] and "invented.py" in report.planner["notes"]


# 17 -----------------------------------------------------------------------------------------------
def test_analysis_time_limit_is_reported(project, tmp_path):
    tw = TwinService(TwinStore(tmp_path / "tw2"), background=False, deadline_seconds=0)
    g = tw.store.get("p1", "graphs", tw.start_analysis("p1", project, "u1").id)
    assert g.status == "completed"
    assert any("time limit" in l for l in g.limits)


# 18 -----------------------------------------------------------------------------------------------
@pytest.fixture
def api(tmp_path, project, monkeypatch):
    import backend.evolution.routes as ev_routes
    import backend.routes.export as export
    import backend.twin.routes as routes
    from backend.auth.dependencies import get_current_user
    from backend.generation.store import global_generation_store
    ap = AutopilotService(AutopilotStore(tmp_path / "api-ap"), background=False)
    tw = TwinService(TwinStore(tmp_path / "api-tw"), autopilot=ap, background=False)
    monkeypatch.setattr(routes, "global_twin_service", tw)
    records = {
        "gen_mine": {"generation_id": "gen_mine", "user_id": "alice", "status": "completed", "project_path": str(project)},
        "gen_theirs": {"generation_id": "gen_theirs", "user_id": "bob", "status": "completed", "project_path": str(project)},
    }
    monkeypatch.setattr(global_generation_store, "get", lambda gid, default=None: records.get(gid, default))
    monkeypatch.setattr(export, "_safe_project_dir", lambda p: project if p == str(project) else None)
    monkeypatch.setattr("backend.twin.simulate.tooling", lambda: NO_DOCKER)
    app = FastAPI()
    app.include_router(routes.twin_router)
    app.dependency_overrides[get_current_user] = lambda: {"id": "alice"}
    assert ev_routes._project_dir                                       # same ownership rules as Autopilot
    return TestClient(app)


def test_api_flow_ownership_and_validation(api, project):
    base = "/api/projects/gen_mine/twin"
    assert api.post("/api/projects/gen_theirs/twin/analyses").status_code == 403
    assert api.get("/api/projects/nope/twin/graph").status_code == 404
    assert api.get(f"{base}/graph").status_code == 404                  # no graph yet
    assert api.post(f"{base}/analyses").status_code == 202
    latest = api.get(f"{base}/analyses/latest").json()
    assert latest["analysis"]["status"] == "completed" and latest["stale"] is False
    graph = api.get(f"{base}/graph", params={"type": "route"}).json()
    assert graph["total"] == 1 and graph["stats"]["cycles"] == 1
    deps = api.get(f"{base}/dependencies", params={"node": "file:backend/models.py", "depth": 2}).json()
    assert {d["path"] for d in deps["files"]["dependents"]} >= {"backend/routes.py", "backend/auth.py"}
    assert any(i["path"] == "backend/main.py" for i in deps["files"]["indirect_dependents"])
    assert api.get(f"{base}/dependencies", params={"node": "file:../etc/passwd"}).status_code == 404
    bad = api.post(f"{base}/simulations", json={"request": "x change", "target_files": ["../../etc/passwd"]})
    assert bad.status_code == 400
    report = api.post(f"{base}/simulations", json={"request": "Change the item route",
                                                     "target_files": ["backend/routes.py"]}).json()["report"]
    full = api.get(f"{base}/reports/{report['id']}").json()["report"]
    assert full["status"] == "completed" and full["options"][0]["modify_scope"] == ["backend/routes.py"]
    tests = api.get(f"{base}/reports/{report['id']}/tests").json()
    assert tests["tests"][0]["path"] == "tests/test_routes.py"
    plan = api.post(f"{base}/reports/{report['id']}/plan", json={}).json()["plan"]
    assert plan["origin"] == "digital_twin"
    assert api.get(f"{base}/reports/{report['id']}/outcome").json()["outcome"] is None
    assert api.get("/api/projects/gen_theirs/twin/reports").status_code == 403
    assert api.get(f"{base}/reports/imp_missing").status_code == 404


# 19 -----------------------------------------------------------------------------------------------
def test_results_persist_and_interrupted_jobs_are_closed(project, tmp_path):
    from backend.twin.models import ImpactReport
    store = TwinStore(tmp_path / "persist")
    tw = TwinService(store, background=False)
    g = tw.store.get("p1", "graphs", tw.start_analysis("p1", project, "u1").id)
    store.put("p1", "reports", ImpactReport(id="imp_running", project_id="p1", user_id="u1", request="x", status="running"))
    reopened = TwinService(TwinStore(tmp_path / "persist"), background=True)      # what a server restart does
    assert reopened.store.latest_graph("p1").id == g.id
    assert len(reopened.store.latest_graph("p1").edges) == len(g.edges)
    r = reopened.store.get("p1", "reports", "imp_running")
    assert r.status == "failed" and "interrupted" in r.error
    raw = (tmp_path / "persist" / "p1.json").read_text(encoding="utf-8")
    assert "__tablename__ = 'items'\\n" not in raw                     # graph stores structure, not source files
    assert not tw.is_stale("p1", project)
    write(project, {"backend/db.py": "def get_db():\n    return 1\n"})
    assert tw.is_stale("p1", project)


# 20 -----------------------------------------------------------------------------------------------
def test_existing_autopilot_finding_plans_still_work_alongside(project, services):
    ap, tw = services
    analysis = ap.start_analysis("p1", project, "u1")
    assert ap.store.get("p1", "analyses", analysis.id).status == "completed"
    finding = next(f for f in ap.store.list("p1", "findings") if f.fix_strategy != "manual")
    findings_plan = ap.create_plan("p1", "u1", [finding.id])
    assert findings_plan.origin == "findings" and not findings_plan.security_review_required
    analyzed(tw, project)
    report = simulate(tw, project, "Change the item route", target_files=["backend/routes.py"])
    twin_plan = tw.create_plan("p1", report.id, "u1")
    plans = {p.id: p.origin for p in ap.store.list("p1", "plans")}
    assert plans == {findings_plan.id: "findings", twin_plan.id: "digital_twin"}
