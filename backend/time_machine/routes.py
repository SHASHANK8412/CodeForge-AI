"""
AIForge Time Machine REST API (project access is checked as for Autopilot; every answer is stored state).

  GET  /api/projects/{id}/time-machine/events            types, sources, task_id, outcome, file, q, offset, limit (<=200)
  GET  /api/projects/{id}/time-machine/events/{eid}
  GET  /api/projects/{id}/time-machine/legacy            Flight Recorder events (read-only, unverified provenance)
  GET  /api/projects/{id}/time-machine/graph?task_id=
  GET  /api/projects/{id}/time-machine/replay/{task_id}  historical replay (nothing is executed)
  GET  /api/projects/{id}/time-machine/compare?first=&second=
  POST /api/projects/{id}/time-machine/checkpoints       {"name"}
  GET  /api/projects/{id}/time-machine/checkpoints
  POST /api/projects/{id}/time-machine/restore/preview   {"checkpoint_id"} or {"revert_change_id"}
  POST /api/projects/{id}/time-machine/restore/isolated  same target: rebuilt in a separate folder and tested
  POST /api/projects/{id}/time-machine/restore           target + {"token", "approved": true}: only safe files
  POST /api/projects/{id}/time-machine/investigations    the Regression Detective (202)
  POST /api/projects/{id}/time-machine/reruns            {"execution_id"} or {"experiment_id"} (202)
  GET  /api/projects/{id}/time-machine/jobs, /jobs/{jid}; POST /jobs/{jid}/cancel
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, model_validator

from backend.auth.dependencies import get_current_user
from backend.evolution.routes import _project_dir, _user_id
from backend.time_machine.service import Busy, TimeMachineError, global_time_machine

time_machine_router = APIRouter(prefix="/api/projects", tags=["AIForge Time Machine"])
BASE = "/{project_id}/time-machine"


def _tm():
    return global_time_machine


def _split(v: Optional[str]):
    return [x for x in (v or "").split(",") if x] or None


@time_machine_router.get(BASE + "/events")
def events(project_id: str, types: Optional[str] = None, sources: Optional[str] = None, task_id: Optional[str] = None,
           outcome: Optional[str] = None, file: Optional[str] = None, q: Optional[str] = Query(None, max_length=100),
           offset: int = Query(0, ge=0), limit: int = Query(50, ge=1), oldest_first: bool = False,
           user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    return _tm().timeline(project_id, types=_split(types), sources=_split(sources), task_id=task_id, outcome=outcome,
                          file=file, q=q, offset=offset, limit=limit, newest_first=not oldest_first)


@time_machine_router.get(BASE + "/events/{event_id}")
def event(project_id: str, event_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    e = _tm().ledger.get(project_id, event_id)
    if e is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Event not found.")
    return {"event": e.model_dump(mode="json"),
            "children": [c.id for c in _tm().ledger.events(project_id) if event_id in c.parents]}


@time_machine_router.get(BASE + "/legacy")
def legacy(project_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    return {"events": _tm().legacy(project_id)}


@time_machine_router.get(BASE + "/graph")
def graph(project_id: str, task_id: Optional[str] = None, limit: int = Query(300, ge=1, le=1000),
          user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    return _tm().graph(project_id, task_id, limit)


@time_machine_router.get(BASE + "/replay/{task_id}")
def replay(project_id: str, task_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    try:
        return _tm().replay(project_id, task_id)
    except KeyError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No recorded events for that task.")


@time_machine_router.get(BASE + "/compare")
def compare(project_id: str, first: str, second: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    try:
        return _tm().compare(project_id, first, second)
    except KeyError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Event not found.")


class CheckpointRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)


@time_machine_router.post(BASE + "/checkpoints", status_code=201)
def create_checkpoint(project_id: str, body: CheckpointRequest, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    path = _project_dir(project_id, user)
    e = _tm().checkpoint(project_id, path, _user_id(user), body.name)
    return {"checkpoint": {**e.model_dump(mode="json", exclude={"data"}),
                           "file_count": e.data.get("file_count"), "unstored": e.data.get("unstored")}}


@time_machine_router.get(BASE + "/checkpoints")
def checkpoints(project_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    items = _tm().ledger.query(project_id, types=["checkpoint_created"], limit=200)["items"]
    return {"checkpoints": [{"id": e.id, "name": e.data.get("name"), "at": e.at, "revision": e.revision,
                             "source": e.source, "file_count": e.data.get("file_count"),
                             "unstored": e.data.get("unstored"), "latest_test_outcome": e.data.get("latest_test_outcome")}
                            for e in items]}


class Target(BaseModel):
    checkpoint_id: Optional[str] = Field(None, max_length=40)
    revert_change_id: Optional[str] = Field(None, max_length=40)

    @model_validator(mode="after")
    def one(self):
        if bool(self.checkpoint_id) == bool(self.revert_change_id):
            raise ValueError("give exactly one of checkpoint_id or revert_change_id")
        return self

    def target(self) -> Dict[str, str]:
        return {k: v for k, v in self.model_dump().items() if k in ("checkpoint_id", "revert_change_id") and v}


class RestoreRequest(Target):
    token: str = Field(..., max_length=80)
    approved: bool = False


def _guard(fn):
    try:
        return fn()
    except KeyError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Checkpoint or change not found.")
    except TimeMachineError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except Busy as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))


@time_machine_router.post(BASE + "/restore/preview")
def preview(project_id: str, body: Target, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    path = _project_dir(project_id, user)
    return _guard(lambda: _tm().preview(project_id, path, body.target(), _user_id(user)))


@time_machine_router.post(BASE + "/restore/isolated")
def restore_isolated(project_id: str, body: Target, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    path = _project_dir(project_id, user)
    return _guard(lambda: _tm().restore_isolated(project_id, path, _user_id(user), body.target()))


@time_machine_router.post(BASE + "/restore")
def restore(project_id: str, body: RestoreRequest, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    path = _project_dir(project_id, user, writable=True)
    return _guard(lambda: _tm().restore(project_id, path, _user_id(user), body.target(), body.token, body.approved))


@time_machine_router.post(BASE + "/investigations", status_code=202)
def investigate(project_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    path = _project_dir(project_id, user)
    return {"job": _guard(lambda: _tm().investigate(project_id, path, _user_id(user))).model_dump(mode="json")}


class RerunRequest(BaseModel):
    execution_id: Optional[str] = Field(None, max_length=40)
    experiment_id: Optional[str] = Field(None, max_length=40)


@time_machine_router.post(BASE + "/reruns", status_code=202)
def rerun(project_id: str, body: RerunRequest, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    path = _project_dir(project_id, user)
    if bool(body.execution_id) == bool(body.experiment_id):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "give exactly one of execution_id or experiment_id")
    if body.execution_id:
        job = _guard(lambda: _tm().rerun(project_id, path, _user_id(user), body.execution_id))
    else:
        job = _guard(lambda: _tm().rerun_experiment(project_id, path, _user_id(user), body.experiment_id))
    return {"job": job.model_dump(mode="json")}


@time_machine_router.get(BASE + "/jobs")
def jobs(project_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    items = sorted(_tm().jobs.list(project_id, "jobs"), key=lambda j: j.created_at, reverse=True)
    return {"jobs": [j.model_dump(mode="json", exclude={"steps"}) for j in items[:50]]}


@time_machine_router.get(BASE + "/jobs/{job_id}")
def job(project_id: str, job_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    j = _tm().jobs.get(project_id, "jobs", job_id)
    if j is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found.")
    return {"job": j.model_dump(mode="json")}


@time_machine_router.post(BASE + "/jobs/{job_id}/cancel")
def cancel(project_id: str, job_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    j = _tm().cancel(project_id, job_id)
    if j is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found.")
    return {"job": {"id": j.id, "status": j.status, "cancel_requested": j.cancel_requested}}
