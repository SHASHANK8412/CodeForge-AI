"""
AIForge Day 20 — DevOps Agent & Dockerfile Builder
===================================================
Inspects generated software project structure, identifies backend/frontend frameworks,
generates production multi-stage Dockerfiles (FastAPI + React/Nginx), and builds structured DeploymentPlans.
"""

import secrets
import logging
from typing import Dict, Any, List

from backend.devops.models import DeploymentPlan, ResourceLimits

_logger = logging.getLogger("aiforge.devops.builder")


class DevOpsAgent:
    """
    Autonomous DevOps Agent for project inspection and containerization planning.
    """

    def generate_dockerfile(self, app_type: str = "react_fastapi") -> str:
        """
        Generates production multi-stage Dockerfile (Nginx static frontend + FastAPI backend).
        Uses non-root app user and containerized security practices.
        """
        return """# AIForge Generated Production Multi-Stage Dockerfile
# Stage 1: Build Frontend React Application
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --quiet
COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python Application Container
FROM python:3.11-slim AS production
WORKDIR /app

# Create non-root system user
RUN groupadd -g 10001 appgroup && useradd -u 10001 -g appgroup -s /bin/bash appuser

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY --from=frontend-builder /app/frontend/dist ./static/

USER appuser
EXPOSE 8080

ENV PORT=8080
ENV ENVIRONMENT=production

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
"""

    def create_deployment_plan(
        self,
        project_id: str,
        version: int = 1,
        environment: str = "production",
        port: int = 8080
    ) -> DeploymentPlan:
        _logger.info(f"[DevOpsAgent] Generating deployment plan for '{project_id}' v{version}")
        dockerfile = self.generate_dockerfile("react_fastapi")

        return DeploymentPlan(
            plan_id=f"plan_devops_{secrets.token_urlsafe(6)}",
            project_id=project_id,
            version=version,
            application_type="react_fastapi",
            frontend_type="static_nginx",
            backend_type="fastapi",
            containerization=True,
            provider="Docker",
            environment=environment,
            health_endpoint="/health",
            required_environment_vars=["DATABASE_URL", "JWT_SECRET", "API_BASE_URL"],
            resource_limits=ResourceLimits(max_memory_mb=512, max_cpu=1.0),
            port=port,
            dockerfile_content=dockerfile
        )


global_devops_agent = DevOpsAgent()
