"""
AIForge Execution Guardian REST API. The project is resolved from its id with the same ownership checks as
Autopilot (no client-supplied paths); verification runs on an isolated copy in a background thread.

  POST /api/projects/{id}/verifications                    {"settings": {...}, "requirements": str} -> 202 + id
  GET  /api/projects/{id}/verifications                    recent verifications
  GET  /api/projects/{id}/verifications/{vid}              status, current operation, activity
  GET  /api/projects/{id}/verifications/{vid}/checks       individual check results
  GET  /api/projects/{id}/verifications/{vid}/repairs      repair history (+ failures before / after)
  GET  /api/projects/{id}/verifications/{vid}/report       ?format=json|markdown
  POST /api/projects/{id}/verifications/{vid}/cancel
(/api/verification is the Blockchain verifiable-records API.)
"""

import json
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from backend.auth.dependencies import get_current_user
from backend.evolution.autopilot.redact import redact
from backend.evolution.routes import _project_dir, _user_id
from backend.execution_guardian.service import Busy, GuardianError, global_execution_guardian

execution_guardian_router = APIRouter(tags=["AIForge Execution Guardian"])
BASE = "/api/projects/{project_id}/verifications"


def _g():
    return global_execution_guardian


def _get(project_id: str, vid: str):
    v = _g().store.get(project_id, "verifications", vid)
    if v is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Verification not found.")
    return v


class StartRequest(BaseModel):
    settings: Dict[str, float] = Field(default_factory=dict)
    requirements: str = Field("", max_length=4000)


@execution_guardian_router.post(BASE, status_code=202)
def start(project_id: str, body: StartRequest, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    path = _project_dir(project_id, user)
    try:
        v = _g().start(project_id, path, _user_id(user), body.settings, body.requirements)
    except GuardianError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e)) from None
    except Busy as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e)) from None
    return {"verification_id": v.id, "verification": v.model_dump(mode="json")}


@execution_guardian_router.get(BASE)
def verifications(project_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    items = sorted(_g().store.list(project_id, "verifications"), key=lambda v: v.started_at, reverse=True)
    return {"verifications": [{"id": v.id, "status": v.status, "source": v.source, "started_at": v.started_at,
                               "finished_at": v.finished_at, "repairs": len(v.repairs),
                               "checks": {c.name: c.status for c in v.checks}} for v in items[:50]],
            "active": _g().active(project_id)}


@execution_guardian_router.get(BASE + "/{vid}")
def verification(project_id: str, vid: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    v = _get(project_id, vid)
    return {"verification": v.model_dump(mode="json", exclude={"original_checks"})}


@execution_guardian_router.get(BASE + "/{vid}/checks")
def checks(project_id: str, vid: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    v = _get(project_id, vid)
    return {"status": v.status, "checks": [c.model_dump() for c in v.checks],
            "original_checks": [c.model_dump() for c in v.original_checks]}


@execution_guardian_router.get(BASE + "/{vid}/repairs")
def repairs(project_id: str, vid: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    v = _get(project_id, vid)
    return {"repairs": [r.model_dump() for r in v.repairs], "original_failures": [f.model_dump() for f in v.original_failures],
            "remaining_failures": [f.model_dump() for f in v.failures],
            "max_repair_attempts": v.settings.get("max_repair_attempts"), "delivery": v.delivery}


@execution_guardian_router.get(BASE + "/{vid}/report")
def report(project_id: str, vid: str, format: str = Query("json", pattern="^(json|markdown)$"),
           user: dict = Depends(get_current_user)):
    _project_dir(project_id, user)
    v = _get(project_id, vid)
    if v.status == "RUNNING":
        raise HTTPException(status.HTTP_409_CONFLICT, "The verification is still running.")
    r = v.report
    if format == "json":
        return json.loads(redact(json.dumps(r)))
    lines = [f"# Verification report - {v.project_id}", "", f"Verification `{v.id}`: **{r.get('status')}** - {r.get('statement')}.",
             f"Started {r.get('started_at')}, finished {r.get('finished_at')}.", "", "## Technology stack", "",
             f"- languages: {', '.join((r.get('technology_stack') or {}).get('languages') or []) or 'none detected'}",
             f"- frameworks: {', '.join((r.get('technology_stack') or {}).get('frameworks') or []) or 'none detected'}", "",
             "## Checks", ""]
    for c in r.get("checks", []):
        lines.append(f"- [{c['status']}] {c['label']}{'' if c['required'] else ' (optional)'} - {c.get('duration_seconds')} s"
                     + (f" - {c['error_summary']}" if c.get("error_summary") else "") + (f" - {c['reason']}" if c.get("reason") else ""))
    lines += ["", f"Counts: {r.get('counts')}. Tests: {r.get('test_summaries') or 'none ran'}.",
              f"Runtime startup: {r.get('runtime_startup')}.", "", "## Repairs", "", f"{r.get('repair_attempts')} attempt(s)."]
    lines += [f"- attempt {x.attempt}: {x.agent} via {x.strategy} -> {x.outcome}; files {x.files_changed or '-'}"
              + (f"; rejected {x.rejected_paths}" if x.rejected_paths else "") + (f"; {x.note}" if x.note else "") for x in v.repairs]
    lines += ["", "## Failures", "", "Discovered:"] + ([f"- [{f['category']}] {f['summary']}" for f in r.get("failures_discovered", [])]
                                                       or ["- none"])
    lines += ["Resolved:"] + ([f"- [{f['category']}] {f['summary']}" for f in r.get("failures_resolved", [])] or ["- none"])
    lines += ["Remaining:"] + ([f"- [{f['category']}] {f['summary']} -> {f['responsible_agent']}: {f['next_action']}"
                               for f in r.get("remaining_failures", [])] or ["- none"])
    lines += ["", "## What was tested", ""] + [f"- {x}" for x in r.get("what_was_tested", [])]
    lines += ["", "## What was not tested", ""] + ([f"- {x}" for x in r.get("what_was_not_tested", [])] or ["- nothing was skipped"])
    lines += ["", "## How to run it", ""] + [f"- `{x}`" for x in r.get("how_to_run", [])]
    lines += ["", "## Limitations", ""] + [f"- {x}" for x in r.get("limitations", [])]
    if v.delivery:
        lines += ["", f"Repaired files: {v.delivery}"]
    return PlainTextResponse(redact("\n".join(lines)), media_type="text/markdown",
                             headers={"Content-Disposition": f'attachment; filename="verification-{vid}.md"'})


@execution_guardian_router.post(BASE + "/{vid}/cancel")
def cancel(project_id: str, vid: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    _get(project_id, vid)
    v = _g().cancel(project_id, vid)
    return {"verification": {"id": v.id, "status": v.status, "cancel_requested": v.cancel_requested}}
