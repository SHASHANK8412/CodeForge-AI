import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from backend.graph.executor import global_workflow_executor
from backend.deployment.exporter import global_deployment_exporter
from backend.deployment.validator import global_deployment_validator

logger = logging.getLogger("aiforge.routes.deployment")

router = APIRouter(tags=["Autonomous DevOps & Deployment"])


@router.get("/deployment/files/{project_id}")
@router.get("/api/deployment/files/{project_id}")
def get_deployment_files(project_id: str):
    """Returns generated DevOps deployment files for a project."""
    status = global_workflow_executor.get_project_status(project_id)
    project_name = status.get("project_id", project_id)
    bundle = global_deployment_exporter.generate_deployment_bundle(project_name)
    bundle["project_id"] = project_id
    return bundle


@router.post("/deployment/generate/{project_id}")
@router.post("/api/deployment/generate/{project_id}")
def generate_deployment_config(project_id: str):
    """Triggers generation of Docker, Compose, K8s, CI/CD, and Nginx deployment manifests."""
    bundle = global_deployment_exporter.generate_deployment_bundle(f"Project_{project_id}")
    return {
        "status": "success",
        "project_id": project_id,
        "message": "Deployment bundle generated successfully.",
        "readiness_score": bundle["validation"]["readiness_score"],
        "total_files": bundle["total_deployment_files"],
        "files": bundle["files"]
    }


@router.get("/deployment/report/{project_id}")
@router.get("/api/deployment/report/{project_id}")
def get_deployment_report(project_id: str):
    """Returns deployment readiness score, validation checks, and missing environment variables."""
    bundle = global_deployment_exporter.generate_deployment_bundle(f"Project_{project_id}")
    val = bundle["validation"]
    return {
        "project_id": project_id,
        "readiness_score": val["readiness_score"],
        "is_ready": val["is_ready"],
        "checks": val["checks"],
        "errors": val["errors"],
        "warnings": val["warnings"],
        "required_env_vars": [
            "DATABASE_URL",
            "REDIS_URL",
            "SECRET_KEY",
            "JWT_SECRET"
        ]
    }
