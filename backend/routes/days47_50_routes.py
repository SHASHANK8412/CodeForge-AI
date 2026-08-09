"""
FastAPI Routes for Days 47-50 Autonomous AI Software Engineer Platform
========================================================================
Exposes REST APIs for Self-Healing Debug Engine (Day 47), AI Refactoring Engine (Day 48), AI Architecture Optimizer (Day 49), and AI Product Manager / SRS Generator (Day 50).
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from backend.self_healing.debug_pipeline import global_debug_pipeline
from backend.self_healing.build_validator import global_build_validator
from backend.refactoring.quality_scorer import global_quality_scorer
from backend.refactoring.refactoring_agent import global_refactoring_agent
from backend.architecture.optimizer_agent import global_architecture_optimizer
from backend.product_manager.requirement_agent import global_requirement_agent
from backend.product_manager.clarification_flow import global_clarification_flow

router = APIRouter(tags=["Days 47-50 Autonomous Software Engineering Platform"])


class DebugRequest(BaseModel):
    project_files: Dict[str, str]
    max_retries: Optional[int] = 3


class RefactoringRequest(BaseModel):
    project_files: Dict[str, str]


class ArchitectureRequest(BaseModel):
    prompt: str
    target_users: Optional[int] = 10000000


class SRSRequest(BaseModel):
    idea: str


# Day 47: Autonomous Bug Detection & Self-Healing Pipeline
@router.post("/api/v1/self-healing/debug")
@router.post("/self-healing/debug")
async def run_debug_pipeline(req: DebugRequest) -> Dict[str, Any]:
    """Runs autonomous debug pipeline, stack trace analysis, patch generation, and retry loop."""
    res = global_debug_pipeline.run_debug_and_repair_loop(req.project_files, req.max_retries or 3)
    return {"status": "success", "debug_result": res}


# Day 48: AI Project Refactoring Engine
@router.post("/api/v1/refactoring/analyze")
@router.post("/refactoring/analyze")
async def analyze_code_quality(req: RefactoringRequest) -> Dict[str, Any]:
    """Calculates 0-100 Code Quality Score and improvement suggestions."""
    score = global_quality_scorer.evaluate_quality(req.project_files)
    return {"status": "success", "quality_report": score}


@router.post("/api/v1/refactoring/apply")
@router.post("/refactoring/apply")
async def apply_code_refactoring(req: RefactoringRequest) -> Dict[str, Any]:
    """Refactors project code enforcing SOLID, Clean Architecture, DRY, KISS, and Type Safety."""
    res = global_refactoring_agent.refactor_project(req.project_files)
    return {"status": "success", "refactoring": res}


# Day 49: AI Architecture Optimizer
@router.post("/api/v1/architecture/optimize")
@router.post("/architecture/optimize")
async def optimize_architecture(req: ArchitectureRequest) -> Dict[str, Any]:
    """Recommends multi-tier architecture, cloud cost estimation ($/mo), and scalability trade-offs."""
    res = global_architecture_optimizer.optimize_architecture(req.prompt, req.target_users or 10000000)
    return {"status": "success", "architecture": res}


# Day 50: AI Product Manager (Requirement Intelligence)
@router.post("/api/v1/requirements/generate-srs")
@router.post("/requirements/generate-srs")
async def generate_srs(req: SRSRequest) -> Dict[str, Any]:
    """Converts user idea into full SRS, user stories, acceptance criteria, sprint plan, and roadmap."""
    res = global_requirement_agent.analyze_and_generate_srs(req.idea)
    return {"status": "success", "srs": res}


@router.post("/api/v1/requirements/clarify")
@router.post("/requirements/clarify")
async def get_clarification_questions(req: SRSRequest) -> Dict[str, Any]:
    """Generates targeted clarifying questions for ambiguous user prompts."""
    questions = global_clarification_flow.generate_clarifying_questions(req.idea)
    return {"status": "success", "questions": questions}
