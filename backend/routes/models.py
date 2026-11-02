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


@router.get("/api/models/installed")
def get_installed_models():
    """
    The Ollama models actually installed on this machine, and which one the generation
    pipeline will use for planning and for writing code.
    """
    from backend.models.model_router import discover_installed_models, global_model_router

    try:
        from ollama import Client
        listing = Client(timeout=5.0).list()
        entries = listing.get("models", []) if isinstance(listing, dict) else getattr(listing, "models", [])
        names = []
        for m in entries:
            name = m.get("model") or m.get("name") if isinstance(m, dict) else getattr(m, "model", None)
            if name and not any(k in name.lower() for k in ("embed", "minilm", "bge", "bert")):
                names.append(name)
        online = True
    except Exception as e:
        logger.info("Ollama is not reachable: %s", e)
        names, online = [], False

    if not online or not names:
        return {"ollama_online": online, "models": names, "planning_model": None, "coding_model": None}

    discover_installed_models(force_refresh=True)
    planning = global_model_router.select("PROJECT_GENERATION", agent_name="project_planner")
    coding = global_model_router.select("PROJECT_GENERATION", agent_name="project_backend")
    return {
        "ollama_online": True,
        "models": names,
        "planning_model": planning.selected_model,
        "coding_model": coding.selected_model,
    }


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
