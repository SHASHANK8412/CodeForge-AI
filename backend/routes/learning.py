import logging
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.learning.knowledge_base import global_knowledge_base
from backend.learning.retriever import global_knowledge_retriever
from backend.learning.analytics import global_learning_analytics

logger = logging.getLogger("aiforge.routes.learning")

router = APIRouter(tags=["Autonomous Learning & Knowledge Base"])


class StorePatternRequest(BaseModel):
    name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    description: str = Field(min_length=1)
    tags: List[str] = Field(default_factory=list)


@router.get("/knowledge")
@router.get("/api/knowledge")
def list_knowledge(category: Optional[str] = None):
    """Lists knowledge entries optionally filtered by category."""
    return {"entries": global_knowledge_base.list_knowledge(category)}


@router.get("/knowledge/search")
@router.get("/api/knowledge/search")
def search_knowledge(q: str = Query(..., min_length=1), top_k: int = Query(5, ge=1, le=20)):
    """Performs semantic vector search over the knowledge base."""
    results = global_knowledge_retriever.search_knowledge(q, top_k)
    return {"query": q, "count": len(results), "results": results}


@router.post("/knowledge/store")
@router.post("/api/knowledge/store")
def store_knowledge_pattern(req: StorePatternRequest):
    """Stores a new reusable pattern into the knowledge base."""
    entry = global_knowledge_base.store_pattern(req.name, req.category, req.description, req.tags)
    return {"status": "success", "entry": entry}


@router.get("/knowledge/templates")
@router.get("/api/knowledge/templates")
def get_architecture_templates():
    """Returns architecture template library."""
    return {"templates": global_knowledge_base.get_templates()}


@router.get("/learning/analytics")
@router.get("/api/learning/analytics")
def get_learning_analytics():
    """Returns continuous learning metrics and knowledge growth statistics."""
    return global_learning_analytics.get_analytics()
