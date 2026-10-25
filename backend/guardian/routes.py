"""
AIForge Security Guardian REST API.

  POST /api/projects/{project_id}/guardian/assessments                     start an assessment (read-only analysis)
  GET  /api/projects/{project_id}/guardian/assessments                     history (assessments and verification jobs)
  GET  /api/projects/{project_id}/guardian/assessments/{id}                status, tools, coverage, audit
  POST /api/projects/{project_id}/guardian/assessments/{id}/abort
  GET  /api/projects/{project_id}/guardian/findings                        filters: severity, category, state, file, route, priority, q
  GET  /api/projects/{project_id}/guardian/findings/{id}                    evidence and verification
  POST /api/projects/{project_id}/guardian/verifications                   {"finding_ids": [...], "approved": true}
  POST /api/projects/{project_id}/guardian/findings/{id}/accept-risk       {"note": "..."}
  POST /api/projects/{project_id}/guardian/findings/{id}/plan              remediation -> Autopilot plan (origin "security")
  GET  /api/projects/{project_id}/guardian/gates/{execution_id}             the remediation's re-check
  GET  /api/projects/{project_id}/guardian/compare?first=&second=
  GET  /api/projects/{project_id}/guardian/report?format=markdown|json      redacted report of the latest assessment
Approval and execution of remediation plans use the Autopilot endpoints. Ownership as for Autopilot.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from backend.auth.dependencies import get_current_user
from backend.evolution.routes import _project_dir, _user_id
from backend.guardian.service import Busy, GuardianError, global_security_guardian

guardian_router = APIRouter(prefix="/api/projects", tags=["AIForge Security Guardian"])


def _engine():
    return global_security_guardian


def _get(project_id: str, kind: str, item_id: str):
    item = _engine().store.get(project_id, kind, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{kind[:-1].capitalize()} not found.")
    return item


@guardian_router.post("/{project_id}/guardian/assessments", status_code=202)
def start(project_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    path = _project_dir(project_id, user)
    try:
        a = _engine().start(project_id, path, _user_id(user))
    except Busy as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
    return {"assessment": a.model_dump(mode="json")}


@guardian_router.get("/{project_id}/guardian/assessments")
def history(project_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    items = sorted(_engine().store.list(project_id, "assessments"), key=lambda a: a.created_at, reverse=True)
    return {"assessments": [a.model_dump(mode="json", exclude={"audit", "coverage"}) for a in items[:50]],
            "active_job": _engine().active_job(project_id)}


@guardian_router.get("/{project_id}/guardian/assessments/{assessment_id}")
def get_assessment(project_id: str, assessment_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    return {"assessment": _get(project_id, "assessments", assessment_id).model_dump(mode="json"),
            "active_job": _engine().active_job(project_id)}


@guardian_router.post("/{project_id}/guardian/assessments/{assessment_id}/abort")
def abort(project_id: str, assessment_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    _get(project_id, "assessments", assessment_id)
    a = _engine().abort(project_id, assessment_id)
    return {"assessment": {"id": a.id, "status": a.status, "abort_requested": a.abort_requested}}


@guardian_router.get("/{project_id}/guardian/findings")
def findings(project_id: str, severity: Optional[str] = None, category: Optional[str] = None,
             state: Optional[str] = None, file: Optional[str] = None, route: Optional[str] = None,
             priority: Optional[str] = None, q: Optional[str] = Query(None, max_length=100),
             include_resolved: bool = False, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    items = _engine().store.list(project_id, "findings")
    if not include_resolved:
        items = [f for f in items if "resolved_at" not in f.context]
    for attr, value in (("severity", severity), ("category", category), ("state", state), ("priority", priority)):
        if value:
            items = [f for f in items if getattr(f, attr) in value.split(",")]
    if file:
        items = [f for f in items if (f.file or "").startswith(file)]
    if route:
        items = [f for f in items if f.route == route]
    if q:
        items = [f for f in items if q.lower() in f"{f.title} {f.description} {f.file} {f.rule_id}".lower()]
    sev = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    items.sort(key=lambda f: (f.priority, sev.get(f.severity, 9), f.file or ""))
    return {"total": len(items), "items": [f.model_dump(mode="json") for f in items]}


@guardian_router.get("/{project_id}/guardian/findings/{finding_id}")
def finding(project_id: str, finding_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    return {"finding": _get(project_id, "findings", finding_id).model_dump(mode="json")}


class VerifyRequest(BaseModel):
    finding_ids: List[str] = Field(..., min_length=1, max_length=20)
    approved: bool = False


@guardian_router.post("/{project_id}/guardian/verifications", status_code=202)
def verify(project_id: str, body: VerifyRequest, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    path = _project_dir(project_id, user)
    try:
        job = _engine().start_verification(project_id, path, _user_id(user), body.finding_ids, body.approved)
    except GuardianError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except Busy as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
    return {"verification": job.model_dump(mode="json")}


class AcceptRisk(BaseModel):
    note: str = Field(..., min_length=3, max_length=500)


@guardian_router.post("/{project_id}/guardian/findings/{finding_id}/accept-risk")
def accept_risk(project_id: str, finding_id: str, body: AcceptRisk, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    try:
        f = _engine().accept_risk(project_id, finding_id, _user_id(user), body.note)
    except KeyError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Finding not found.")
    except GuardianError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    return {"finding": f.model_dump(mode="json")}


@guardian_router.post("/{project_id}/guardian/findings/{finding_id}/plan", status_code=201)
def plan(project_id: str, finding_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    path = _project_dir(project_id, user)
    try:
        p = _engine().create_plan(project_id, path, _user_id(user), finding_id)
    except KeyError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Finding not found.")
    except GuardianError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    return {"plan": p.model_dump(mode="json")}


@guardian_router.get("/{project_id}/guardian/gates/{execution_id}")
def gate(project_id: str, execution_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    return {"gate": _get(project_id, "gates", execution_id).model_dump(mode="json")}


@guardian_router.get("/{project_id}/guardian/compare")
def compare(project_id: str, first: str = Query(..., max_length=40), second: str = Query(..., max_length=40),
            user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    try:
        return _engine().compare(project_id, first, second)
    except KeyError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Assessment not found.")


@guardian_router.get("/{project_id}/guardian/report")
def report(project_id: str, format: str = Query("markdown", pattern="^(markdown|json)$"),
           user: dict = Depends(get_current_user)):
    _project_dir(project_id, user)
    try:
        out = _engine().report(project_id, format)
    except KeyError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No completed assessment yet.")
    if format == "markdown":
        return PlainTextResponse(out, media_type="text/markdown",
                                 headers={"Content-Disposition": f'attachment; filename="security-report-{project_id}.md"'})
    return out
