"""
AIForge REST API — Canvas
=========================
A user's canvases (documents, code, roadmaps, tables, diagrams) with version history.
Every canvas belongs to the user who created it; someone else's canvas answers 404.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.auth.dependencies import get_current_user
from backend.auth.ownership import user_id_of
from backend.canvas.canvas_service import CanvasType, global_canvas_service

router = APIRouter(prefix="/api/canvas", tags=["Canvas"])


class CreateCanvasPayload(BaseModel):
    title: str
    canvas_type: CanvasType = CanvasType.DOCUMENT
    content: Optional[Any] = None
    files: Optional[Dict[str, str]] = None
    project_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class UpdateCanvasPayload(BaseModel):
    title: Optional[str] = None
    canvas_type: Optional[CanvasType] = None
    content: Optional[Any] = None
    files: Optional[Dict[str, str]] = None
    change_summary: Optional[str] = "Updated content"


def _own_canvas(canvas_id: str, user: dict):
    item = global_canvas_service.get_canvas(canvas_id, user_id_of(user))
    if not item:
        raise HTTPException(status_code=404, detail=f"Canvas '{canvas_id}' not found")
    return item


@router.get("/list")
@router.get("")
def list_canvases(
    project_id: Optional[str] = Query(None, description="Filter by project"),
    canvas_type: Optional[str] = Query(None, description="Filter by canvas type"),
    user: dict = Depends(get_current_user),
):
    items = global_canvas_service.list_canvases(user_id_of(user), project_id=project_id, canvas_type=canvas_type)
    return {
        "success": True,
        "count": len(items),
        "canvases": [c.model_dump() for c in items]
    }


@router.get("/{canvas_id}")
def get_canvas(canvas_id: str, user: dict = Depends(get_current_user)):
    return {
        "success": True,
        "canvas": _own_canvas(canvas_id, user).model_dump()
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_canvas(payload: CreateCanvasPayload, user: dict = Depends(get_current_user)):
    if not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    item = global_canvas_service.create_canvas(
        title=payload.title,
        canvas_type=payload.canvas_type,
        content=payload.content,
        files=payload.files,
        project_id=payload.project_id,
        tags=payload.tags,
        owner_id=user_id_of(user),
    )
    return {
        "success": True,
        "canvas": item.model_dump()
    }


@router.put("/{canvas_id}")
def update_canvas(canvas_id: str, payload: UpdateCanvasPayload, user: dict = Depends(get_current_user)):
    _own_canvas(canvas_id, user)
    item = global_canvas_service.update_canvas(
        canvas_id=canvas_id,
        content=payload.content,
        title=payload.title,
        files=payload.files,
        canvas_type=payload.canvas_type,
        change_summary=payload.change_summary or "User Edit",
        author="User"
    )
    return {
        "success": True,
        "canvas": item.model_dump()
    }


@router.delete("/{canvas_id}")
def delete_canvas(canvas_id: str, user: dict = Depends(get_current_user)):
    _own_canvas(canvas_id, user)
    global_canvas_service.delete_canvas(canvas_id)
    return {
        "success": True,
        "deleted_id": canvas_id
    }


@router.get("/{canvas_id}/versions")
def get_canvas_versions(canvas_id: str, user: dict = Depends(get_current_user)):
    item = _own_canvas(canvas_id, user)
    return {
        "success": True,
        "canvas_id": canvas_id,
        "versions": [v.model_dump() for v in item.versions]
    }


@router.post("/{canvas_id}/versions/{version_id}/restore")
def restore_canvas_version(canvas_id: str, version_id: str, user: dict = Depends(get_current_user)):
    _own_canvas(canvas_id, user)
    item = global_canvas_service.restore_version(canvas_id, version_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Version '{version_id}' not found")
    return {
        "success": True,
        "canvas": item.model_dump()
    }
