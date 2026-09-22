import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Query, Depends, status
from pydantic import BaseModel, Field

from backend.auth.dependencies import get_current_user
from backend.memory.memory_manager import global_memory_manager

logger = logging.getLogger("aiforge.routes.memory")

router = APIRouter(prefix="/api/projects", tags=["Project Memory & Decisions"])


class SearchMemoryRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = 5


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/{project_id}/memory")
def get_project_memory(
    project_id: str,
    memory_type: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """
    Returns persistent memory items and architectural decisions for a project.
    Only project owners can access project memory.
    """
    memories = global_memory_manager.long_term.get_memories(project_id, memory_type=memory_type)
    decisions = global_memory_manager.get_decisions(project_id)

    return {
        "status": "success",
        "project_id": project_id,
        "memories_count": len(memories),
        "decisions_count": len(decisions),
        "memories": [m.model_dump() for m in memories],
        "decisions": [d.model_dump() for d in decisions]
    }


@router.post("/{project_id}/memory/search")
def search_project_memory(
    project_id: str,
    req: SearchMemoryRequest,
    user: dict = Depends(get_current_user)
):
    """
    Performs relevant search across saved project memories and decisions.
    """
    results = global_memory_manager.search(project_id, req.query, top_k=req.top_k)
    return {
        "status": "success",
        "project_id": project_id,
        "query": req.query,
        "results_count": len(results),
        "results": [r.model_dump() for r in results]
    }


@router.delete("/{project_id}/memory/{memory_id}")
def delete_project_memory(
    project_id: str,
    memory_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Deletes a specific memory record.
    """
    success = global_memory_manager.delete(project_id, memory_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory record '{memory_id}' not found for project '{project_id}'."
        )
    return {"status": "success", "message": f"Memory '{memory_id}' deleted successfully."}


@router.get("/{project_id}/explain")
def explain_project_decision(
    project_id: str,
    topic: str = Query(..., description="Decision topic or question, e.g., 'PostgreSQL' or 'FastAPI'"),
    user: dict = Depends(get_current_user)
):
    """
    Provides explainability on why a specific architectural choice was made by an agent.
    """
    explanation = global_memory_manager.explain_decision(project_id, topic)
    return {"status": "success", **explanation}
