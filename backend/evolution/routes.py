"""
AIForge Autopilot REST API (the project's software-evolution endpoints).

  GET    /api/evolution/projects                                   projects the user can analyze
  POST   /api/projects/{project_id}/evolution/analyses             start an analysis
  GET    /api/projects/{project_id}/evolution/analyses/latest
  GET    /api/projects/{project_id}/evolution/analyses/{analysis_id}
  GET    /api/projects/{project_id}/evolution/findings             filters + pagination
  GET    /api/projects/{project_id}/evolution/findings/{finding_id}
  PATCH  /api/projects/{project_id}/evolution/findings/{finding_id}   dismiss / reopen
  POST   /api/projects/{project_id}/evolution/plans                create a plan from findings
  GET    /api/projects/{project_id}/evolution/plans                list
  GET    /api/projects/{project_id}/evolution/plans/{plan_id}
  POST   /api/projects/{project_id}/evolution/plans/{plan_id}/approve | reject | cancel
  POST   /api/projects/{project_id}/evolution/plans/{plan_id}/execute
  GET    /api/projects/{project_id}/evolution/executions           list
  GET    /api/projects/{project_id}/evolution/executions/{execution_id}
  POST   /api/projects/{project_id}/evolution/executions/{execution_id}/cancel
  GET    /api/projects/{project_id}/evolution/executions/{execution_id}/report

A project is a completed generation the user owns (its folder must be inside generated_projects/).
Nothing runs without an approved plan, and changes reach the project only after validation.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.auth.dependencies import get_current_user
from backend.evolution.autopilot.findings import filter_findings
from backend.evolution.autopilot.plans import PlanError
from backend.evolution.autopilot.service import Busy, global_autopilot_service

autopilot_evolution_router = APIRouter(tags=["AIForge Autopilot"])
_PROJECT_ID = re.compile(r"^[A-Za-z0-9_.\-]{1,120}$")
_SHARED_OWNERS = ("default", "demo_user")
_READABLE = ("completed", "waiting_for_approval", "failed", "cancelled")
# A generation paused for approval resumes and writes its files again, so only finished ones are changed.
_WRITABLE = ("completed", "failed", "cancelled")


def _user_id(user: dict) -> str:
    return str(user.get("id") or user.get("user_id") or "")


def _project_dir(project_id: str, user: dict, writable: bool = False) -> Path:
    """The project's folder, if `user` may work on it; 404/403 otherwise."""
    from backend.generation.store import global_generation_store
    from backend.routes.export import _safe_project_dir
    if not _PROJECT_ID.match(project_id or "") or project_id in (".", ".."):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found.")
    rec = global_generation_store.get(project_id)
    if not rec:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found.")
    owner = rec.get("user_id")
    if owner != _user_id(user) and owner not in _SHARED_OWNERS:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have access to this project.")
    if writable and rec.get("status") not in _WRITABLE:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            f"The generation is '{rec.get('status')}': it can still write its files. Finish or cancel it "
                            "before Autopilot changes the project.")
    if rec.get("status") not in _READABLE:
        raise HTTPException(status.HTTP_409_CONFLICT, f"The generation is '{rec.get('status')}'; wait for it to finish.")
    path = _safe_project_dir(rec.get("project_path") or "")
    if path is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "The project's folder is missing.")
    return path


