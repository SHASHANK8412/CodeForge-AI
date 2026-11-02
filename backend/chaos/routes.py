"""
AIForge Chaos Engineer REST API.

  GET  /api/chaos/scenarios                                         supported scenarios (procedure, safety, cleanup)
  POST /api/projects/{project_id}/chaos/preflight                   safety checks for a configuration (runs nothing)
  POST /api/projects/{project_id}/chaos/assessments                 create: preflight -> awaiting_approval | refused
  GET  /api/projects/{project_id}/chaos/assessments                 history
  GET  /api/projects/{project_id}/chaos/assessments/{id}            status, live observations, report
  POST /api/projects/{project_id}/chaos/assessments/{id}/approve    explicit approval -> runs in the sandbox
  POST /api/projects/{project_id}/chaos/assessments/{id}/abort
  GET  /api/projects/{project_id}/chaos/compare?first=&second=       two assessments side by side
  GET  /api/projects/{project_id}/chaos/findings
  POST /api/projects/{project_id}/chaos/findings/{id}/plan          repair -> Autopilot plan (origin "chaos")
  GET  /api/projects/{project_id}/chaos/gates/{execution_id}         the repair's before/after experiment
Approving and executing a repair plan use the Autopilot endpoints. Projects and ownership as for Autopilot.
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.auth.dependencies import get_current_user
from backend.chaos.models import AssessmentConfig
from backend.chaos.sandbox import preflight
from backend.chaos.scenarios import NEEDS_DEPENDENCY, SCENARIOS, describe
from backend.chaos.service import Busy, ChaosError, global_chaos_engineer
from backend.evolution.routes import _project_dir, _user_id

chaos_router = APIRouter(tags=["AIForge Chaos Engineer"])


def _engine():
    return global_chaos_engineer


def _get(project_id: str, kind: str, item_id: str):
    item = _engine().store.get(project_id, kind, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{kind[:-1].capitalize()} not found.")
    return item


@chaos_router.get("/api/chaos/scenarios")
def scenarios(user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    return {"scenarios": [describe(s) for s in SCENARIOS.values()],
            "environments": [{"id": "sandbox", "supported": True,
                              "detail": "a disposable Docker network with no external route, created per experiment"},
                             {"id": "production", "supported": False,
                              "detail": "never targeted: experiments only run against disposable copies"}]}


def _validate(config: AssessmentConfig) -> None:
    unknown = [s for s in config.scenarios if s not in SCENARIOS]
    if unknown or not config.scenarios:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"unknown scenarios: {unknown}" if unknown else "choose a scenario")


@chaos_router.post("/api/projects/{project_id}/chaos/preflight")
def run_preflight(project_id: str, config: AssessmentConfig, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    path = _project_dir(project_id, user)
    _validate(config)
    checks = preflight(path, config, NEEDS_DEPENDENCY)
    return {"passed": all(c.passed for c in checks), "checks": [c.model_dump() for c in checks]}


@chaos_router.post("/api/projects/{project_id}/chaos/assessments", status_code=201)
def create_assessment(project_id: str, config: AssessmentConfig, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    path = _project_dir(project_id, user)
    _validate(config)
    try:
        a = _engine().create(project_id, path, _user_id(user), config)
    except ChaosError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    return {"assessment": a.model_dump(mode="json")}


@chaos_router.get("/api/projects/{project_id}/chaos/assessments")
def list_assessments(project_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    items = sorted(_engine().store.list(project_id, "assessments"), key=lambda a: a.created_at, reverse=True)
    return {"assessments": [{
        "id": a.id, "status": a.status, "created_at": a.created_at, "finished_at": a.finished_at,
        "scenarios": a.config.scenarios, "score": a.score.get("overall"), "error": a.error,
        "failed": [r.scenario for r in a.results if r.status == "failed"],
        "passed": [r.scenario for r in a.results if r.status == "passed"],
        "not_evaluated": [r.scenario for r in a.results if r.status not in ("passed", "failed")],
    } for a in items[:50]], "active_job": _engine().active_job(project_id)}


@chaos_router.get("/api/projects/{project_id}/chaos/assessments/{assessment_id}")
def get_assessment(project_id: str, assessment_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    return {"assessment": _get(project_id, "assessments", assessment_id).model_dump(mode="json"),
            "active_job": _engine().active_job(project_id)}


@chaos_router.post("/api/projects/{project_id}/chaos/assessments/{assessment_id}/approve", status_code=202)
def approve(project_id: str, assessment_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    path = _project_dir(project_id, user)
    _get(project_id, "assessments", assessment_id)
    try:
        a = _engine().approve(project_id, assessment_id, path, _user_id(user))
    except ChaosError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
    except Busy as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
    return {"assessment": a.model_dump(mode="json")}


@chaos_router.post("/api/projects/{project_id}/chaos/assessments/{assessment_id}/abort")
def abort(project_id: str, assessment_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    _get(project_id, "assessments", assessment_id)
    a = _engine().abort(project_id, assessment_id, _user_id(user))
    return {"assessment": a.model_dump(mode="json", include={"id", "status", "abort_requested"})}


@chaos_router.get("/api/projects/{project_id}/chaos/compare")
def compare(project_id: str, first: str = Query(..., max_length=40), second: str = Query(..., max_length=40),
            user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    a, b = _get(project_id, "assessments", first), _get(project_id, "assessments", second)
    ra, rb = {r.scenario: r for r in a.results}, {r.scenario: r for r in b.results}
    rows = []
    for sid in sorted(set(ra) | set(rb)):
        x, y = ra.get(sid), rb.get(sid)
        rows.append({"scenario": sid, "first": x.status if x else "not run", "second": y.status if y else "not run",
                     "first_recovery_s": x.recovery_seconds if x else None, "second_recovery_s": y.recovery_seconds if y else None,
                     "changed": [c.id for c in (y.criteria if y else []) if x and any(
                         d.id == c.id and d.status != c.status for d in x.criteria)]})
    return {"first": {"id": a.id, "created_at": a.created_at, "score": a.score.get("overall")},
            "second": {"id": b.id, "created_at": b.created_at, "score": b.score.get("overall")}, "scenarios": rows}


@chaos_router.get("/api/projects/{project_id}/chaos/findings")
def findings(project_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    order = {"reproduced": 0, "static_suspicion": 1}
    sev = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    items = sorted(_engine().store.list(project_id, "findings"),
                   key=lambda f: (order.get(f.kind, 9), sev.get(f.severity, 9), f.component))
    return {"items": [f.model_dump(mode="json") for f in items]}


@chaos_router.post("/api/projects/{project_id}/chaos/findings/{finding_id}/plan", status_code=201)
def plan(project_id: str, finding_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    path = _project_dir(project_id, user)
    try:
        p = _engine().create_plan(project_id, path, _user_id(user), finding_id)
    except KeyError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Finding not found.")
    except ChaosError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    return {"plan": p.model_dump(mode="json")}


@chaos_router.get("/api/projects/{project_id}/chaos/gates/{execution_id}")
def gate(project_id: str, execution_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    return {"gate": _get(project_id, "gates", execution_id).model_dump(mode="json")}
