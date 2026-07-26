import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.memory.manager import central_memory_manager

logger = logging.getLogger("aiforge.routes.memory")

router = APIRouter(tags=["Memory & Project Management"])


class MemorySaveRequest(BaseModel):
    project_id: str = Field(min_length=1)
    name: str = "Untitled Project"
    prompt: str = ""
    tech_stack: Dict[str, Any] = Field(default_factory=dict)
    architecture: Dict[str, Any] = Field(default_factory=dict)
    database_schema: str = ""
    generated_files: Dict[str, str] = Field(default_factory=dict)
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    commit_message: str = "Automated AIForge Save"


class MemoryUpdateRequest(BaseModel):
    name: Optional[str] = None
    prompt: Optional[str] = None
    tech_stack: Optional[Dict[str, Any]] = None
    architecture: Optional[Dict[str, Any]] = None
    database_schema: Optional[str] = None
    generated_files: Optional[Dict[str, str]] = None
    user_preferences: Optional[Dict[str, Any]] = None


class ResumeRequest(BaseModel):
    project_id: str
    new_prompt: str


@router.post("/memory/save")
@router.post("/api/memory/save")
def save_memory(req: MemorySaveRequest):
    """Saves or updates long-term memory and creates a version snapshot."""
    record = central_memory_manager.save_project(req.project_id, req.model_dump())
    return {"status": "success", "project": record}


@router.get("/memory/projects")
@router.get("/api/memory/projects")
def list_projects():
    """Lists all stored long-term memory projects."""
    return central_memory_manager.list_projects()


@router.get("/memory/project/{project_id}")
@router.get("/api/memory/project/{project_id}")
def get_project(project_id: str):
    """Retrieves long-term memory for a specific project."""
    record = central_memory_manager.get_project(project_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found in long-term memory.")
    versions = central_memory_manager.version_control.list_versions(project_id)
    return {"status": "success", "project": record, "versions": versions}


@router.put("/memory/project/{project_id}")
@router.put("/api/memory/project/{project_id}")
def update_project(project_id: str, req: MemoryUpdateRequest):
    """Updates fields of an existing project in long-term memory."""
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    record = central_memory_manager.update_project(project_id, updates)
    if not record:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    return {"status": "success", "project": record}


@router.delete("/memory/project/{project_id}")
@router.delete("/api/memory/project/{project_id}")
def delete_project(project_id: str):
    """Deletes a project from long-term memory."""
    success = central_memory_manager.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    return {"status": "success", "message": f"Deleted project '{project_id}' successfully."}


@router.get("/memory/search")
@router.get("/api/memory/search")
def search_memory(query: str = Query(..., min_length=1), top_k: int = 5):
    """Performs semantic relevance search across saved project memories."""
    results = central_memory_manager.search_projects(query, top_k=top_k)
    return {"query": query, "count": len(results), "projects": results}


@router.post("/memory/resume")
@router.post("/api/memory/resume")
def resume_project(req: ResumeRequest):
    """Resumes an existing project by bumping its version (v1 -> v2) and loading past memory."""
    try:
        record = central_memory_manager.resume_project(req.project_id, req.new_prompt)
        return {"status": "success", "project": record}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
