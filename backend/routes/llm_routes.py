"""
FastAPI Routes for Day 34 Multi-LLM Intelligence Engine & Dynamic Model Routing
=================================================================================
Exposes REST APIs for model registry metadata, intelligent routing selection, benchmark execution, fallback testing, and multi-LLM dashboards.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from backend.llm.model_registry import global_model_registry
from backend.llm.model_selector import global_model_selector
from backend.llm.fallback import global_fallback_manager
from backend.llm.evaluator import global_response_evaluator
from backend.llm.benchmark import global_benchmark_engine
from backend.llm.router import global_dynamic_model_router

router = APIRouter(tags=["Multi-LLM Intelligence Engine"])


class ModelSelectInput(BaseModel):
    task_type: Optional[str] = "coding"  # coding, architecture, documentation, reasoning
    prompt: Optional[str] = ""
    ensemble_mode: Optional[bool] = False
    primary_model_override: Optional[str] = None


class RunBenchmarkInput(BaseModel):
    models: Optional[List[str]] = None
    sample_prompt: Optional[str] = "Generate FastAPI REST Endpoint"


class FallbackTestInput(BaseModel):
    primary_model: Optional[str] = "FailingModel"
    prompt: Optional[str] = "Execute code generation task"
    custom_chain: Optional[List[str]] = None


@router.get("/models")
@router.get("/api/v1/models")
async def list_supported_models(capability: Optional[str] = Query(None, description="Filter by capability: code, reasoning")) -> Dict[str, Any]:
    """Retrieves metadata for supported LLMs (Qwen, DeepSeek, Llama, Mistral, Gemma, GPT-4o, Claude)."""
    if capability:
        models = global_model_registry.get_models_by_capability(capability)
    else:
        models = global_model_registry.get_all_models()
    return {"status": "success", "total_models": len(models), "models": models}


@router.post("/models/select")
@router.post("/api/v1/models/select")
async def select_or_route_model(req: ModelSelectInput) -> Dict[str, Any]:
    """Dynamically routes prompt to optimal LLM model or executes Ensemble multi-model mode."""
    try:
        res = global_dynamic_model_router.route_and_generate(
            prompt=req.prompt or "Build application module",
            task_type=req.task_type or "coding",
            ensemble_mode=req.ensemble_mode or False,
            primary_model_override=req.primary_model_override
        )
        return {"status": "success", "routing_result": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/models/benchmark")
@router.post("/api/v1/models/benchmark")
async def run_model_benchmark(req: RunBenchmarkInput) -> Dict[str, Any]:
    """Runs latency, token throughput, cost, and accuracy benchmark on selected LLMs."""
    try:
        report = global_benchmark_engine.run_benchmark(
            model_names=req.models,
            sample_prompt=req.sample_prompt or "Generate FastAPI REST Endpoint"
        )
        return {"status": "success", "benchmark_report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/status")
@router.get("/api/v1/models/status")
async def get_models_status() -> Dict[str, Any]:
    """Retrieves operational status, provider availability, and fallback history."""
    history = global_fallback_manager.get_fallback_history()
    models = global_model_registry.get_all_models()
    return {
        "status": "success",
        "models_count": len(models),
        "all_models_online": True,
        "fallback_history_count": len(history),
        "models": models
    }


@router.post("/models/fallback")
@router.post("/api/v1/models/fallback")
async def test_model_fallback(req: FallbackTestInput) -> Dict[str, Any]:
    """Tests model fallback chain execution when primary model becomes unavailable."""
    try:
        res = global_fallback_manager.execute_with_fallback(
            primary_model=req.primary_model or "FailingModel",
            prompt=req.prompt or "Generate code",
            custom_chain=req.custom_chain
        )
        return {"status": "success", "fallback_result": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/models/dashboard")
@router.get("/api/v1/models/dashboard")
async def get_multi_llm_dashboard() -> Dict[str, Any]:
    """Retrieves Multi-LLM Dashboard metrics: Current Model, Fallback Status, Latency, Success Rate, Model Rankings, Average Cost, Benchmark History."""
    dash = global_dynamic_model_router.get_router_dashboard()
    return {"status": "success", "multi_llm_dashboard": dash}
