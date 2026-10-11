"""
AIForge Digital Twin REST API.

  POST /api/projects/{project_id}/twin/analyses                 build the dependency graph
  GET  /api/projects/{project_id}/twin/analyses/latest          status, stats, staleness
  GET  /api/projects/{project_id}/twin/graph                    nodes (filters, pagination) + summary
  GET  /api/projects/{project_id}/twin/dependencies?node=...    neighborhood of one node (direct / indirect)
  POST /api/projects/{project_id}/twin/simulations              read-only impact simulation
  GET  /api/projects/{project_id}/twin/reports                  list
  GET  /api/projects/{project_id}/twin/reports/{report_id}
  GET  /api/projects/{project_id}/twin/reports/{report_id}/tests
  POST /api/projects/{project_id}/twin/reports/{report_id}/plan        -> Autopilot plan (approval workflow)
  GET  /api/projects/{project_id}/twin/reports/{report_id}/outcome     prediction versus actual
  GET  /api/projects/{project_id}/twin/accuracy

Projects and ownership are resolved exactly as for Autopilot (backend/evolution/routes.py).
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.auth.dependencies import get_current_user
from backend.evolution.autopilot.plans import PlanError
from backend.evolution.routes import _project_dir, _user_id
from backend.twin.index import GraphIndex
from backend.twin.service import Busy, global_twin_service

twin_router = APIRouter(prefix="/api/projects", tags=["AIForge Digital Twin"])


def _report_or_404(project_id: str, report_id: str):
    report = global_twin_service.store.get(project_id, "reports", report_id)
    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Report not found.")
    return report


def _graph_or_404(project_id: str):
    graph = global_twin_service.store.latest_graph(project_id)
    if graph is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No dependency graph yet: start an analysis first.")
    return graph


@twin_router.post("/{project_id}/twin/analyses", status_code=202)
def start_analysis(project_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    path = _project_dir(project_id, user)
    try:
        g = global_twin_service.start_analysis(project_id, path, _user_id(user))
    except Busy as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
    return {"analysis": g.model_dump(mode="json", exclude={"nodes", "edges"})}


@twin_router.get("/{project_id}/twin/analyses/latest")
def latest_analysis(project_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    path = _project_dir(project_id, user)
    graphs = global_twin_service.store.list(project_id, "graphs")
    latest = max(graphs, key=lambda g: g.started_at or "", default=None)
    completed = global_twin_service.store.latest_graph(project_id)
    return {
        "analysis": latest.model_dump(mode="json", exclude={"nodes", "edges"}) if latest else None,
        "graph_id": completed.id if completed else None,
        "stale": global_twin_service.is_stale(project_id, path, completed) if completed else None,
        "active_job": global_twin_service.active_job(project_id),
    }


@twin_router.get("/{project_id}/twin/graph")
def get_graph(project_id: str, type: Optional[str] = None, language: Optional[str] = None, q: Optional[str] = None,
              offset: int = Query(0, ge=0), limit: int = Query(200, ge=1, le=1000),
              user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    graph = _graph_or_404(project_id)
    index = GraphIndex(graph)
    nodes = graph.nodes
    if type:
        nodes = [n for n in nodes if n.type in type.split(",")]
    if language:
        nodes = [n for n in nodes if (n.language or "") in language.split(",")]
    if q:
        nodes = [n for n in nodes if q.lower() in f"{n.path or ''} {n.symbol or ''}".lower()]
    nodes = sorted(nodes, key=lambda n: (n.type, n.path or "", n.symbol or ""))
    page = nodes[offset:offset + limit]
    degree = {n.id: (len(index.inc.get(n.id, [])), len(index.out.get(n.id, []))) for n in page}
    return {
        "graph_id": graph.id, "stats": graph.stats, "cycles": graph.cycles, "limits": graph.limits,
        "unresolved": graph.unresolved[:200], "total": len(nodes), "offset": offset, "limit": limit,
        "nodes": [{**n.model_dump(mode="json"), "in_degree": degree[n.id][0], "out_degree": degree[n.id][1]} for n in page],
    }


@twin_router.get("/{project_id}/twin/dependencies")
def dependencies(project_id: str, node: str = Query(..., max_length=600), depth: int = Query(2, ge=1, le=4),
                 direction: str = Query("both", pattern="^(both|in|out)$"), limit: int = Query(150, ge=10, le=500),
                 user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    index = GraphIndex(_graph_or_404(project_id))
    if node not in index.nodes:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Node not found in the graph.")
    nodes, edges, dist = index.neighborhood(node, depth, direction, limit)
    file_view = None
    focus = index.nodes[node]
    if focus.path and focus.type in ("file", "test", "config"):
        file_view = {
            "dependencies": [{"path": p, "type": e.type, "certainty": e.certainty, "evidence": e.evidence}
                             for p, e in index.dependencies(focus.path)],
            "dependents": [{"path": p, "type": e.type, "certainty": e.certainty, "evidence": e.evidence}
                           for p, e in index.dependents(focus.path)],
            "indirect_dependents": [{"path": p, "depth": v["depth"], "chain": v["chain"],
                                     "certainty": "established" if v["established"] else "inferred"}
                                    for p, v in sorted(index.reverse_closure([focus.path]).items(),
                                                       key=lambda kv: (kv[1]["depth"], kv[0])) if v["depth"] > 1],
        }
    return {"focus": focus.model_dump(mode="json"),
            "nodes": [{**n.model_dump(mode="json"), "distance": dist[n.id]} for n in nodes],
            "edges": [e.model_dump(mode="json") for e in edges], "files": file_view,
            "truncated": len(nodes) >= limit}


class SimulationRequest(BaseModel):
    request: str = Field(..., min_length=3, max_length=2000)
    target_files: List[str] = Field(default_factory=list, max_length=30)
    alternatives: List[str] = Field(default_factory=list, max_length=3)
    use_model: bool = False


@twin_router.post("/{project_id}/twin/simulations", status_code=202)
def simulate(project_id: str, body: SimulationRequest, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    path = _project_dir(project_id, user)
    for p in body.target_files:
        if p.startswith(("/", "\\")) or ".." in p.replace("\\", "/").split("/") or ":" in p:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"invalid file path: {p}")
    try:
        report = global_twin_service.simulate(project_id, path, _user_id(user), body.request,
                                              target_files=body.target_files, alternatives=body.alternatives,
                                              use_model=body.use_model)
    except Busy as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
    return {"report": report.model_dump(mode="json")}


@twin_router.get("/{project_id}/twin/reports")
def list_reports(project_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    reports = sorted(global_twin_service.store.list(project_id, "reports"), key=lambda r: r.created_at, reverse=True)
    return {"reports": [{"id": r.id, "request": r.request[:200], "status": r.status, "created_at": r.created_at,
                         "risk": r.options[0].risk if r.options else None, "plan_id": r.plan_id,
                         "has_outcome": r.outcome is not None} for r in reports[:50]]}


@twin_router.get("/{project_id}/twin/reports/{report_id}")
def get_report(project_id: str, report_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    return {"report": _report_or_404(project_id, report_id).model_dump(mode="json"),
            "active_job": global_twin_service.active_job(project_id)}


@twin_router.get("/{project_id}/twin/reports/{report_id}/tests")
def report_tests(project_id: str, report_id: str, option: int = Query(0, ge=0, le=3),
                 user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    report = _report_or_404(project_id, report_id)
    if option >= len(report.options):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such option in this report.")
    pred = report.options[option]
    return {"tests": [t.model_dump(mode="json") for t in pred.tests], "untested_changed_files": pred.untested,
            "note": "Selection is based on static links; it does not cover every possible regression."}


class PlanFromReport(BaseModel):
    option: int = Field(0, ge=0, le=3)


@twin_router.post("/{project_id}/twin/reports/{report_id}/plan", status_code=201)
def plan_from_report(project_id: str, report_id: str, body: PlanFromReport = PlanFromReport(),
                     user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    _report_or_404(project_id, report_id)
    try:
        plan = global_twin_service.create_plan(project_id, report_id, _user_id(user), body.option)
    except PlanError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
    return {"plan": plan.model_dump(mode="json")}


@twin_router.get("/{project_id}/twin/reports/{report_id}/outcome")
def report_outcome(project_id: str, report_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    _report_or_404(project_id, report_id)
    outcome = global_twin_service.outcome(project_id, report_id)
    return {"outcome": outcome.model_dump(mode="json") if outcome else None}


@twin_router.get("/{project_id}/twin/accuracy")
def accuracy(project_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    return global_twin_service.accuracy(project_id)
