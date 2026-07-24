"""
AIForge Day 101 Product Intelligence & Requirements API Router
==============================================================
Endpoints:
- POST /product/feedback/analyze
- POST /product/roadmap
- POST /product/backlog/prioritize
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from backend.agents.product_manager import global_product_manager_agent
from backend.services.feedback_service import global_feedback_service
from backend.services.roadmap_service import global_roadmap_service

router = APIRouter(prefix="/product", tags=["Product Manager"])


class FeedbackAnalysisRequest(BaseModel):
    feedback_list: Optional[List[str]] = None
    github_issues: Optional[List[str]] = None


class RoadmapRequest(BaseModel):
    features: List[str]


@router.post("/feedback/analyze")
def analyze_product_feedback(request: FeedbackAnalysisRequest):
    return global_product_manager_agent.analyze_feedback_and_plan(
        feedback_list=request.feedback_list,
        github_issues=request.github_issues
    )


@router.post("/roadmap")
def generate_product_roadmap(request: RoadmapRequest):
    return global_roadmap_service.generate_sprint_roadmap(request.features)


@router.post("/backlog/prioritize")
def prioritize_backlog(request: RoadmapRequest):
    return global_feedback_service.categorize_feedback(request.features)
