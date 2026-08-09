"""
FastAPI Routes for Day 41 Production-Ready Learning Engine
===========================================================
Exposes REST APIs for historical project memory, bug fix memory, pattern templates, semantic project search, user feedback collection, platform statistics, and the Learning Dashboard.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from backend.learning.project_memory import global_production_project_memory
from backend.learning.knowledge_store import global_production_knowledge_store
from backend.learning.pattern_detector import global_pattern_detector
from backend.learning.embedding_search import global_semantic_search_engine
from backend.learning.success_tracker import global_success_tracker
from backend.learning.learning_engine import global_production_learning_engine

router = APIRouter(tags=["Production-Ready Learning Engine"])


class RecordProjectInput(BaseModel):
    user_prompt: str
    architecture: Optional[str] = "Modular Monolith"
    generated_files: Optional[List[str]] = []
    technologies: Optional[List[str]] = ["FastAPI", "React"]
    execution_time_seconds: Optional[float] = 15.0
    success_status: Optional[str] = "SUCCESS"


class UserFeedbackInput(BaseModel):
    project_id: str
    rating: int  # 1 to 5 stars
    comment: Optional[str] = ""


class BugFixInput(BaseModel):
    bug: str
    cause: str
    solution: str
    affected_files: Optional[List[str]] = []
    confidence_score: Optional[float] = 0.95


@router.get("/learning/projects")
@router.get("/api/v1/learning/projects")
async def list_learned_projects() -> Dict[str, Any]:
    """Retrieves all historical project records stored in Project Memory."""
    projects = global_production_project_memory.get_all_projects()
    return {"status": "success", "total_projects": len(projects), "projects": projects}


@router.get("/learning/patterns")
@router.get("/api/v1/learning/patterns")
async def list_learned_patterns() -> Dict[str, Any]:
    """Retrieves all detected reusable software architecture and code patterns."""
    patterns = global_pattern_detector.get_all_templates()
    return {"status": "success", "total_patterns": len(patterns), "patterns": patterns}


@router.get("/learning/bugs")
@router.get("/api/v1/learning/bugs")
async def list_learned_bugs() -> Dict[str, Any]:
    """Retrieves Bug Memory repository with causes, solutions, and confidence scores."""
    bugs = global_production_knowledge_store.get_all_bugs()
    return {"status": "success", "total_bugs": len(bugs), "bugs": bugs}


@router.get("/learning/statistics")
@router.get("/api/v1/learning/statistics")
async def get_learning_statistics() -> Dict[str, Any]:
    """Retrieves platform-wide learning analytics and agent performance metrics."""
    stats = global_success_tracker.get_statistics()
    return {"status": "success", "statistics": stats["statistics"]}


@router.post("/learning/project")
@router.post("/api/v1/learning/project")
async def store_project_memory(req: RecordProjectInput) -> Dict[str, Any]:
    """Stores a generated project into persistent Project Memory."""
    try:
        rec = global_production_project_memory.record_project(
            user_prompt=req.user_prompt,
            architecture=req.architecture or "Modular Monolith",
            generated_files=req.generated_files or [],
            technologies=req.technologies or ["FastAPI", "React"],
            execution_time_seconds=req.execution_time_seconds or 15.0,
            success_status=req.success_status or "SUCCESS"
        )
        return {"status": "success", "project_record": rec}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/learning/feedback")
@router.post("/api/v1/learning/feedback")
async def submit_user_feedback(req: UserFeedbackInput) -> Dict[str, Any]:
    """Submits user feedback rating and comments for a generated project."""
    try:
        updated = global_production_project_memory.add_user_feedback(req.project_id, req.rating, req.comment or "")
        return {"status": "success", "project_record": updated}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/learning/search")
@router.get("/api/v1/learning/search")
async def search_learned_projects(q: str = Query(..., description="Semantic search query prompt")) -> Dict[str, Any]:
    """Performs semantic vector search over past successful project blueprints."""
    res = global_semantic_search_engine.search_similar_projects(q)
    return {"status": "success", "search_results": res}


@router.get("/learning/dashboard")
@router.get("/api/v1/learning/dashboard")
async def get_learning_dashboard() -> Dict[str, Any]:
    """Retrieves Learning Dashboard data: Projects Stored, Patterns Learned, Bug Library, Best Practices, Success Rate %, Build Time, Tech Stack, Base Size."""
    dash = global_production_learning_engine.get_dashboard_data()
    return {"status": "success", "learning_dashboard": dash}
