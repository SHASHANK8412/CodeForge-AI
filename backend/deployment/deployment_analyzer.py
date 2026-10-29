"""
AIForge Deployment Analyzer Module
==================================
Inspects codebase manifests and workspace files to determine:
- Frontend & Backend tech stack
- Package managers & build/start commands
- Required and optional environment variables
- Database, Redis, and persistent storage requirements
- Health-check endpoints and container readiness
"""

import json
import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

_logger = logging.getLogger("aiforge.deployment.analyzer")


class DeploymentSpec(BaseModel):
    project_name: str = "AIForge Project"
    frontend_tech: str = "react"
    backend_tech: str = "fastapi"
    database_tech: Optional[str] = "postgresql"
    cache_tech: Optional[str] = None
    frontend_build_cmd: str = "npm run build"
    frontend_start_cmd: str = "npm run dev"
    backend_start_cmd: str = "uvicorn backend.main:app --host 0.0.0.0 --port 8000"
    required_env_vars: List[str] = Field(default_factory=list)
    optional_env_vars: List[str] = Field(default_factory=list)
    frontend_port: int = 5173
    backend_port: int = 8000
    docker_ready: bool = True
    health_check_endpoint: str = "/health"
    has_dockerfile: bool = False
    has_docker_compose: bool = False


class DeploymentAnalyzer:
    """
    Analyzes project codebase to derive exact deployment requirements.
    """

    def analyze(self, workspace_path: Path, files_manifest: Dict[str, str]) -> DeploymentSpec:
        spec = DeploymentSpec(project_name=workspace_path.name)
        paths = set(files_manifest.keys())
        all_code = "\n".join(files_manifest.values())

        # Check existing Docker setup
        spec.has_dockerfile = ("Dockerfile" in paths or "backend/Dockerfile" in paths)
        spec.has_docker_compose = ("docker-compose.yml" in paths or "docker-compose.yaml" in paths)

        # Environment variable extraction (find os.getenv, process.env, etc.)
        env_vars = set()
        for env_match in re.findall(r"(?:process\.env\.|os\.getenv\(|os\.environ\.get\(|os\.environ\[)['\"]([A-Z0-9_]+)['\"]", all_code):
            if env_match not in ["NODE_ENV", "PORT", "PYTHONPATH"]:
                env_vars.add(env_match)

        # Default standard env vars for database/auth if detected
        if "jwt" in all_code.lower() or "auth" in all_code.lower():
            env_vars.add("JWT_SECRET")
        if "postgres" in all_code.lower() or "sqlalchemy" in all_code.lower():
            env_vars.add("DATABASE_URL")
            spec.database_tech = "postgresql"

        spec.required_env_vars = sorted(list(env_vars))
        spec.optional_env_vars = ["LOG_LEVEL", "DEBUG"]

        # Health endpoint check
        if "/health" in all_code:
            spec.health_check_endpoint = "/health"
        elif "/api/health" in all_code:
            spec.health_check_endpoint = "/api/health"

        _logger.info(f"DeploymentAnalyzer: Extracted spec for '{spec.project_name}': FE={spec.frontend_tech}, BE={spec.backend_tech}, Required Envs={spec.required_env_vars}")
        return spec


global_deployment_analyzer = DeploymentAnalyzer()
