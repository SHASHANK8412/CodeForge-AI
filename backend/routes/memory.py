"""
AIForge Day 96 & 97 Project Memory API Router
=============================================
Endpoints:
- POST /memory/store
- GET /memory/projects
- GET /memory/search
- GET /memory/similar
- GET /memory/history
- GET /memory/project
- DELETE /memory/clear
"""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from backend.learning.project_memory import global_project_memory_store
from backend.learning.similarity import global_semantic_similarity_engine
from backend.memory.memory_manager import memory_manager

router = APIRouter(prefix="/memory", tags=["Memory"])


class StoreProjectRequest(BaseModel):
    prompt: str
    architecture: Optional[str] = "FastAPI + React"
    agents_used: Optional[List[str]] = None
    generated_files: Optional[List[str]] = None
    bugs: Optional[List[str]] = None
    fixes: Optional[List[str]] = None
    tests: Optional[Dict[str, Any]] = None
    review_score: Optional[float] = 95.6
    performance: Optional[Dict[str, Any]] = None


@router.post("/store")
def store_project_memory(request: StoreProjectRequest):
    rec = global_project_memory_store.store_project(
        prompt=request.prompt,
        architecture=request.architecture or "FastAPI + React",
        agents_used=request.agents_used,
        generated_files=request.generated_files,
        bugs=request.bugs,
        fixes=request.fixes,
        tests=request.tests,
        review_score=request.review_score or 95.6,
        performance=request.performance
    )
    return {
        "status": "success",
        "stored_project": rec
    }


@router.get("/projects")
def get_all_projects():
    projects = global_project_memory_store.get_all_projects()
    return {
        "count": len(projects),
        "projects": projects
    }


@router.get("/search")
def search_projects(query: str = Query(...)):
    matched = global_project_memory_store.search_projects(query)
    return {
        "query": query,
        "matched_count": len(matched),
        "results": matched
    }


@router.get("/similar")
def get_similar_projects(prompt: str = Query(...), top_k: int = Query(default=3)):
    similar = global_semantic_similarity_engine.find_similar_projects(prompt, top_k=top_k)
    return {
        "prompt": prompt,
        "similar_count": len(similar),
        "results": similar
    }


@router.get("/history")
def get_memory_history(session_id: str = Query(default="default")):
    return {
        "session_id": session_id,
        "history": memory_manager.get_history(session_id),
    }


@router.get("/project")
def get_project_memory(session_id: str = Query(default="default")):
    return {
        "session_id": session_id,
        "project": memory_manager.get_project(session_id),
    }


@router.delete("/clear")
def clear_memory(session_id: str = Query(default="default")):
    memory_manager.clear_session(session_id)
    return {
        "session_id": session_id,
        "success": True,
    }
