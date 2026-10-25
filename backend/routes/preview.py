"""
Live preview of a generated project (see backend/execution/preview_manager.py).

POST /api/projects/{project_id}/preview/start   start or restart; returns at once ("starting")
GET  /api/projects/{project_id}/preview/status  status and the URLs that answered an HTTP probe
GET  /api/projects/{project_id}/preview/logs    recent container logs per service
POST /api/projects/{project_id}/preview/stop    stop and remove the containers

project_id is a generation id or a folder under generated_projects/.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from backend.auth.dependencies import get_current_user
from backend.execution import preview_manager

router = APIRouter(prefix="/api/projects", tags=["preview"])


def _project_dir(project_id: str) -> Path:
    from backend.routes.export import _generation_record, _safe_project_dir
    record = _generation_record(project_id)
    project_dir = _safe_project_dir(record.get("project_path", "") if record else project_id)
    if not project_dir:
        raise HTTPException(status_code=404, detail=f"No generated project folder for '{project_id}'.")
    return project_dir


def _status(project_id: str) -> dict:
    preview = preview_manager.get_preview(project_id)
    if not preview:
        return {"project_id": project_id, "status": "not_started"}
    data = preview.to_dict()
    for svc in ("backend", "frontend"):
        data[svc].pop("logs", None)
    return data


@router.post("/{project_id}/preview/start")
def start_project_preview(project_id: str, user: dict = Depends(get_current_user)):
    preview_manager.start_preview(project_id, _project_dir(project_id))
    return _status(project_id)


@router.get("/{project_id}/preview/status")
def get_project_preview_status(project_id: str, user: dict = Depends(get_current_user)):
    return _status(project_id)


@router.get("/{project_id}/preview/logs")
def get_project_preview_logs(project_id: str, user: dict = Depends(get_current_user)):
    preview = preview_manager.get_preview(project_id)
    if not preview:
        return {"backend": "", "frontend": ""}
    return {"backend": preview.backend.logs, "frontend": preview.frontend.logs}


@router.post("/{project_id}/preview/stop")
def stop_project_preview(project_id: str, user: dict = Depends(get_current_user)):
    return {"stopped": preview_manager.stop_preview(project_id), **_status(project_id)}
