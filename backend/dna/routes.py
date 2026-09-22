"""
AIForge Day 15 — Engineering DNA REST API Routes
=================================================
Endpoints for:
- GET  /api/dna/{projectId}/graph
- POST /api/projects/{projectId}/impact-analysis
- GET  /api/dna/{projectId}/requirements-trace
- GET  /api/dna/{projectId}/dead-code
- GET  /api/dna/{projectId}/circular-dependencies
- GET  /api/dna/{projectId}/diff?v1=1&v2=2
- POST /api/dna/{projectId}/explain-node
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user
from backend.dna.service import global_dna_service
from backend.dna.repository import global_graph_repository
from backend.dna.impact import global_impact_engine

dna_router = APIRouter(tags=["Engineering DNA"])


class ImpactPayload(BaseModel):
    node_id: str
    change_type: str = "modify"


class ExplainPayload(BaseModel):
    node_id: str


@dna_router.get("/api/dna/{project_id}/graph")
async def get_project_dna_graph(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    graph = global_dna_service.get_or_build_graph(project_id)
    if not graph:
        return {"status": "unavailable", "message": "Engineering DNA analysis unavailable."}
    return {"status": "success", "graph": graph.model_dump()}


@dna_router.post("/api/projects/{project_id}/impact-analysis")
async def analyze_project_impact(
    project_id: str,
    payload: ImpactPayload,
    user: dict = Depends(get_current_user)
):
    res = global_dna_service.analyze_impact(project_id, payload.node_id, payload.change_type)
    return {"status": "success", "impact": res.model_dump()}


@dna_router.get("/api/dna/{project_id}/requirements-trace")
async def trace_project_requirements(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    global_dna_service.get_or_build_graph(project_id)
    traces = global_impact_engine.trace_requirements(project_id)
    return {"status": "success", "traces": [t.model_dump() for t in traces]}


@dna_router.get("/api/dna/{project_id}/dead-code")
async def get_dead_code_findings(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    global_dna_service.get_or_build_graph(project_id)
    dead = global_impact_engine.detect_dead_code(project_id)
    return {"status": "success", "dead_code": [d.model_dump() for d in dead]}


@dna_router.get("/api/dna/{project_id}/circular-dependencies")
async def get_circular_dependencies(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    global_dna_service.get_or_build_graph(project_id)
    cycles = global_impact_engine.detect_circular_dependencies(project_id)
    return {"status": "success", "circular_dependencies": [c.model_dump() for c in cycles]}


@dna_router.get("/api/dna/{project_id}/diff")
async def get_graph_diff(
    project_id: str,
    v1: int = Query(1),
    v2: int = Query(2),
    user: dict = Depends(get_current_user)
):
    diff = global_graph_repository.diff_graphs(project_id, v1, v2)
    return {"status": "success", "diff": diff.model_dump()}


@dna_router.post("/api/dna/{project_id}/explain-node")
async def explain_graph_node(
    project_id: str,
    payload: ExplainPayload,
    user: dict = Depends(get_current_user)
):
    global_dna_service.get_or_build_graph(project_id)
    explanation = global_impact_engine.explain_node(project_id, payload.node_id)
    return {"status": "success", "explanation": explanation}
