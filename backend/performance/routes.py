"""
AIForge Performance Engineer REST API.

  POST /api/projects/{project_id}/performance/analyses               static findings + measured baseline
  GET  /api/projects/{project_id}/performance/analyses/latest
  GET  /api/projects/{project_id}/performance/findings               ?evidence_kind=&category=&status=
  POST /api/projects/{project_id}/performance/baselines              measure a workload now
  GET  /api/projects/{project_id}/performance/runs                   list
  GET  /api/projects/{project_id}/performance/runs/{run_id}
  POST /api/projects/{project_id}/performance/runs/{run_id}/cancel
  POST /api/projects/{project_id}/performance/plans                  optimization plan for a finding
  GET  /api/projects/{project_id}/performance/plans                  list (ranked)
  GET  /api/projects/{project_id}/performance/plans/{plan_id}/report before/after report
Approval, execution, execution status and cancellation use the Autopilot endpoints
(/api/projects/{id}/evolution/plans/{autopilot_plan_id}/approve|reject|execute, executions/{id}).

Projects and ownership are resolved as for Autopilot. Nothing here runs project code on the host:
apps run only in the Docker sandbox.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.auth.dependencies import get_current_user
from backend.evolution.routes import _project_dir, _user_id
from backend.performance.engineer.models import Endpoint, Thresholds, Workload
from backend.performance.engineer.service import Busy, PlanError, global_performance_engineer

performance_router = APIRouter(prefix="/api/projects", tags=["AIForge Performance Engineer"])


def _engine():
    return global_performance_engineer


def _check_endpoints(endpoints: List[Endpoint]) -> None:
    for e in endpoints:
        if not e.path.startswith("/") or ".." in e.path.split("/") or "://" in e.path or "\\" in e.path:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"invalid endpoint path: {e.path}")
        if e.method.upper() not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"invalid method: {e.method}")


class AnalysisRequest(BaseModel):
    measure: bool = True
    workload: Optional[Workload] = None


@performance_router.post("/{project_id}/performance/analyses", status_code=202)
def start_analysis(project_id: str, body: AnalysisRequest = AnalysisRequest(),
                   user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    path = _project_dir(project_id, user)
    if body.workload:
        _check_endpoints(body.workload.endpoints)
    try:
        a = _engine().start_analysis(project_id, path, _user_id(user), body.measure, body.workload)
    except Busy as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
    return {"analysis": a.model_dump(mode="json")}


@performance_router.get("/{project_id}/performance/analyses/latest")
def latest_analysis(project_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    a = _engine().store.latest(project_id, "analyses")
    baseline = _engine().store.get(project_id, "runs", a.baseline_run_id) if a and a.baseline_run_id else None
    return {"analysis": a.model_dump(mode="json") if a else None,
            "baseline": baseline.model_dump(mode="json") if baseline else None,
            "active_job": _engine().active_job(project_id)}


@performance_router.get("/{project_id}/performance/findings")
def findings(project_id: str, evidence_kind: Optional[str] = None, category: Optional[str] = None,
             status_: Optional[str] = Query(None, alias="status"), user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    items = _engine().store.list(project_id, "findings")
    if evidence_kind:
        items = [f for f in items if f.evidence_kind in evidence_kind.split(",")]
    if category:
        items = [f for f in items if f.category in category.split(",")]
    if status_:
        items = [f for f in items if f.status in status_.split(",")]
    order = {"measured": 0, "static_warning": 1, "hypothesis": 2}
    sev = {"high": 0, "medium": 1, "low": 2}
    items.sort(key=lambda f: (order.get(f.evidence_kind, 9), sev.get(f.severity, 9), f.file or ""))
    return {"total": len(items), "items": [f.model_dump(mode="json") for f in items]}


class BaselineRequest(BaseModel):
    workload: Workload = Field(default_factory=Workload)


@performance_router.post("/{project_id}/performance/baselines", status_code=202)
def start_baseline(project_id: str, body: BaselineRequest = BaselineRequest(),
                   user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    path = _project_dir(project_id, user)
    _check_endpoints(body.workload.endpoints)
    try:
        run = _engine().start_baseline(project_id, path, _user_id(user), body.workload)
    except Busy as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
    return {"run": run.model_dump(mode="json")}


@performance_router.get("/{project_id}/performance/runs")
def list_runs(project_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    runs = sorted(_engine().store.list(project_id, "runs"), key=lambda r: r.started_at or "", reverse=True)
    return {"runs": [r.model_dump(mode="json", exclude={"measurement": {"logs_tail"}}) for r in runs[:30]],
            "active_job": _engine().active_job(project_id)}


@performance_router.get("/{project_id}/performance/runs/{run_id}")
def get_run(project_id: str, run_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    run = _engine().store.get(project_id, "runs", run_id)
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Run not found.")
    return {"run": run.model_dump(mode="json")}


@performance_router.post("/{project_id}/performance/runs/{run_id}/cancel")
def cancel_run(project_id: str, run_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    run = _engine().cancel_run(project_id, run_id)
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Run not found.")
    return {"run": run.model_dump(mode="json", exclude={"measurement"}), "cancel_requested": run.cancel_requested}


class PlanRequest(BaseModel):
    finding_id: str = Field(..., max_length=80)
    thresholds: Optional[Thresholds] = None
    workload: Optional[Workload] = None


@performance_router.post("/{project_id}/performance/plans", status_code=201)
def create_plan(project_id: str, body: PlanRequest, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    path = _project_dir(project_id, user)
    if body.workload:
        _check_endpoints(body.workload.endpoints)
    try:
        plan = _engine().create_plan(project_id, path, _user_id(user), body.finding_id, body.thresholds, body.workload)
    except KeyError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Finding not found.")
    except PlanError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    return {"plan": plan.model_dump(mode="json")}


@performance_router.get("/{project_id}/performance/plans")
def list_plans(project_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    plans = sorted(_engine().store.list(project_id, "plans"), key=lambda p: (-p.rank_score, p.created_at))
    return {"plans": [p.model_dump(mode="json") for p in plans[:50]]}


@performance_router.get("/{project_id}/performance/plans/{plan_id}/report")
def plan_report(project_id: str, plan_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    report = _engine().report(project_id, plan_id)
    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan not found.")
    return {"report": report}
