"""
AIForge V2 — Extraordinary Features REST API Routes
===================================================
Endpoints for What-If Simulator, DNA Graph, Bug Bounty, Multi-Agent Debate,
Software Assistant, and Production Readiness CTO Gate.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.auth.dependencies import get_current_user
from backend.intelligence.models import SimulationRequest, ImpactQueryRequest, SoftwareAssistantQuery
from backend.intelligence.simulator import global_whatif_simulator
from backend.intelligence.dna_graph import global_dna_graph_engine
from backend.intelligence.bug_hunter import global_security_hunter_agent
from backend.intelligence.debate_engine import global_debate_engine
from backend.intelligence.software_assistant import global_software_assistant_engine
from backend.intelligence.cto_gate import global_cto_gate

sim_router = APIRouter(prefix="/api/simulator", tags=["What-If Engineering Simulator"])
dna_router = APIRouter(prefix="/api/dna", tags=["AI Engineering DNA Graph"])
bug_router = APIRouter(prefix="/api/bug-bounty", tags=["Autonomous Bug Bounty"])
debate_router = APIRouter(prefix="/api/debate", tags=["Multi-Agent Debate Arena"])
talk_router = APIRouter(prefix="/api/software-assistant", tags=["Talk to Your Software"])
cto_router = APIRouter(prefix="/api/production-gate", tags=["Production Readiness CTO Gate"])


# 1. What-If Simulator
@sim_router.post("/simulate")
async def run_simulation(req: SimulationRequest, user: dict = Depends(get_current_user)):
    res = global_whatif_simulator.simulate(req.project_id, req.proposed_change)
    return {"status": "success", "simulation": res.model_dump()}


# 2. AI Engineering DNA Graph
@dna_router.get("/{project_id}/graph")
async def get_dna_graph(project_id: str, user: dict = Depends(get_current_user)):
    graph = global_dna_graph_engine.get_graph(project_id)
    return {"status": "success", "graph": graph.model_dump()}


@dna_router.post("/impact")
async def query_dna_impact(req: ImpactQueryRequest, user: dict = Depends(get_current_user)):
    res = global_dna_graph_engine.analyze_impact(req.project_id, req.target_node_or_component)
    return {"status": "success", **res}


# 3. Autonomous Bug Bounty
@bug_router.post("/scan")
async def scan_security(project_id: str = Query("aiforge-demo"), user: dict = Depends(get_current_user)):
    report = global_security_hunter_agent.scan_and_repair(project_id)
    return {"status": "success", "report": report.model_dump()}


@bug_router.get("/{project_id}/report")
async def get_security_report(project_id: str, user: dict = Depends(get_current_user)):
    report = global_security_hunter_agent.scan_and_repair(project_id)
    return {"status": "success", "report": report.model_dump()}


# 4. Multi-Agent Debate Arena
@debate_router.post("/start")
async def start_debate(generation_id: str = Query("aiforge-demo"), prompt: str = Query("FastAPI e-commerce architecture"), user: dict = Depends(get_current_user)):
    verdict = global_debate_engine.run_debate(generation_id, prompt)
    return {"status": "success", "verdict": verdict.model_dump()}


@debate_router.get("/{generation_id}")
async def get_debate_verdict(generation_id: str, user: dict = Depends(get_current_user)):
    verdict = global_debate_engine.run_debate(generation_id, "Standard Project Architecture")
    return {"status": "success", "verdict": verdict.model_dump()}


# 5. Talk to Your Software Assistant
@talk_router.post("/chat")
async def chat_software(req: SoftwareAssistantQuery, user: dict = Depends(get_current_user)):
    res = global_software_assistant_engine.answer_query(req.project_id, req.query)
    return {"status": "success", "response": res.model_dump()}


# 6. Production Readiness CTO Gate
@cto_router.get("/{project_id}")
async def get_cto_gate_report(project_id: str, user: dict = Depends(get_current_user)):
    report = global_cto_gate.evaluate(project_id)
    return {"status": "success", "report": report.model_dump()}


@cto_router.post("/{project_id}/override")
async def override_cto_gate(project_id: str, user: dict = Depends(get_current_user)):
    report = global_cto_gate.override_or_fix(project_id)
    return {"status": "success", "report": report.model_dump()}
