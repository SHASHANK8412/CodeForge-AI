"""
AIForge V2 – Memory & Telemetry REST API Router
===============================================
FastAPI routes for project history, agent outputs, and telemetry execution logs.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from v2.database.db import get_db
from v2.services.memory_service import MemoryService

memory_router = APIRouter(prefix="", tags=["memory"])


@memory_router.get("/memory/{project_id}")
def api_get_memory(project_id: str, db: Session = Depends(get_db)):
    service = MemoryService(db)
    mem = service.get_project_memory(project_id)
    if not mem["project"]:
        raise HTTPException(status_code=404, detail="Project memory not found")
    return mem


@memory_router.get("/logs/{project_id}")
def api_get_logs(project_id: str, db: Session = Depends(get_db)):
    service = MemoryService(db)
    mem = service.get_project_memory(project_id)
    return {"project_id": project_id, "logs_count": mem["logs_count"], "logs": mem["logs"]}
