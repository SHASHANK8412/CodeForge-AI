"""
AIForge Integration & Compatibility Engine REST API. Project-scoped like the Execution Guardian's verifications: the
project is resolved from its id with the Autopilot ownership checks (no client-supplied paths or files), and every
route needs an authenticated user who may work on the project.

  POST /api/projects/{id}/contract                    {"contract": {...}, "reason": str} -> 201 new version (+ change)
  POST /api/projects/{id}/contract/derive             {"reason"?} -> a version derived from the generation's architecture
  GET  /api/projects/{id}/contract                    ?version=N&agent=frontend|backend|database (an agent's slice)
  GET  /api/projects/{id}/contract/versions           every version (who, why, when, breaking)
  GET  /api/projects/{id}/contract/diff               ?from=N&to=M (default: the current version against its parent)
  POST /api/projects/{id}/integration/analyze         static compatibility analysis -> the run (synchronous)
  POST /api/projects/{id}/integration/verify          {"settings": {...}} -> 202 + run id (tests + bounded repairs)
  GET  /api/projects/{id}/integration/runs            recent runs
  GET  /api/projects/{id}/integration/runs/{run_id}   status, findings, tests, repairs, activity
  GET  /api/projects/{id}/integration/runs/{run_id}/report   ?format=json|markdown
  POST /api/projects/{id}/integration/runs/{run_id}/cancel

(The proposed /api/contracts and /api/integration/{run_id} paths map onto these: runs and contracts belong to a
project, so they are addressed through it, as every other project resource here is.)
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from backend.auth.dependencies import get_current_user
from backend.compatibility import contract as ct
from backend.compatibility.service import Busy, ContractError, global_integration_engine, markdown
from backend.evolution.autopilot.redact import redact
from backend.evolution.routes import _project_dir, _user_id

integration_router = APIRouter(tags=["AIForge Integration & Compatibility Engine"])
BASE = "/api/projects/{project_id}"


def _e():
    return global_integration_engine


def _architecture(project_id: str) -> Dict[str, Any]:
    """The architecture and plan the generation's workflow recorded for this project (graph state)."""
    from backend.graph.parallel_workflow import parallel_graph
    try:
        st = parallel_graph.get_state({"configurable": {"thread_id": project_id}})
    except Exception:  # noqa: BLE001 - no checkpoint: nothing to derive from
        return {}
    values = dict(st.values or {}) if st else {}
    return {"architecture": values.get("architecture") or {}, "plan": values.get("plan") or {}}


class ContractRequest(BaseModel):
    contract: Dict[str, Any]
    reason: str = Field(..., min_length=3, max_length=500)


class DeriveRequest(BaseModel):
    reason: str = Field("derived from the generation's architecture", min_length=3, max_length=500)


class VerifyRequest(BaseModel):
    settings: Dict[str, float] = Field(default_factory=dict)


def _contract_out(c, change=None, warnings=None) -> Dict[str, Any]:
    out = {"contract": c.model_dump(mode="json")}
    if change is not None:
        out["change"] = change.model_dump(mode="json")
    if warnings:
        out["warnings"] = warnings
    return out


@integration_router.post(BASE + "/contract", status_code=201)
def register_contract(project_id: str, body: ContractRequest, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    try:
        c, change, warnings = _e().register(project_id, body.contract, f"user {_user_id(user)}", body.reason, source="user")
    except ContractError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, {"errors": e.errors}) from None
    return _contract_out(c, change, warnings)


@integration_router.post(BASE + "/contract/derive", status_code=201)
def derive_contract(project_id: str, body: Optional[DeriveRequest] = None, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    src = _architecture(project_id)
    if not (src.get("architecture") or {}).get("routes") and not (src.get("architecture") or {}).get("models") \
            and not (src.get("architecture") or {}).get("apis"):
        raise HTTPException(status.HTTP_409_CONFLICT, "No architecture with API routes or data models is recorded for this "
                                                      "project: register the contract explicitly.")
    try:
        c, change, warnings = _e().derive(project_id, src["architecture"], src.get("plan"), author=f"user {_user_id(user)} (architecture)",
                                          reason=(body.reason if body else DeriveRequest().reason))
    except ContractError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, {"errors": e.errors}) from None
    return _contract_out(c, change, warnings)


