import logging
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.models.manager import global_model_manager
from backend.models.router import global_intelligent_router
from backend.models.consensus import global_consensus_engine
from backend.models.benchmark import global_model_benchmarker

logger = logging.getLogger("aiforge.routes.models")

router = APIRouter(tags=["Multi-LLM Intelligence & Routing"])


class RouteRequest(BaseModel):
    task_name: str = Field(min_length=1)
    user_override: Optional[str] = None


class ConsensusRequest(BaseModel):
    prompt: str = Field(min_length=1)
    task_name: str = "architecture"
    models: Optional[List[str]] = None


@router.get("/models")
@router.get("/api/models")
def get_all_models():
    """Lists all registered LLMs, capabilities, and online status."""
    return global_model_manager.discover_models()


@router.get("/models/status")
@router.get("/api/models/status")
def get_models_status():
    """Returns online/offline status and health metrics for installed LLMs."""
    return global_model_manager.check_health()


@router.post("/models/route")
@router.post("/api/models/route")
def route_task_to_model(req: RouteRequest):
    """Routes an agent task to the optimal LLM based on task capability ratings."""
    return global_intelligent_router.route_task(req.task_name, req.user_override)


@router.post("/models/benchmark")
@router.post("/api/models/benchmark")
def benchmark_models(model_id: Optional[str] = None):
    """Measures latency, throughput, and success rate for a specific model or all models."""
    if model_id:
        return global_model_benchmarker.benchmark_model(model_id)
    return global_model_benchmarker.benchmark_all_models()


@router.post("/models/consensus")
@router.post("/api/models/consensus")
def generate_model_consensus(req: ConsensusRequest):
    """Executes multi-model consensus evaluation and selects the highest-scoring output."""
    return global_consensus_engine.generate_consensus(req.prompt, req.task_name, req.models)
