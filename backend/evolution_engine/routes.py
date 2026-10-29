"""
AIForge Evolution Engine REST API (project access is checked as for Autopilot).

  POST /api/projects/{id}/evolution-engine/opportunities/discover   {"criteria": {...}} (optional weights)
  GET  /api/projects/{id}/evolution-engine/opportunities
  POST /api/projects/{id}/evolution-engine/experiments              plan: {"opportunity_id", "max_candidates", "weights",
                                                                    "thresholds", "overrides": {strategy: justification}}
  GET  /api/projects/{id}/evolution-engine/experiments
  GET  /api/projects/{id}/evolution-engine/experiments/{eid}
  POST /api/projects/{id}/evolution-engine/experiments/{eid}/run      {"approved": true}
  POST /api/projects/{id}/evolution-engine/experiments/{eid}/abort
  POST /api/projects/{id}/evolution-engine/experiments/{eid}/approve  {"candidate_id": optional}
  POST /api/projects/{id}/evolution-engine/experiments/{eid}/promote
  GET  /api/projects/{id}/evolution-engine/memory                     Engineering Memory (all projects' records)
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.auth.dependencies import get_current_user
from backend.evolution.routes import _project_dir, _user_id
from backend.evolution_engine.memory import MEMORY_KEY, related
from backend.evolution_engine.models import Weights
from backend.evolution_engine.service import Busy, EvolutionError, global_evolution_engine
from backend.performance.engineer.models import Thresholds

evolution_engine_router = APIRouter(prefix="/api/projects", tags=["AIForge Evolution Engine"])
BASE = "/{project_id}/evolution-engine"


def _engine():
    return global_evolution_engine


def _exp(project_id: str, eid: str):
    e = _engine().store.get(project_id, "experiments", eid)
    if e is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Experiment not found.")
    return e


class DiscoverRequest(BaseModel):
    criteria: Dict[str, float] = Field(default_factory=dict)


@evolution_engine_router.post(BASE + "/opportunities/discover")
def discover(project_id: str, body: Optional[DiscoverRequest] = None, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    path = _project_dir(project_id, user)
    ops = _engine().discover(project_id, path, (body.criteria if body else None) or None)
    return {"opportunities": [o.model_dump(mode="json") for o in ops]}


@evolution_engine_router.get(BASE + "/opportunities")
def opportunities(project_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    ops = sorted(_engine().store.list(project_id, "opportunities"), key=lambda o: (not o.experimentable, -o.priority))
    return {"opportunities": [o.model_dump(mode="json") for o in ops]}


class PlanRequest(BaseModel):
    opportunity_id: str = Field(..., max_length=40)
    max_candidates: int = Field(2, ge=1, le=3)
    weights: Optional[Weights] = None
    thresholds: Optional[Thresholds] = None
    overrides: Dict[str, str] = Field(default_factory=dict)


@evolution_engine_router.post(BASE + "/experiments", status_code=201)
def create(project_id: str, body: PlanRequest, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    path = _project_dir(project_id, user)
    if any(len(v.strip()) < 10 for v in body.overrides.values()):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "a new justification (10+ characters) is required to retry a failed strategy")
    try:
        exp = _engine().create_experiment(project_id, path, _user_id(user), body.opportunity_id, body.max_candidates,
                                          body.weights, body.thresholds, body.overrides)
    except KeyError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Opportunity not found: discover opportunities first.")
    return {"experiment": exp.model_dump(mode="json")}


@evolution_engine_router.get(BASE + "/experiments")
def experiments(project_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    items = sorted(_engine().store.list(project_id, "experiments"), key=lambda e: e.created_at, reverse=True)
    brief = [{"id": e.id, "status": e.status, "outcome": e.outcome, "title": e.opportunity.title, "endpoint": e.opportunity.endpoint,
              "created_at": e.created_at, "finished_at": e.finished_at, "selected": e.selected,
              "candidates": [{"id": c.id, "strategy": c.strategy, "status": c.status, "eligible": c.eligible} for c in e.candidates]}
             for e in items[:50]]
    return {"experiments": brief, "active_job": _engine().active_job(project_id)}


@evolution_engine_router.get(BASE + "/experiments/{eid}")
def experiment(project_id: str, eid: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    e = _exp(project_id, eid)
    history = related(project_id, e.opportunity.category, e.plan.context)
    return {"experiment": e.model_dump(mode="json"), "memory": [h for h in history if h["experiment_id"] != eid],
            "active_job": _engine().active_job(project_id)}


class RunRequest(BaseModel):
    approved: bool = False


@evolution_engine_router.post(BASE + "/experiments/{eid}/run", status_code=202)
def run(project_id: str, eid: str, body: RunRequest, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    path = _project_dir(project_id, user, writable=False)
    _exp(project_id, eid)
    try:
        e = _engine().run(project_id, path, _user_id(user), eid, body.approved)
    except EvolutionError as err:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(err))
    except Busy as err:
        raise HTTPException(status.HTTP_409_CONFLICT, str(err))
    return {"experiment": e.model_dump(mode="json")}


@evolution_engine_router.post(BASE + "/experiments/{eid}/abort")
def abort(project_id: str, eid: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    _exp(project_id, eid)
    e = _engine().abort(project_id, eid)
    return {"experiment": {"id": e.id, "status": e.status, "cancel_requested": e.cancel_requested}}


class ApproveRequest(BaseModel):
    candidate_id: Optional[str] = Field(None, max_length=8)


@evolution_engine_router.post(BASE + "/experiments/{eid}/approve")
def approve(project_id: str, eid: str, body: Optional[ApproveRequest] = None, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    path = _project_dir(project_id, user)
    _exp(project_id, eid)
    try:
        e = _engine().approve(project_id, path, _user_id(user), eid, body.candidate_id if body else None)
    except EvolutionError as err:
        raise HTTPException(status.HTTP_409_CONFLICT, str(err))
    return {"experiment": e.model_dump(mode="json")}


@evolution_engine_router.post(BASE + "/experiments/{eid}/promote", status_code=202)
def promote(project_id: str, eid: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    path = _project_dir(project_id, user, writable=True)
    _exp(project_id, eid)
    try:
        e = _engine().promote(project_id, path, _user_id(user), eid)
    except EvolutionError as err:
        raise HTTPException(status.HTTP_409_CONFLICT, str(err))
    except Busy as err:
        raise HTTPException(status.HTTP_409_CONFLICT, str(err))
    return {"experiment": e.model_dump(mode="json")}


@evolution_engine_router.get(BASE + "/memory")
def engineering_memory(project_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    records = sorted(_engine().store.list(MEMORY_KEY, "memory"), key=lambda r: r.recorded_at, reverse=True)
    # other projects' records are shown without their file paths (only the kind of context)
    out = []
    for r in records[:200]:
        d = r.model_dump(mode="json")
        if r.project_id != project_id:
            d["context"] = {k: v for k, v in d["context"].items() if k not in ("file", "endpoint")}
            d["project_id"] = "another project"
            d["scope"] = "measured in another project; not a general rule"
        out.append(d)
    return {"memory": out}
