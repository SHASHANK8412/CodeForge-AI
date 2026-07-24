"""
AIForge Day 96 & 97 Feedback & Reflection API Router
=====================================================
Endpoints:
- POST /feedback
- POST /reflection
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from backend.learning.reflection import global_ai_reflection_engine
from backend.learning.feedback import global_feedback_engine

router = APIRouter(tags=["Feedback"])


class ReflectionRequest(BaseModel):
    project_name: str
    architecture_score: Optional[float] = 95.0
    code_quality_score: Optional[float] = 94.0
    security_score: Optional[float] = 98.0
    performance_score: Optional[float] = 92.0
    testing_score: Optional[float] = 97.0
    documentation_score: Optional[float] = 96.0


class FeedbackRequest(BaseModel):
    project_name: str
    problem: str
    solution: str
    category: Optional[str] = "general"


@router.post("/reflection")
def create_ai_reflection(request: ReflectionRequest):
    reflection = global_ai_reflection_engine.generate_reflection(
        project_name=request.project_name,
        architecture_score=request.architecture_score or 95.0,
        code_quality_score=request.code_quality_score or 94.0,
        security_score=request.security_score or 98.0,
        performance_score=request.performance_score or 92.0,
        testing_score=request.testing_score or 97.0,
        documentation_score=request.documentation_score or 96.0
    )
    return {
        "status": "success",
        "reflection": reflection
    }


@router.post("/feedback")
def submit_feedback(request: FeedbackRequest):
    rec = global_feedback_engine.record_mistake(
        problem=request.problem,
        solution=request.solution,
        category=request.category or "general"
    )
    return {
        "status": "success",
        "recorded_feedback": rec
    }