@integration_router.get(BASE + "/contract")
def get_contract(project_id: str, version: Optional[int] = Query(None, ge=1),
                 agent: Optional[str] = Query(None, pattern="^(frontend|backend|database)$"),
                 user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    c = _e().version(project_id, version) if version else _e().current(project_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such contract version." if version else "No contract is registered.")
    if agent:
        return {"version": c.version, "agent": agent, "slice": ct.slice_for(c, agent)}
    return {"contract": c.model_dump(mode="json"), "versions": len(_e().versions(project_id))}


@integration_router.get(BASE + "/contract/versions")
def contract_versions(project_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    changes = {ch.to_version: ch for ch in _e().changes(project_id)}
    return {"versions": [{"version": c.version, "revision": c.revision, "author": c.author, "reason": c.reason, "source": c.source,
                          "created_at": c.created_at, "operations": len(c.api.endpoints), "entities": len(c.entities),
                          "breaking": changes[c.version].breaking if c.version in changes else None,
                          "changes": len(changes[c.version].items) if c.version in changes else 0}
                         for c in reversed(_e().versions(project_id))]}


@integration_router.get(BASE + "/contract/diff")
def contract_diff(project_id: str, from_: Optional[int] = Query(None, alias="from", ge=1), to: Optional[int] = Query(None, ge=1),
                  user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    try:
        return _e().diff(project_id, from_, to)
    except KeyError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e).strip("'")) from None


@integration_router.post(BASE + "/integration/analyze")
def analyze(project_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    path = _project_dir(project_id, user)
    try:
        r = _e().analyze(project_id, path, _user_id(user))
    except ContractError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, {"errors": e.errors}) from None
    return {"run_id": r.id, "run": r.model_dump(mode="json", exclude={"implementation"})}


@integration_router.post(BASE + "/integration/verify", status_code=202)
def verify(project_id: str, body: VerifyRequest, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    path = _project_dir(project_id, user)
    try:
        r = _e().start_verify(project_id, path, _user_id(user), body.settings)
    except ContractError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, {"errors": e.errors}) from None
    except Busy as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e)) from None
    return {"run_id": r.id, "run": r.model_dump(mode="json", exclude={"implementation"})}


@integration_router.get(BASE + "/integration/runs")
def runs(project_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    return {"runs": [{"id": r.id, "kind": r.kind, "source": r.source, "status": r.status, "contract_version": r.contract_version,
                      "started_at": r.started_at, "finished_at": r.finished_at, "repairs": len(r.repairs),
                      "open_findings": sum(1 for f in r.findings if f.status in ("open", "unresolved", "needs_contract_decision", "blocked"))}
                     for r in _e().runs(project_id)[:50]]}


def _run(project_id: str, run_id: str):
    try:
        return _e().get(project_id, run_id)
    except KeyError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Integration run not found.") from None


@integration_router.get(BASE + "/integration/runs/{run_id}")
def run(project_id: str, run_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    return {"run": _run(project_id, run_id).model_dump(mode="json", exclude={"implementation"})}


@integration_router.get(BASE + "/integration/runs/{run_id}/report")
def report(project_id: str, run_id: str, format: str = Query("json", pattern="^(json|markdown)$"),
           user: dict = Depends(get_current_user)):
    _project_dir(project_id, user)
    r = _run(project_id, run_id)
    if r.status in ("queued", "running"):
        raise HTTPException(status.HTTP_409_CONFLICT, "The integration run is still running.")
    if format == "json":
        return r.report
    return PlainTextResponse(redact(markdown(r.report), 200_000), media_type="text/markdown",
                             headers={"Content-Disposition": f'attachment; filename="compatibility-{run_id}.md"'})


@integration_router.post(BASE + "/integration/runs/{run_id}/cancel")
def cancel(project_id: str, run_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    _run(project_id, run_id)
    r = _e().cancel(project_id, run_id)
    return {"run": {"id": r.id, "status": r.status, "cancel_requested": r.cancel_requested}}
