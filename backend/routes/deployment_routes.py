"""
FastAPI Routes for Day 33 Autonomous CI/CD Pipeline & Production Release Management
=====================================================================================
Exposes REST APIs for CI/CD pipeline triggers, build tracking, Docker packaging metadata, multi-strategy deployments, health monitoring, automated rollbacks, semantic versioning, release notes, and deployment dashboards.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from backend.deployment.pipeline import global_ci_pipeline_engine
from backend.deployment.build_manager import global_build_manager
from backend.deployment.version_manager import global_version_manager
from backend.deployment.deployment_manager import global_deployment_manager, DeploymentStrategy
from backend.deployment.health_checker import global_health_checker
from backend.deployment.rollback_manager import global_rollback_manager
from backend.deployment.release_notes import global_release_notes_generator

router = APIRouter(tags=["Autonomous CI/CD & Production Release"])


class PipelineStartInput(BaseModel):
    branch: Optional[str] = "main"
    commit_hash: Optional[str] = "a1b2c3d"


class DeployInput(BaseModel):
    environment: Optional[str] = "Production"
    strategy: Optional[str] = DeploymentStrategy.ROLLING  # Rolling, Blue-Green, Canary
    version: Optional[str] = None


class RollbackInput(BaseModel):
    reason: Optional[str] = "Health Check Failure"
    failed_version: Optional[str] = None
    target_version: Optional[str] = None


class VersionBumpInput(BaseModel):
    release_type: Optional[str] = "patch"  # major, minor, patch


class GenerateReleaseNotesInput(BaseModel):
    version: Optional[str] = None
    features: Optional[List[str]] = None
    fixes: Optional[List[str]] = None
    performance: Optional[List[str]] = None
    security: Optional[List[str]] = None


@router.post("/pipeline/start")
@router.post("/api/v1/pipeline/start")
async def start_ci_pipeline(req: PipelineStartInput) -> Dict[str, Any]:
    """Triggers the 10-stage autonomous CI/CD pipeline."""
    try:
        pipe = global_ci_pipeline_engine.start_pipeline(branch=req.branch or "main", commit_hash=req.commit_hash or "a1b2c3d")
        
        # Record build entry
        global_build_manager.record_build(
            branch=req.branch or "main",
            status=pipe["status"],
            duration=pipe["duration"],
            commit_hash=req.commit_hash or "a1b2c3d"
        )

        return {"status": "success", "pipeline": pipe}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pipeline/status")
@router.get("/api/v1/pipeline/status")
async def get_ci_pipeline_status() -> Dict[str, Any]:
    """Retrieves live CI/CD pipeline stage execution status and logs."""
    pipe = global_ci_pipeline_engine.get_pipeline_status()
    return {"status": "success", "pipeline_status": pipe}


@router.get("/builds")
@router.get("/api/v1/builds")
async def list_all_builds() -> Dict[str, Any]:
    """Retrieves build history, artifact metadata, and commit hashes."""
    builds = global_build_manager.get_all_builds()
    return {"status": "success", "total_builds": len(builds), "builds": builds}


@router.post("/deploy")
@router.post("/api/v1/deploy")
async def deploy_production_release(req: DeployInput) -> Dict[str, Any]:
    """Executes multi-strategy deployment (Rolling, Blue-Green, Canary)."""
    try:
        deploy = global_deployment_manager.execute_deployment(
            environment=req.environment or "Production",
            strategy=req.strategy or DeploymentStrategy.ROLLING,
            version=req.version
        )
        return {"status": "success", "deployment": deploy}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rollback")
@router.post("/api/v1/rollback")
async def rollback_deployment(req: RollbackInput) -> Dict[str, Any]:
    """Rolls back failed deployment and restores previous stable release version."""
    try:
        rb = global_rollback_manager.trigger_rollback(
            reason=req.reason or "Health Check Failure",
            failed_version=req.failed_version,
            target_version=req.target_version
        )
        return {"status": "success", "rollback_result": rb}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/health")
@router.get("/api/v1/health/check")
async def perform_health_check(fail_simulation: bool = False) -> Dict[str, Any]:
    """Performs post-deployment health check on API, DB, Auth, Frontend, CPU/RAM, response time, and error rate."""
    report = global_health_checker.perform_health_check(fail_simulation=fail_simulation)
    return {"status": "success", "health_report": report}


@router.get("/release-notes")
@router.get("/api/v1/release-notes")
async def get_release_notes(version: Optional[str] = Query(None, description="Release version string (e.g. v2.1.0)")) -> Dict[str, Any]:
    """Retrieves structured release notes summary for a version."""
    notes = global_release_notes_generator.get_release_notes(version=version)
    return {"status": "success", "release_notes": notes}


@router.post("/release-notes/generate")
async def generate_release_notes(req: GenerateReleaseNotesInput) -> Dict[str, Any]:
    """Generates and logs semantic release notes."""
    notes = global_release_notes_generator.generate_release_notes(
        version=req.version,
        features=req.features,
        fixes=req.fixes,
        performance=req.performance,
        security=req.security
    )
    return {"status": "success", "release_notes": notes}


@router.get("/versions")
@router.get("/api/v1/versions")
async def list_versions() -> Dict[str, Any]:
    """Retrieves semantic version history and current release tag."""
    curr = global_version_manager.get_current_version()
    history = global_version_manager.get_version_history()
    return {"status": "success", "current_version": curr, "version_history": history}


@router.post("/versions/increment")
async def increment_version(req: VersionBumpInput) -> Dict[str, Any]:
    """Increments semantic version (Major, Minor, Patch)."""
    res = global_version_manager.increment_version(release_type=req.release_type or "patch")
    return {"status": "success", "new_version": res}


@router.get("/deployment/dashboard")
@router.get("/api/v1/deployment/dashboard")
async def get_deployment_dashboard() -> Dict[str, Any]:
    """Retrieves Monitoring Dashboard data: Current Version, Pipeline Status, Deployment Progress, Health Status, Rollback History, Release Notes, Build History, Active Environment."""
    curr_v = global_version_manager.get_current_version()
    pipe_status = global_ci_pipeline_engine.get_pipeline_status()
    builds = global_build_manager.get_all_builds()[:5]
    deployments = global_deployment_manager.get_all_deployments()[:5]
    health = global_health_checker.perform_health_check()
    rollbacks = global_rollback_manager.get_rollback_history()
    notes = global_release_notes_generator.get_release_notes(curr_v)

    return {
        "status": "success",
        "deployment_dashboard": {
            "current_version": curr_v,
            "pipeline_status": pipe_status,
            "health_status": health,
            "active_environment": "Production",
            "recent_deployments": deployments,
            "rollback_history": rollbacks,
            "build_history": builds,
            "latest_release_notes": notes
        }
    }
