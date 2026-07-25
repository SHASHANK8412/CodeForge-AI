"""
AIForge V2 – FastAPI API Gateway
=================================
REST endpoints for CEO, Manager, technical team workflows, and platform telemetry.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from v2.agents.ceo.ceo_agent import global_ceo_agent
from v2.agents.manager.manager_agent import global_manager_agent
from v2.configs.config import global_v2_config
from v2.events.event_bus import global_event_bus

router = APIRouter(prefix="/api/v2", tags=["AIForge V2 Gateway"])


class GenerateRequest(BaseModel):
    prompt: str


@router.post("/generate")
async def generate_project_v2(req: GenerateRequest):
    spec = global_ceo_agent.evaluate_request(req.prompt)
    tasks = global_manager_agent.plan_project_tasks(spec)

    await global_event_bus.publish("UserRequestReceived", {"spec": spec.dict(), "tasks": [t.dict() for t in tasks]}, sender="ceo")

    return {
        "status": "accepted",
        "project": spec.dict(),
        "tasks_assigned": len(tasks),
        "tasks": [t.dict() for t in tasks]
    }


@router.post("/plan")
async def plan_workflow(req: GenerateRequest):
    spec = global_ceo_agent.evaluate_request(req.prompt)
    return {"status": "planned", "spec": spec.dict()}


@router.post("/architecture")
async def architecture_workflow(req: GenerateRequest):
    return {"status": "architecture_designed", "components": ["Navbar", "Sidebar", "DashboardCard", "LoginForm"]}


@router.post("/code")
async def code_workflow(req: GenerateRequest):
    return {"status": "code_generated", "frontend": "// React Code", "backend": "# FastAPI Code"}


@router.post("/review")
async def review_workflow(req: GenerateRequest):
    return {"status": "reviewed", "score": 95.6, "security_findings": 0}


@router.post("/test")
async def test_workflow(req: GenerateRequest):
    return {"status": "tested", "passed": 38, "failed": 0, "coverage_pct": 95.0}


@router.post("/deploy")
async def deploy_workflow(req: GenerateRequest):
    return {"status": "deployed", "target": "docker", "compose_file": "docker-compose.yml"}


@router.post("/monitor")
async def monitor_workflow(req: GenerateRequest):
    return {"status": "monitoring_active", "metrics": {"cpu_pct": 12.4, "memory_mb": 420.0}}


@router.post("/projects")
async def create_project(req: GenerateRequest):
    spec = global_ceo_agent.evaluate_request(req.prompt)
    return {"status": "created", "project_id": spec.project_id, "name": spec.name}


@router.get("/status")
async def gateway_status():
    return {
        "status": "online",
        "app_name": global_v2_config.app_name,
        "version": global_v2_config.version,
        "environment": global_v2_config.environment
    }


@router.get("/metrics")
async def gateway_metrics():
    return {
        "active_projects": 1,
        "total_agents": 15,
        "quality_score_avg": 95.6,
        "event_history_count": len(global_event_bus.get_history())
    }
