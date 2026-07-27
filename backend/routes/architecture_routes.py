"""
FastAPI Routes for Day 37 Autonomous Software Architect & System Design Intelligence
======================================================================================
Exposes REST APIs for system architecture selection, API contracts, database schema designs, scalability capacity planning, risk analysis, C4 diagram generation, and architecture dashboards.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from backend.architecture.analyzer import global_requirement_analyzer
from backend.architecture.designer import global_core_architecture_designer
from backend.architecture.api_designer import global_api_designer
from backend.architecture.database_designer import global_database_designer
from backend.architecture.scalability import global_scalability_planner
from backend.architecture.risk_analyzer import global_risk_analyzer
from backend.architecture.diagrams import global_architecture_diagram_generator

router = APIRouter(tags=["Autonomous Software Architect"])


class DesignArchitectureInput(BaseModel):
    prompt: str
    project_name: Optional[str] = "Project"


@router.post("/architecture/design")
@router.post("/api/v1/architecture/design")
async def generate_architecture_design(req: DesignArchitectureInput) -> Dict[str, Any]:
    """Generates complete system architecture blueprint, API design, database schemas, and scalability plan."""
    try:
        name = req.project_name or "Project"
        req_analysis = global_requirement_analyzer.analyze_requirements(req.prompt, name)
        arch_design = global_core_architecture_designer.select_architecture(req_analysis)
        api_design = global_api_designer.design_apis(name)
        db_design = global_database_designer.design_database(name)
        scaling_plan = global_scalability_planner.plan_scalability(req_analysis["peak_concurrency_target"])
        risks = global_risk_analyzer.analyze_risks(arch_design)
        diagrams = global_architecture_diagram_generator.generate_all_diagrams(name)

        return {
            "status": "success",
            "project_name": name,
            "requirement_analysis": req_analysis,
            "architecture_design": arch_design,
            "api_design": api_design,
            "database_design": db_design,
            "scalability_plan": scaling_plan,
            "risk_analysis": risks,
            "diagrams": diagrams
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/architecture/report")
@router.get("/api/v1/architecture/report")
async def get_architecture_report(project_name: Optional[str] = Query("Project", description="Target project name")) -> Dict[str, Any]:
    """Retrieves full executive architecture report."""
    name = project_name or "Project"
    req_analysis = global_requirement_analyzer.analyze_requirements("10 million users e-commerce app", name)
    arch_design = global_core_architecture_designer.select_architecture(req_analysis)
    return {"status": "success", "architecture_report": arch_design}


@router.get("/architecture/diagram")
@router.get("/api/v1/architecture/diagram")
async def get_architecture_diagrams(project_name: Optional[str] = Query("Project", description="Target project name")) -> Dict[str, Any]:
    """Retrieves C4 Context, Container, Sequence, and ER Mermaid diagrams."""
    diagrams = global_architecture_diagram_generator.generate_all_diagrams(project_name or "Project")
    return {"status": "success", "diagrams": diagrams}


@router.get("/architecture/risks")
@router.get("/api/v1/architecture/risks")
async def get_architecture_risks() -> Dict[str, Any]:
    """Retrieves single points of failure and bottleneck risk analysis."""
    arch_design = global_core_architecture_designer.select_architecture({"expected_users": "10 Million Users", "peak_concurrency_target": 10000})
    risks = global_risk_analyzer.analyze_risks(arch_design)
    return {"status": "success", "risk_analysis": risks}


@router.get("/architecture/scaling")
@router.get("/api/v1/architecture/scaling")
async def get_scalability_plan(concurrency: Optional[int] = Query(5000, description="Peak concurrent users target")) -> Dict[str, Any]:
    """Retrieves capacity planning estimates for CPU, RAM, storage, and load balancing."""
    plan = global_scalability_planner.plan_scalability(concurrency or 5000)
    return {"status": "success", "scalability_plan": plan}


@router.get("/architecture/dashboard")
@router.get("/api/v1/architecture/dashboard")
async def get_architecture_dashboard() -> Dict[str, Any]:
    """Retrieves Architecture Dashboard data: Overview, Service Map, API Map, DB Design, Infra Estimate, Risk Score, Diagrams."""
    name = "Food Delivery Platform"
    req_analysis = global_requirement_analyzer.analyze_requirements("10M Users food delivery app", name)
    arch_design = global_core_architecture_designer.select_architecture(req_analysis)
    api_design = global_api_designer.design_apis(name)
    db_design = global_database_designer.design_database(name)
    scaling = global_scalability_planner.plan_scalability(5000)
    risks = global_risk_analyzer.analyze_risks(arch_design)
    diagrams = global_architecture_diagram_generator.generate_all_diagrams(name)

    return {
        "status": "success",
        "architecture_dashboard": {
            "project_name": name,
            "architecture_overview": arch_design,
            "service_map": arch_design["recommended_components"],
            "api_map": api_design["endpoints"],
            "database_design": db_design,
            "infrastructure_estimate": arch_design["estimated_infrastructure"],
            "risk_score": risks["overall_risk_score"],
            "diagrams": diagrams
        }
    }
