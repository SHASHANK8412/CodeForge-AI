"""
FastAPI Routes for Autonomous Code Evolution & Benchmarking Engine
===================================================================
Exposes REST endpoints for impact analysis, migration planning, benchmark reporting,
knowledge graphs, and pattern store retrieval.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional

from backend.evolution.migration import global_evolution_engine
from backend.learning.benchmark import global_benchmark_engine
from backend.learning.knowledge_graph import global_knowledge_graph_engine
from backend.learning.pattern_store import global_pattern_store_engine

router = APIRouter(prefix="/api/v1/evolution", tags=["Autonomous Code Evolution Engine"])


class ImpactRequest(BaseModel):
    proposed_change: str
    target_symbol: Optional[str] = ""


class EvolutionRequest(BaseModel):
    proposed_evolution: str
    target_symbol: Optional[str] = ""


@router.post("/impact")
async def evaluate_evolution_impact(req: ImpactRequest) -> Dict[str, Any]:
    try:
        impact = global_evolution_engine.impact_analyzer.evaluate_impact(req.proposed_change, req.target_symbol)
        return {"status": "success", "impact": impact}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute")
async def execute_code_evolution(req: EvolutionRequest) -> Dict[str, Any]:
    try:
        res = global_evolution_engine.evolve_codebase(req.proposed_evolution, req.target_symbol)
        return {"status": "success", "result": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/benchmark")
def get_evolution_benchmark(project_name: str = Query(default="Current App")):
    return global_benchmark_engine.benchmark_project(project_name)


@router.get("/graph")
def get_knowledge_graph():
    return global_knowledge_graph_engine.build_system_knowledge_graph()


@router.get("/patterns")
def get_pattern_store():
    return global_pattern_store_engine.get_all_patterns()
