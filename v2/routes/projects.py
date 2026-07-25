"""
AIForge V2 – Projects REST API Router
====================================
FastAPI routes for Project CRUD lifecycles.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from v2.database.db import get_db
from v2.database.schemas_memory import ProjectCreateSchema
from v2.services.project_service import ProjectService

projects_router = APIRouter(prefix="/projects", tags=["projects"])


@projects_router.post("")
def api_create_project(req: ProjectCreateSchema, db: Session = Depends(get_db)):
    service = ProjectService(db)
    return service.create_new_project(req.title, req.description)


@projects_router.get("")
def api_list_projects(db: Session = Depends(get_db)):
    service = ProjectService(db)
    return service.fetch_all_projects()


@projects_router.get("/{project_id}")
def api_get_project(project_id: str, db: Session = Depends(get_db)):
    service = ProjectService(db)
    res = service.get_project_by_id(project_id)
    if not res:
        raise HTTPException(status_code=404, detail="Project not found")
    return res


@projects_router.put("/{project_id}")
def api_update_project(project_id: str, title: Optional[str] = None, status: Optional[str] = None, db: Session = Depends(get_db)):
    service = ProjectService(db)
    res = service.update_existing_project(project_id, title=title, status=status)
    if not res:
        raise HTTPException(status_code=404, detail="Project not found")
    return res


@projects_router.delete("/{project_id}")
def api_delete_project(project_id: str, db: Session = Depends(get_db)):
    service = ProjectService(db)
    success = service.remove_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "deleted", "id": project_id}
