"""
AIForge Swarm Intelligence REST API (project access is checked as for Autopilot).

  GET  /api/swarm/agents                                       the capability registry
  POST /api/projects/{id}/swarm/missions                       {"objective", "contract", "constraints", "acceptance", "settings"}
  GET  /api/projects/{id}/swarm/missions
  GET  /api/projects/{id}/swarm/missions/{mid}
  POST /api/projects/{id}/swarm/missions/{mid}/run             {"approved": true} (also resumes an interrupted mission)
  POST /api/projects/{id}/swarm/missions/{mid}/cancel
  POST /api/projects/{id}/swarm/missions/{mid}/decide          {"conflict_id", "proposal_id"} (escalated conflicts)
  POST /api/projects/{id}/swarm/missions/{mid}/deliver         the integrated files as an Autopilot plan awaiting approval
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.auth.dependencies import get_current_user
from backend.evolution.routes import _project_dir, _user_id
from backend.swarm.models import Contract
from backend.swarm.registry import REGISTRY
from backend.swarm.service import Busy, SwarmError, global_swarm_engine

swarm_router = APIRouter(tags=["AIForge Swarm Intelligence"])
BASE = "/api/projects/{project_id}/swarm/missions"
SETTINGS = {"concurrency": (1, 4), "max_messages": (20, 500), "max_repair_rounds": (0, 3), "mission_seconds": (60, 7200)}


def _engine():
    return global_swarm_engine


def _mission(project_id: str, mid: str):
    m = _engine().store.get(project_id, "missions", mid)
    if m is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mission not found.")
    return m


def _guard(fn):
    try:
        return fn()
    except KeyError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mission not found.")
    except SwarmError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
    except Busy as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))


@swarm_router.get("/api/swarm/agents")
def agents(user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    return {"agents": [a.model_dump() for a in REGISTRY]}


class MissionRequest(BaseModel):
    objective: str = Field(..., min_length=5, max_length=2000)
    contract: Contract
    constraints: List[str] = Field(default_factory=list, max_length=20)
    acceptance: List[str] = Field(default_factory=list, max_length=20)
    settings: Dict[str, Any] = Field(default_factory=dict)
    priorities: Dict[str, float] = Field(default_factory=dict)


@swarm_router.post(BASE, status_code=201)
def create(project_id: str, body: MissionRequest, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    settings = {}
    for k, v in body.settings.items():
        if k not in SETTINGS or not isinstance(v, (int, float)) or not SETTINGS[k][0] <= v <= SETTINGS[k][1]:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"setting {k} must be within {SETTINGS.get(k)}")
        settings[k] = v
    if body.priorities:
        settings["priorities"] = {k: float(v) for k, v in body.priorities.items() if 0 <= float(v) <= 1}
    m = _engine().create(project_id, _user_id(user), body.objective, body.contract, body.constraints, body.acceptance, settings)
    return {"mission": m.model_dump(mode="json")}


@swarm_router.get(BASE)
def missions(project_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    items = sorted(_engine().store.list(project_id, "missions"), key=lambda m: m.created_at, reverse=True)
    return {"missions": [{"id": m.id, "objective": m.objective, "status": m.status, "created_at": m.created_at,
                          "finished_at": m.finished_at, "tasks": {t.id: t.status for t in m.tasks},
                          "conflicts": len(m.conflicts)} for m in items[:50]]}


@swarm_router.get(BASE + "/{mid}")
def mission(project_id: str, mid: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    return {"mission": _mission(project_id, mid).model_dump(mode="json"), "active": _engine().active(project_id)}


class RunRequest(BaseModel):
    approved: bool = False


@swarm_router.post(BASE + "/{mid}/run", status_code=202)
def run(project_id: str, mid: str, body: RunRequest, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    path = _project_dir(project_id, user)
    _mission(project_id, mid)
    return {"mission": _guard(lambda: _engine().run(project_id, path, _user_id(user), mid, body.approved)).model_dump(mode="json")}


@swarm_router.post(BASE + "/{mid}/cancel")
def cancel(project_id: str, mid: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    _mission(project_id, mid)
    m = _engine().cancel(project_id, mid)
    return {"mission": {"id": m.id, "status": m.status, "cancel_requested": m.cancel_requested}}


class DecideRequest(BaseModel):
    conflict_id: str = Field(..., max_length=20)
    proposal_id: str = Field(..., max_length=20)


@swarm_router.post(BASE + "/{mid}/decide", status_code=202)
def decide(project_id: str, mid: str, body: DecideRequest, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    path = _project_dir(project_id, user)
    _mission(project_id, mid)
    m = _guard(lambda: _engine().decide(project_id, path, _user_id(user), mid, body.conflict_id, body.proposal_id))
    return {"mission": m.model_dump(mode="json")}


@swarm_router.post(BASE + "/{mid}/deliver", status_code=201)
def deliver(project_id: str, mid: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    _mission(project_id, mid)
    return {"mission": _guard(lambda: _engine().deliver(project_id, _user_id(user), mid)).model_dump(mode="json")}
