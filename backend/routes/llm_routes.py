"""
FastAPI Routes for Day 71 Multi-LLM Collaboration Router
=========================================================
Exposes REST endpoints for model routing, parallel execution, memory stats, and benchmarks.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from backend.llm.model_registry import MODELS
from backend.llm.model_router import global_model_router

router = APIRouter(prefix="/api/v1/llm", tags=["Multi-LLM Collaboration"])

class LLMRequest(BaseModel):
    task: str
    strategy: Optional[str] = "auto"

@router.get("/models")
async def get_registered_models() -> Dict[str, Any]:
    """Returns all registered local and cloud models."""
    return {"status": "success", "models": MODELS}

@router.post("/generate")
async def generate_with_llm(req: LLMRequest) -> Dict[str, Any]:
    """Routes and executes prompt using selected strategy (auto, fast, cheap, accurate, parallel, benchmark)."""
    try:
        result = await global_model_router.route_and_execute(req.task, strategy=req.strategy)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memory")
async def get_model_memory() -> Dict[str, Any]:
    """Returns historical performance memory and preferred model rankings per task."""
    return {"status": "success", "memory": global_model_router.memory.get_all_memory()}

@router.get("/dashboard")
async def get_llm_dashboard() -> Dict[str, Any]:
    """Returns telemetry data for dashboard display."""
    memory_data = global_model_router.memory.get_all_memory()
    history = memory_data.get("history", [])
    avg_latency = sum(h.get("latency", 0) for h in history) / len(history) if history else 1.7
    avg_quality = sum(h.get("quality_score", 0) for h in history) / len(history) if history else 92.0

    return {
        "status": "success",
        "current_preferred_coding": memory_data.get("coding", {}).get("preferred", "deepseek"),
        "average_latency_seconds": round(avg_latency, 2),
        "average_quality_score": round(avg_quality, 1),
        "registered_models_count": len(MODELS),
        "total_executions": len(history)
    }
