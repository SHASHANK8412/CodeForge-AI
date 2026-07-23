"""
FastAPI Routes for Day 73 Autonomous Learning & Self-Improvement Engine
======================================================================
Exposes REST endpoints for prior experience search, learning cycle execution,
prompt enhancement, architecture memory, and dashboard telemetry.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from backend.learning.learning_engine import global_learning_engine

router = APIRouter(prefix="/api/v1/learning", tags=["Learning & Self-Improvement Engine"])


class PriorSearchRequest(BaseModel):
    user_prompt: str


class PromptEnhanceRequest(BaseModel):
    prompt: str


class LearningCycleRequest(BaseModel):
    project_name: str
    project_type: str
    user_prompt: str
    technologies: List[str]
    architecture: str
    success: Optional[bool] = True
    execution_time: Optional[float] = 30.0
    errors: Optional[List[str]] = None
    fixes: Optional[List[str]] = None
    score: Optional[float] = 95.0


@router.post("/search-prior")
async def search_prior_experience(req: PriorSearchRequest) -> Dict[str, Any]:
    """Queries prior project memory before generation to reuse architectures and best practices."""
    try:
        res = global_learning_engine.query_prior_experience(req.user_prompt)
        return {"status": "success", "result": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enhance-prompt")
async def enhance_user_prompt(req: PromptEnhanceRequest) -> Dict[str, Any]:
    """Enhances user prompt before execution by attaching production requirements and best practices."""
    try:
        enhanced = global_learning_engine.prompt_optimizer.enhance_user_prompt(req.prompt)
        return {"status": "success", "enhanced_prompt": enhanced}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cycle")
async def execute_learning_cycle(req: LearningCycleRequest) -> Dict[str, Any]:
    """Executes continuous learning cycle post-generation."""
    try:
        res = global_learning_engine.run_learning_cycle(
            project_name=req.project_name,
            project_type=req.project_type,
            user_prompt=req.user_prompt,
            technologies=req.technologies,
            architecture=req.architecture,
            success=req.success,
            execution_time=req.execution_time,
            errors=req.errors,
            fixes=req.fixes,
            score=req.score
        )
        return {"status": "success", "result": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_learning_dashboard() -> Dict[str, Any]:
    """Returns telemetry data for AI Learning Dashboard."""
    try:
        telemetry = global_learning_engine.get_telemetry()
        return {"status": "success", "telemetry": telemetry}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/experiences")
async def get_experiences() -> Dict[str, Any]:
    """Returns all stored experiences."""
    try:
        experiences = global_learning_engine.experience_store.get_all_experiences()
        return {"status": "success", "experiences": experiences}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/architectures")
async def get_architectures() -> Dict[str, Any]:
    """Returns stored architectural recommendations by project category."""
    try:
        architectures = global_learning_engine.architecture_memory.get_all_architectures()
        return {"status": "success", "architectures": architectures}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/best-practices")
async def get_best_practices() -> Dict[str, Any]:
    """Returns list of active engineering best practices."""
    try:
        best_practices = global_learning_engine.best_practices.get_all_best_practices()
        return {"status": "success", "best_practices": best_practices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
