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
  GET  /api/projects/{id}/swarm/missions/{mid}/report          ?format=markdown|json: the evidence-backed mission report
"""

import json
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from backend.auth.dependencies import get_current_user
from backend.evolution.autopilot.redact import redact
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
    return {"missions": [{"id": m.id, "objective": m.objective, "status": m.status, "outcome": m.outcome, "phase": m.phase,
                          "created_at": m.created_at,
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


@swarm_router.get(BASE + "/{mid}/report")
def report(project_id: str, mid: str, format: str = Query("markdown", pattern="^(markdown|json)$"),
           user: dict = Depends(get_current_user)):
    _project_dir(project_id, user)
    m = _mission(project_id, mid)
    if format == "json":
        return json.loads(redact(json.dumps({"mission": m.id, "objective": m.objective, "status": m.status, "outcome": m.outcome,
                                             "phase_history": m.phase_history, "autopilot_review": m.autopilot_review,
                                             "findings": [f.model_dump() for f in m.findings],
                                             "repairs": [r.model_dump() for r in m.repairs],
                                             "runtime": m.runtime, "properties": m.properties,
                                             "gates": [g.model_dump() for g in m.gates], "report": m.report})))
    r = m.autopilot_review or {}
    lines = [f"# Swarm mission report - {m.objective[:100]}", "",
             f"Mission `{m.id}`: **{m.outcome or m.status}** (phase {m.phase}). Contract version `{r.get('contract_version')}`.",
             "The swarm never writes to the project or deploys anything; results go to Autopilot for approval.", "",
             "## Versions", "", f"- backend: {r.get('backend_version')}", f"- frontend: {r.get('frontend_version')}", "",
             "## Integration test runs (isolated environment)", ""]
    for run in m.runtime:
        lines.append(f"### Run {run.get('id')} (round {run.get('round')}): {run.get('status')} {run.get('counts')} - {run.get('environment')}")
        if run.get("error"):
            lines.append(f"- error: {run['error']}")
        lines += [f"- [{c['status']}] {c['id']} {c['endpoint']}: expected {c['expected']}; observed {c['observed']}" for c in run.get("checks", [])]
        lines.append(f"- cleanup: {run.get('cleanup')}")
        lines.append("")
    lines += ["## Findings", ""] + [f"- [{f.status}] {f.category} ({f.basis}, responsible: {f.responsible or 'not established'}) "
                                    f"{f.endpoint}: expected {f.expected}; observed {f.observed}" for f in m.findings]
    lines += ["", "## Repair history", ""] + [f"- {x.id} {x.component} requested by {x.requested_by} at {x.requested_at}; author "
                                              f"{x.author}; changed {x.changed_files}; {x.artifact_before} -> {x.artifact_after}; "
                                              f"outcome {x.outcome}; validation {x.validation}" for x in m.repairs] or ["- none"]
    lines += ["", "## Gates", ""] + [f"- {g.name} ({'mandatory' if g.mandatory else 'optional'}): {g.status} - {g.detail}" for g in m.gates]
    lines += ["", "## Autopilot review", "", f"- approval status: {r.get('approval_status')}",
              f"- project modified: {r.get('project_modified')}; deployed: {r.get('deployed')}"]
    lines += [f"- proposed: {a}" for a in r.get("proposed_actions", [])]
    lines += ["", "## Limitations", ""] + [f"- {x}" for x in (m.report or {}).get("limitations", [])]
    return PlainTextResponse(redact("\n".join(lines)), media_type="text/markdown",
                             headers={"Content-Disposition": f'attachment; filename="swarm-{mid}.md"'})
