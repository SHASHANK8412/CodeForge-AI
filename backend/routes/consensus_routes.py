"""
FastAPI Routes for Day 43 Multi-Model AI Collaboration, Dynamic Routing & Consensus Engine
=============================================================================================
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from backend.services.model_manager import global_model_manager
from backend.services.consensus_engine import global_consensus_engine
from backend.services.benchmark import global_benchmark_tracker

router = APIRouter(tags=["Multi-Model Collaboration & Consensus Engine"])


class ConsensusRequest(BaseModel):
    prompt: str
    task_type: Optional[str] = "General"
    models: Optional[List[str]] = None
    offline_models: Optional[List[str]] = None


class RouteTaskRequest(BaseModel):
    task_type: str


@router.post("/api/v1/consensus/execute")
@router.post("/consensus/execute")
async def execute_consensus_pipeline(req: ConsensusRequest) -> Dict[str, Any]:
    """
    Executes multi-model parallel generation, performs AI cross-voting, ranks candidates, and selects winner.
    """
    # 1. Parallel execution
    candidates = global_model_manager.execute_models_in_parallel(
        prompt=req.prompt,
        models=req.models,
        task_type=req.task_type or "General",
        offline_models=req.offline_models
    )

    # 2. Consensus & Ranking
    consensus_res = global_consensus_engine.evaluate_candidates(
        candidate_outputs=candidates,
        task_type=req.task_type or "General"
    )

    # 3. Benchmark Recording
    winner_name = consensus_res.get("winner_model", "")
    for c in candidates:
        m_name = c["model"]
        is_win = (m_name == winner_name)
        global_benchmark_tracker.record_run(
            model_name=m_name,
            latency=c.get("latency", 2.0),
            tokens_used=c.get("tokens_used", 100),
            quality_score=consensus_res.get("winning_score", 90.0) if is_win else 85.0,
            is_winner=is_win,
            is_error=(c.get("status") != "SUCCESS")
        )

    return {
        "status": "success",
        "candidates": candidates,
        "consensus": consensus_res
    }


@router.get("/api/v1/consensus/benchmark")
@router.get("/consensus/benchmark")
async def get_benchmark_dashboard() -> Dict[str, Any]:
    """
    Retrieves model benchmark statistics, latency, win rates, and quality metrics.
    """
    summary = global_benchmark_tracker.get_dashboard_summary()
    return {"status": "success", "benchmark_summary": summary}


@router.get("/api/v1/consensus/models")
@router.get("/consensus/models")
async def list_models() -> Dict[str, Any]:
    """
    Retrieves registered LLMs and their current online status.
    """
    return {"status": "success", "models": global_model_manager.registry}


@router.post("/api/v1/consensus/route-task")
@router.post("/consensus/route-task")
async def route_task(req: RouteTaskRequest) -> Dict[str, Any]:
    """
    Determines preferred LLM for a given task type with automatic fallback capability.
    """
    best_model = global_model_manager.route_task(req.task_type)
    return {
        "status": "success",
        "task_type": req.task_type,
        "preferred_model": best_model
    }
