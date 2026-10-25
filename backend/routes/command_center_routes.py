"""
AIForge REST API — Universal Command Center & Natural Language Router
=====================================================================
Endpoints:
- POST /api/command/route
- POST /api/command/quick-remember
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Body, status
from pydantic import BaseModel, Field

from backend.services.command_router_service import global_command_router
from backend.memory.ai_memory_service import global_ai_memory_service, MemoryCategory, MemoryImportance, MemoryScope

router = APIRouter(prefix="/api/command", tags=["Universal AI Command Center"])


class RouteCommandPayload(BaseModel):
    query: str
    current_project_id: Optional[str] = None
    current_view: Optional[str] = None


class QuickRememberPayload(BaseModel):
    content: str
    scope: str = "PERSONAL"
    project_id: Optional[str] = None
    category: str = "Preferences"


@router.post("/route")
def route_command(payload: RouteCommandPayload):
    resolution = global_command_router.resolve_command(
        query=payload.query,
        current_project_id=payload.current_project_id,
        current_view=payload.current_view
    )
    return {
        "success": True,
        "resolution": resolution.model_dump()
    }


@router.post("/quick-remember", status_code=status.HTTP_201_CREATED)
def quick_remember(payload: QuickRememberPayload):
    if not payload.content.strip():
        raise HTTPException(status_code=400, detail="Memory content cannot be empty")

    item = global_ai_memory_service.create_memory(
        title=f"Command Note: {payload.content[:35]}",
        content=payload.content.strip(),
        scope=MemoryScope.PROJECT if payload.scope == "PROJECT" else MemoryScope.PERSONAL,
        project_id=payload.project_id if payload.scope == "PROJECT" else None,
        category=MemoryCategory.PREFERENCES,
        importance=MemoryImportance.HIGH,
        source="Command Center",
        tags=["Quick Command", "User Note"]
    )
    return {
        "success": True,
        "memory": item.model_dump()
    }
