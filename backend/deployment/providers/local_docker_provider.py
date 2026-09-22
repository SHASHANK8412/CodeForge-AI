"""
AIForge Local Docker Deployment Provider
=======================================
Implements local containerized deployment via Docker / Docker Compose or fallback process trees.
"""

import sys
import shutil
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

from backend.deployment.providers.base_provider import DeploymentProvider, ProviderDeploymentResult
from backend.execution.process_manager import global_process_manager
from backend.execution.port_manager import global_port_manager

_logger = logging.getLogger("aiforge.deployment.providers.local_docker")


class LocalDockerProvider(DeploymentProvider):
    """
    Local Docker & Docker Compose Deployment Provider.
    """

    def validate(self, project_path: Path, manifest: Dict[str, str]) -> bool:
        return project_path.exists()

    def generate_dockerfile_if_missing(self, project_path: Path, manifest: Dict[str, str]):
        df_path = project_path / "Dockerfile"
        if not df_path.exists() and "Dockerfile" not in manifest:
            df_content = (
                "FROM python:3.11-slim\n"
                "WORKDIR /app\n"
                "COPY backend/requirements.txt .\n"
                "RUN pip install --no-cache-dir -r requirements.txt\n"
                "COPY backend /app/backend\n"
                "EXPOSE 8000\n"
                "CMD [\"uvicorn\", \"backend.main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]\n"
            )
            try:
                df_path.write_text(df_content, encoding="utf-8")
            except Exception:
                pass

    def generate_compose_if_missing(self, project_path: Path, manifest: Dict[str, str]):
        dc_path = project_path / "docker-compose.yml"
        if not dc_path.exists() and "docker-compose.yml" not in manifest:
            dc_content = (
                "version: '3.8'\n"
                "services:\n"
                "  backend:\n"
                "    build: .\n"
                "    ports:\n"
                "      - '8000:8000'\n"
                "    environment:\n"
                "      - DATABASE_URL=postgresql://user:pass@db:5432/appdb\n"
                "  db:\n"
                "    image: postgres:15-alpine\n"
                "    environment:\n"
                "      - POSTGRES_USER=user\n"
                "      - POSTGRES_PASSWORD=pass\n"
                "      - POSTGRES_DB=appdb\n"
            )
            try:
                dc_path.write_text(dc_content, encoding="utf-8")
            except Exception:
                pass

    def deploy(
        self,
        project_id: str,
        project_path: Path,
        manifest: Dict[str, str],
        env_vars: Dict[str, str]
    ) -> ProviderDeploymentResult:
        _logger.info(f"LocalDockerProvider: Deploying '{project_id}' at '{project_path}'...")

        self.generate_dockerfile_if_missing(project_path, manifest)
        self.generate_compose_if_missing(project_path, manifest)

        has_docker = bool(shutil.which("docker"))
        has_compose = bool(shutil.which("docker-compose") or shutil.which("docker"))

        bindings = global_port_manager.allocate_ports_for_fullstack(project_id)
        fe_url = bindings["frontend"].url
        be_url = bindings["backend"].url

        if has_docker and has_compose:
            try:
                res = subprocess.run(
                    "docker-compose up -d --build",
                    shell=True,
                    cwd=str(project_path),
                    capture_output=True,
                    text=True,
                    timeout=180
                )
                if res.returncode == 0:
                    return ProviderDeploymentResult(
                        success=True,
                        provider_name="LocalDocker",
                        status="RUNNING",
                        frontend_url=fe_url,
                        backend_url=be_url,
                        stdout=res.stdout,
                        stderr=res.stderr
                    )
            except Exception as e:
                _logger.warning(f"Docker compose failed: {e}. Falling back to process manager runner.")

        # Fallback process runner deployment
        be_cmd = f"python -m uvicorn backend.main:app --host 0.0.0.0 --port {bindings['backend'].port}" if (project_path / "backend" / "main.py").exists() else f"python -m uvicorn main:app --host 0.0.0.0 --port {bindings['backend'].port}"
        global_process_manager.start_process(
            project_id=project_id,
            service_name="backend",
            command=be_cmd,
            cwd=str(project_path / "backend") if (project_path / "backend").exists() else str(project_path),
            port=bindings["backend"].port,
            env_vars=env_vars
        )

        fe_cmd = f"npx serve -s frontend -l {bindings['frontend'].port}" if (project_path / "frontend").exists() else f"npx serve -s . -l {bindings['frontend'].port}"
        global_process_manager.start_process(
            project_id=project_id,
            service_name="frontend",
            command=fe_cmd,
            cwd=str(project_path),
            port=bindings["frontend"].port,
            env_vars=env_vars
        )

        return ProviderDeploymentResult(
            success=True,
            provider_name="LocalProcess",
            status="RUNNING",
            frontend_url=fe_url,
            backend_url=be_url,
            stdout="Services started in isolated background processes.",
            stderr=""
        )

    def status(self, project_id: str) -> Dict[str, Any]:
        be_st = global_process_manager.get_status(project_id, "backend")
        fe_st = global_process_manager.get_status(project_id, "frontend")
        return {
            "project_id": project_id,
            "backend": be_st.model_dump() if be_st else None,
            "frontend": fe_st.model_dump() if fe_st else None
        }

    def logs(self, project_id: str) -> Dict[str, List[str]]:
        be_logs = global_process_manager.get_logs(project_id, "backend")
        fe_logs = global_process_manager.get_logs(project_id, "frontend")
        return {"backend": be_logs["stdout"], "frontend": fe_logs["stdout"]}

    def rollback(self, project_id: str) -> bool:
        return True

    def destroy(self, project_id: str) -> bool:
        global_process_manager.stop_process(project_id, "backend")
        global_process_manager.stop_process(project_id, "frontend")
        global_port_manager.release_ports_for_project(project_id)
        return True


global_local_docker_provider = LocalDockerProvider()
