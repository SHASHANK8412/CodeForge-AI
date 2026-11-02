"""
AIForge REST API — AI Memory Management & Smart Recall
======================================================
Endpoints for:
- GET    /api/memory/list
- POST   /api/memory
- GET    /api/memory/{memory_id}
- PUT    /api/memory/{memory_id}
- DELETE /api/memory/{memory_id}
- POST   /api/memory/recall
- POST   /api/memory/suggest
- DELETE /api/memory/project/{project_id}
- DELETE /api/memory/clear/all
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Body, status
from pydantic import BaseModel, Field

from backend.memory.ai_memory_service import (
    global_ai_memory_service,
    MemoryScope,
    MemoryCategory,
    MemoryImportance
)

router = APIRouter(prefix="/api/memory", tags=["AI Memory & Smart Recall"])


class CreateMemoryPayload(BaseModel):
    title: str
    content: str
    scope: MemoryScope = MemoryScope.PERSONAL
    project_id: Optional[str] = None
    category: MemoryCategory = MemoryCategory.PREFERENCES
    importance: MemoryImportance = MemoryImportance.HIGH
    source: str = "User"
    tags: List[str] = Field(default_factory=list)
    pinned: bool = False


class UpdateMemoryPayload(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[MemoryCategory] = None
    importance: Optional[MemoryImportance] = None
    tags: Optional[List[str]] = None
    pinned: Optional[bool] = None
    project_id: Optional[str] = None


class SmartRecallPayload(BaseModel):
    prompt: str
    project_id: Optional[str] = None
    limit: int = 5


class SuggestMemoryPayload(BaseModel):
    user_prompt: str
    assistant_response: str


@router.get("/list")
@router.get("")
def list_memories(
    scope: Optional[str] = Query(None, description="Filter by scope: PERSONAL or PROJECT"),
    project_id: Optional[str] = Query(None, description="Filter by project_id"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Fuzzy search title, content, or tags"),
    sort_by: str = Query("recent", description="recent, most_used, importance, title")
):
    memories = global_ai_memory_service.list_memories(
        scope=scope,
        project_id=project_id,
        category=category,
        search=search,
        sort_by=sort_by
    )
    return {
        "success": True,
        "count": len(memories),
        "memories": [m.model_dump() for m in memories]
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_memory(payload: CreateMemoryPayload):
    if not payload.title.strip() or not payload.content.strip():
        raise HTTPException(status_code=400, detail="Title and content are required")

    item = global_ai_memory_service.create_memory(
        title=payload.title,
        content=payload.content,
        scope=payload.scope,
        project_id=payload.project_id,
        category=payload.category,
        importance=payload.importance,
        source=payload.source,
        tags=payload.tags,
        pinned=payload.pinned
    )
    return {
        "success": True,
        "memory": item.model_dump()
    }


@router.get("/{memory_id}")
def get_memory(memory_id: str):
    item = global_ai_memory_service.get_memory(memory_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found")
    return {
        "success": True,
        "memory": item.model_dump()
    }


@router.put("/{memory_id}")
def update_memory(memory_id: str, payload: UpdateMemoryPayload):
    updated = global_ai_memory_service.update_memory(
        memory_id=memory_id,
        title=payload.title,
        content=payload.content,
        category=payload.category,
        importance=payload.importance,
        tags=payload.tags,
        pinned=payload.pinned,
        project_id=payload.project_id
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found")
    return {
        "success": True,
        "memory": updated.model_dump()
    }


@router.delete("/{memory_id}")
def delete_memory(memory_id: str):
    success = global_ai_memory_service.delete_memory(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found")
    return {
        "success": True,
        "deleted_id": memory_id
    }


@router.post("/recall")
def smart_recall(payload: SmartRecallPayload):
    result = global_ai_memory_service.smart_recall(
        user_prompt=payload.prompt,
        project_id=payload.project_id,
        limit=payload.limit
    )
    return {
        "success": True,
        **result
    }


@router.post("/suggest")
def suggest_memory(payload: SuggestMemoryPayload):
    suggestions = global_ai_memory_service.generate_memory_suggestions(
        user_prompt=payload.user_prompt,
        assistant_response=payload.assistant_response
    )
    return {
        "success": True,
        "suggestions": suggestions
    }


@router.delete("/project/{project_id}")
def clear_project_memory(project_id: str):
    deleted_count = global_ai_memory_service.clear_project_memory(project_id)
    return {
        "success": True,
        "project_id": project_id,
        "deleted_count": deleted_count
    }


@router.delete("/clear/all")
def clear_all_memory():
    deleted_count = global_ai_memory_service.clear_all_memory()
    return {
        "success": True,
        "deleted_count": deleted_count
    }