def _get_or_404(project_id: str, kind: str, item_id: str):
    item = global_autopilot_service.store.get(project_id, kind, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{kind[:-1].capitalize()} not found.")
    return item


def _busy(e: Busy):
    return HTTPException(status.HTTP_409_CONFLICT, str(e))


# --- projects ------------------------------------------------------------------------------------

@autopilot_evolution_router.get("/api/evolution/projects")
def list_projects(user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    from backend.generation.store import global_generation_store
    from backend.routes.export import _safe_project_dir
    uid = _user_id(user)
    projects = []
    for rec in global_generation_store.list_all():
        gid = rec.get("id") or rec.get("generation_id")
        if not gid or (rec.get("user_id") != uid and rec.get("user_id") not in _SHARED_OWNERS):
            continue
        path = _safe_project_dir(rec.get("project_path") or "")
        if path is None or rec.get("status") not in _READABLE:
            continue
        latest = global_autopilot_service.store.latest_analysis(gid)
        projects.append({
            "project_id": gid, "name": path.name, "status": rec.get("status"),
            "created_at": rec.get("created_at"), "prompt": (rec.get("prompt") or "")[:160],
            "last_analysis": latest.model_dump(include={"id", "status", "started_at", "finished_at", "summary"})
            if latest else None,
        })
    projects.sort(key=lambda p: p.get("created_at") or "", reverse=True)
    return {"projects": projects}


# --- analyses ------------------------------------------------------------------------------------

class AnalysisRequest(BaseModel):
    run_tests: bool = False


@autopilot_evolution_router.post("/api/projects/{project_id}/evolution/analyses", status_code=202)
def start_analysis(project_id: str, body: AnalysisRequest = AnalysisRequest(),
                   user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    path = _project_dir(project_id, user)
    try:
        analysis = global_autopilot_service.start_analysis(project_id, path, _user_id(user), run_tests=body.run_tests)
    except Busy as e:
        raise _busy(e)
    return {"analysis": analysis.model_dump(mode="json")}


@autopilot_evolution_router.get("/api/projects/{project_id}/evolution/analyses/latest")
def latest_analysis(project_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    analysis = global_autopilot_service.store.latest_analysis(project_id)
    return {"analysis": analysis.model_dump(mode="json") if analysis else None,
            "active_job": global_autopilot_service.active_job(project_id)}


@autopilot_evolution_router.get("/api/projects/{project_id}/evolution/analyses/{analysis_id}")
def get_analysis(project_id: str, analysis_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    return {"analysis": _get_or_404(project_id, "analyses", analysis_id).model_dump(mode="json")}


# --- findings -------------------------------------------------------------------------------------

@autopilot_evolution_router.get("/api/projects/{project_id}/evolution/findings")
def list_findings(project_id: str, severity: Optional[str] = None, category: Optional[str] = None,
                  status_: Optional[str] = Query(None, alias="status"), confidence: Optional[str] = None,
                  priority: Optional[str] = None, file: Optional[str] = None, q: Optional[str] = None,
                  offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                  user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    page = filter_findings(global_autopilot_service.store.list(project_id, "findings"), severity=severity,
                           category=category, status=status_, confidence=confidence, priority=priority, file=file,
                           q=q, offset=offset, limit=limit)
    page["items"] = [f.model_dump(mode="json") for f in page["items"]]
    return page


@autopilot_evolution_router.get("/api/projects/{project_id}/evolution/findings/{finding_id}")
def get_finding(project_id: str, finding_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    return {"finding": _get_or_404(project_id, "findings", finding_id).model_dump(mode="json")}


class FindingUpdate(BaseModel):
    dismissed: bool


@autopilot_evolution_router.patch("/api/projects/{project_id}/evolution/findings/{finding_id}")
def update_finding(project_id: str, finding_id: str, body: FindingUpdate,
                   user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    finding = global_autopilot_service.dismiss(project_id, finding_id, body.dismissed)
    if finding is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Finding not found.")
    return {"finding": finding.model_dump(mode="json")}


# --- plans --------------------------------------------------------------------------------------------

class PlanRequest(BaseModel):
    finding_ids: List[str] = Field(..., min_length=1, max_length=40)
    objective: str = ""


class DecisionRequest(BaseModel):
    note: str = ""
    extra_files: List[str] = Field(default_factory=list, max_length=20)
    security_reviewed: bool = False      # required to approve plans that change authentication


class ExecuteRequest(BaseModel):
    run_tests: bool = True


@autopilot_evolution_router.post("/api/projects/{project_id}/evolution/plans", status_code=201)
def create_plan(project_id: str, body: PlanRequest, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    try:
        plan = global_autopilot_service.create_plan(project_id, _user_id(user), body.finding_ids, body.objective)
    except PlanError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    return {"plan": plan.model_dump(mode="json")}


@autopilot_evolution_router.get("/api/projects/{project_id}/evolution/plans")
def list_plans(project_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    plans = sorted(global_autopilot_service.store.list(project_id, "plans"), key=lambda p: p.created_at, reverse=True)
    return {"plans": [p.model_dump(mode="json") for p in plans[:50]]}


@autopilot_evolution_router.get("/api/projects/{project_id}/evolution/plans/{plan_id}")
def get_plan(project_id: str, plan_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    return {"plan": _get_or_404(project_id, "plans", plan_id).model_dump(mode="json")}


def _decide(project_id: str, plan_id: str, user: dict, decision: str, body: DecisionRequest) -> Dict[str, Any]:
    _project_dir(project_id, user)
    _get_or_404(project_id, "plans", plan_id)
    try:
        plan = global_autopilot_service.decide(project_id, plan_id, _user_id(user), decision, body.note,
                                               body.extra_files if decision == "approved" else None,
                                               security_reviewed=body.security_reviewed)
    except PlanError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
    return {"plan": plan.model_dump(mode="json")}


@autopilot_evolution_router.post("/api/projects/{project_id}/evolution/plans/{plan_id}/approve")
def approve_plan(project_id: str, plan_id: str, body: DecisionRequest = DecisionRequest(),
                 user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    return _decide(project_id, plan_id, user, "approved", body)


@autopilot_evolution_router.post("/api/projects/{project_id}/evolution/plans/{plan_id}/reject")
def reject_plan(project_id: str, plan_id: str, body: DecisionRequest = DecisionRequest(),
                user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    return _decide(project_id, plan_id, user, "rejected", body)


@autopilot_evolution_router.post("/api/projects/{project_id}/evolution/plans/{plan_id}/cancel")
def cancel_plan(project_id: str, plan_id: str, body: DecisionRequest = DecisionRequest(),
                user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    return _decide(project_id, plan_id, user, "cancelled", body)


@autopilot_evolution_router.post("/api/projects/{project_id}/evolution/plans/{plan_id}/execute", status_code=202)
def execute_plan(project_id: str, plan_id: str, body: ExecuteRequest = ExecuteRequest(),
                 user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    path = _project_dir(project_id, user, writable=True)
    _get_or_404(project_id, "plans", plan_id)
    try:
        execution = global_autopilot_service.execute(project_id, plan_id, _user_id(user), path,
                                                     include_tests=body.run_tests)
    except PlanError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
    except Busy as e:
        raise _busy(e)
    return {"execution": execution.model_dump(mode="json")}


# --- executions -----------------------------------------------------------------------------------------

@autopilot_evolution_router.get("/api/projects/{project_id}/evolution/executions")
def list_executions(project_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    items = sorted(global_autopilot_service.store.list(project_id, "executions"),
                   key=lambda e: e.started_at or "", reverse=True)
    return {"executions": [e.model_dump(mode="json", exclude={"diff", "baseline", "after"}) for e in items[:50]]}


@autopilot_evolution_router.get("/api/projects/{project_id}/evolution/executions/{execution_id}")
def get_execution(project_id: str, execution_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    return {"execution": _get_or_404(project_id, "executions", execution_id).model_dump(mode="json")}


@autopilot_evolution_router.post("/api/projects/{project_id}/evolution/executions/{execution_id}/cancel")
def cancel_execution(project_id: str, execution_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    _get_or_404(project_id, "executions", execution_id)
    execution = global_autopilot_service.cancel_execution(project_id, execution_id)
    return {"execution": execution.model_dump(mode="json", exclude={"diff"}),
            "cancel_requested": execution.cancel_requested}


@autopilot_evolution_router.get("/api/projects/{project_id}/evolution/executions/{execution_id}/report")
def execution_report(project_id: str, execution_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    report = global_autopilot_service.report(project_id, execution_id)
    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Execution not found.")
    return {"report": report}
