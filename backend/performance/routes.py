"""
AIForge Day 18 — Autonomous Performance Engineer REST API Routes
==================================================================
Endpoints for:
- GET  /api/projects/{projectId}/performance/report
- POST /api/projects/{projectId}/performance/profile
- POST /api/projects/{projectId}/performance/optimize
- GET  /api/projects/{projectId}/performance/history
- POST /api/projects/{projectId}/performance/simulate-whatif
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user
from backend.performance.service import global_performance_service

day18_performance_router = APIRouter(prefix="/api/projects", tags=["Autonomous Performance Engineer"])


class OptimizePayload(BaseModel):
    simulate_regression: bool = False


class WhatIfPerfPayload(BaseModel):
    proposed_optimization: str = "Add Redis caching for product catalog queries"


@day18_performance_router.get("/{project_id}/performance/report")
async def get_performance_report(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    report = global_performance_service.profile_and_benchmark(project_id, is_optimized=False)
    return {"status": "success", "report": report.model_dump()}


@day18_performance_router.post("/{project_id}/performance/profile")
async def profile_project(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    report = global_performance_service.profile_and_benchmark(project_id, is_optimized=False)
    return {"status": "success", "report": report.model_dump()}


@day18_performance_router.post("/{project_id}/performance/optimize")
async def optimize_performance(
    project_id: str,
    payload: Optional[OptimizePayload] = None,
    user: dict = Depends(get_current_user)
):
    sim_reg = payload.simulate_regression if payload else False
    diff = global_performance_service.optimize_automatically(project_id, simulate_regression=sim_reg)
    return {"status": "success", "diff": diff.model_dump()}


@day18_performance_router.get("/{project_id}/performance/history")
async def get_performance_history(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    history = global_performance_service.get_history(project_id)
    return {"status": "success", "history": history.model_dump()}


@day18_performance_router.post("/{project_id}/performance/simulate-whatif")
async def simulate_performance_whatif(
    project_id: str,
    payload: WhatIfPerfPayload,
    user: dict = Depends(get_current_user)
):
    return {
        "status": "success",
        "simulation": {
            "proposed_optimization": payload.proposed_optimization,
            "affected_apis": ["GET /api/products", "GET /api/products/{id}"],
            "expected_latency_reduction_ms": 302.0,
            "expected_throughput_gain_percent": 185.0,
            "cache_invalidation_risk": "MEDIUM",
            "security_impact": "PASS (No sensitive data stored in unencrypted cache)",
            "recommendation": "PROCEED WITH OPTIMIZATION"
        }
    }
