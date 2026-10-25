"""
AIForge REST API — Live AI Canvas Engine
========================================
Endpoints for managing interactive multi-modal canvases, 2-way AI synchronization,
and version snapshot history.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Body, status
from pydantic import BaseModel, Field

from backend.canvas.canvas_service import (
    global_canvas_service,
    CanvasType,
    CanvasItem,
    CanvasVersion
)

router = APIRouter(prefix="/api/canvas", tags=["Live AI Canvas"])


class CreateCanvasPayload(BaseModel):
    title: str
    canvas_type: CanvasType = CanvasType.DOCUMENT
    content: Optional[Any] = None
    files: Optional[Dict[str, str]] = None
    project_id: Optional[str] = "aiforge-fooddelivery-ai"
    tags: List[str] = Field(default_factory=list)


class UpdateCanvasPayload(BaseModel):
    title: Optional[str] = None
    content: Optional[Any] = None
    files: Optional[Dict[str, str]] = None
    change_summary: Optional[str] = "Updated content"


class AITransformPayload(BaseModel):
    instruction: str
    selection_text: Optional[str] = None


@router.get("/list")
@router.get("")
def list_canvases(
    project_id: Optional[str] = Query(None, description="Filter by project"),
    canvas_type: Optional[str] = Query(None, description="Filter by canvas type")
):
    items = global_canvas_service.list_canvases(project_id=project_id, canvas_type=canvas_type)
    return {
        "success": True,
        "count": len(items),
        "canvases": [c.model_dump() for c in items]
    }


@router.get("/{canvas_id}")
def get_canvas(canvas_id: str):
    item = global_canvas_service.get_canvas(canvas_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Canvas '{canvas_id}' not found")
    return {
        "success": True,
        "canvas": item.model_dump()
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_canvas(payload: CreateCanvasPayload):
    if not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    item = global_canvas_service.create_canvas(
        title=payload.title,
        canvas_type=payload.canvas_type,
        content=payload.content,
        files=payload.files,
        project_id=payload.project_id,
        tags=payload.tags
    )
    return {
        "success": True,
        "canvas": item.model_dump()
    }


@router.put("/{canvas_id}")
def update_canvas(canvas_id: str, payload: UpdateCanvasPayload):
    item = global_canvas_service.update_canvas(
        canvas_id=canvas_id,
        content=payload.content,
        title=payload.title,
        files=payload.files,
        change_summary=payload.change_summary or "User Edit",
        author="User"
    )
    if not item:
        raise HTTPException(status_code=404, detail=f"Canvas '{canvas_id}' not found")
    return {
        "success": True,
        "canvas": item.model_dump()
    }


@router.delete("/{canvas_id}")
def delete_canvas(canvas_id: str):
    success = global_canvas_service.delete_canvas(canvas_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Canvas '{canvas_id}' not found")
    return {
        "success": True,
        "deleted_id": canvas_id
    }


@router.post("/{canvas_id}/ai-transform")
def ai_transform_canvas(canvas_id: str, payload: AITransformPayload):
    item = global_canvas_service.ai_transform_canvas(
        canvas_id=canvas_id,
        instruction=payload.instruction,
        selection_text=payload.selection_text
    )
    if not item:
        raise HTTPException(status_code=404, detail=f"Canvas '{canvas_id}' not found")
    return {
        "success": True,
        "canvas": item.model_dump()
    }


@router.get("/{canvas_id}/versions")
def get_canvas_versions(canvas_id: str):
    item = global_canvas_service.get_canvas(canvas_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Canvas '{canvas_id}' not found")
    return {
        "success": True,
        "canvas_id": canvas_id,
        "versions": [v.model_dump() for v in item.versions]
    }


@router.post("/{canvas_id}/versions/{version_id}/restore")
def restore_canvas_version(canvas_id: str, version_id: str):
    item = global_canvas_service.restore_version(canvas_id, version_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Canvas or version '{version_id}' not found")
    return {
        "success": True,
        "canvas": item.model_dump()
    }
