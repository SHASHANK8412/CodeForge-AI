"""
AIForge Day 22 — Long-Term Engineering Memory REST API Routes
=============================================================
Endpoints for:
- POST  /api/projects/{projectId}/memory
- GET   /api/projects/{projectId}/memory
- GET   /api/projects/{projectId}/memory/search
- GET   /api/projects/{projectId}/memory/graph
- GET   /api/projects/{projectId}/memory/dashboard
- GET   /api/projects/{projectId}/memory/{memoryId}
- PATCH /api/projects/{projectId}/memory/{memoryId}
- POST  /api/projects/{projectId}/memory/consolidate
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user
from backend.memory.service import global_engineering_memory_service
from backend.memory.models import MemoryType, MemorySource, MemoryConfidence
from backend.memory.graph import global_knowledge_graph_engine

day22_memory_router = APIRouter(prefix="/api/projects", tags=["Long-Term Engineering Memory & Knowledge Graph"])


class RememberPayload(BaseModel):
    title: str
    content: str
    type: MemoryType = MemoryType.ARCHITECTURE_DECISION
    source: MemorySource = MemorySource.DEBATE
    confidence: MemoryConfidence = MemoryConfidence.HIGH
    tags: List[str] = []


class UpdateMemoryPayload(BaseModel):
    new_content: str
    reason: str = "Migration"


@day22_memory_router.post("/{project_id}/memory")
async def create_memory(
    project_id: str,
    payload: RememberPayload,
    user: dict = Depends(get_current_user)
):
    mem = global_engineering_memory_service.remember(
        project_id=project_id,
        title=payload.title,
        content=payload.content,
        mem_type=payload.type,
        source=payload.source,
        confidence=payload.confidence,
        tags=payload.tags
    )
    return {"status": "success", "memory": mem.model_dump()}


@day22_memory_router.get("/{project_id}/memory")
async def list_memories(
    project_id: str,
    active_only: bool = Query(True),
    user: dict = Depends(get_current_user)
):
    from backend.memory.repository import global_memory_repository
    mems = global_memory_repository.get_by_project(project_id, active_only=active_only)
    if not mems:
        # Seed demo memory
        m1 = global_engineering_memory_service.remember(
            project_id=project_id,
            title="PostgreSQL chosen for transactional consistency",
            content="AIForge selected PostgreSQL due to order and payment ACID compliance requirements.",
            mem_type=MemoryType.ARCHITECTURE_DECISION,
            source=MemorySource.DEBATE
        )
        mems = [m1]
    return {"status": "success", "memories": [m.model_dump() for m in mems]}


@day22_memory_router.get("/{project_id}/memory/search")
async def search_memories(
    project_id: str,
    q: str = Query(...),
    user: dict = Depends(get_current_user)
):
    res = global_engineering_memory_service.search(project_id, q)
    return {"status": "success", "memories": [m.model_dump() for m in res]}


@day22_memory_router.get("/{project_id}/memory/graph")
async def get_knowledge_graph(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    graph = global_knowledge_graph_engine.build_knowledge_graph(project_id)
    return {"status": "success", "graph": graph.model_dump()}


@day22_memory_router.get("/{project_id}/memory/dashboard")
async def get_memory_dashboard(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    score = global_engineering_memory_service.get_quality_score(project_id)
    return {"status": "success", "dashboard": score.model_dump()}


@day22_memory_router.get("/{project_id}/memory/{memory_id}")
async def get_memory_detail(
    project_id: str,
    memory_id: str,
    user: dict = Depends(get_current_user)
):
    from backend.memory.repository import global_memory_repository
    mem = global_memory_repository.get(memory_id)
    if not mem:
        mems = global_memory_repository.get_by_project(project_id, active_only=False)
        mem = mems[0] if mems else None

    if not mem:
        raise HTTPException(status_code=404, detail="Memory not found")

    return {"status": "success", "memory": mem.model_dump()}


@day22_memory_router.patch("/{project_id}/memory/{memory_id}")
async def update_memory_version(
    project_id: str,
    memory_id: str,
    payload: UpdateMemoryPayload,
    user: dict = Depends(get_current_user)
):
    updated = global_engineering_memory_service.update(memory_id, payload.new_content, payload.reason)
    return {"status": "success", "memory": updated.model_dump()}


@day22_memory_router.post("/{project_id}/memory/consolidate")
async def consolidate_memories(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    mems = global_engineering_memory_service.consolidate(project_id)
    return {"status": "success", "memories": [m.model_dump() for m in mems]}
