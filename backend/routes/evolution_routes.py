"""
FastAPI Routes for Day 74-75 Autonomous Code Evolution Engine
=============================================================
Exposes REST endpoints for impact analysis, migration planning, code evolution execution,
selective test runs, and rollback plans.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from backend.evolution.migration import global_evolution_engine

router = APIRouter(prefix="/api/v1/evolution", tags=["Autonomous Code Evolution Engine"])


class ImpactRequest(BaseModel):
    proposed_change: str
    target_symbol: Optional[str] = ""


class EvolutionRequest(BaseModel):
    proposed_evolution: str
    target_symbol: Optional[str] = ""


@router.post("/impact")
async def evaluate_evolution_impact(req: ImpactRequest) -> Dict[str, Any]:
    """Calculates downstream impact, affected files, and risk scores before code modification."""
    try:
        impact = global_evolution_engine.impact_analyzer.evaluate_impact(req.proposed_change, req.target_symbol)
        return {"status": "success", "impact": impact}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute")
async def execute_code_evolution(req: EvolutionRequest) -> Dict[str, Any]:
    """Executes complete Code Evolution pipeline: Impact -> Plan -> Patches -> Rollback -> Selective Tests -> Docs."""
    try:
        res = global_evolution_engine.evolve_codebase(req.proposed_evolution, req.target_symbol)
        return {"status": "success", "result": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
