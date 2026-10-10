"""
AIForge Local Docker Deployment Provider
=======================================
Local deployment = the project's hardened preview containers (backend/execution/preview_manager.py).
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from backend.deployment.providers.base_provider import DeploymentProvider, ProviderDeploymentResult

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
        """
        Runs the project through the hardened preview containers and waits for it to answer.
        The generated docker-compose.yml is not executed (it is untrusted and could mount host
        paths or run privileged), and there is no fallback that starts the app on the host.
        env_vars are not passed into the preview containers.
        """
        _logger.info(f"LocalDockerProvider: Deploying '{project_id}' at '{project_path}' in preview containers...")
        self.generate_dockerfile_if_missing(project_path, manifest)
        self.generate_compose_if_missing(project_path, manifest)

        from backend.execution.preview_manager import start_preview
        preview = start_preview(project_id, Path(project_path), wait=True)
        running = preview.status in ("running", "partial")
        logs = "\n".join(s.logs for s in (preview.backend, preview.frontend) if s.logs)
        errors = "; ".join(f"{name}: {s.error}" for name, s in (("backend", preview.backend), ("frontend", preview.frontend))
                           if s.error and s.status != "not_previewable")
        return ProviderDeploymentResult(
            success=running,
            provider_name="LocalDockerPreview",
            status="RUNNING" if running else ("FAILED" if preview.status == "failed" else preview.status.upper()),
            frontend_url=preview.frontend.url,
            backend_url=preview.backend.url,
            stdout=logs[-20_000:],
            stderr=errors,
            error_message=None if running else (preview.reason or errors or "preview did not start"),
        )

    def status(self, project_id: str) -> Dict[str, Any]:
        from backend.execution.preview_manager import get_preview
        preview = get_preview(project_id)
        return preview.to_dict() if preview else {"project_id": project_id, "status": "not_started"}

    def logs(self, project_id: str) -> Dict[str, List[str]]:
        from backend.execution.preview_manager import get_preview
        preview = get_preview(project_id)
        if not preview:
            return {"backend": [], "frontend": []}
        return {"backend": preview.backend.logs.splitlines(), "frontend": preview.frontend.logs.splitlines()}

    def rollback(self, project_id: str) -> bool:
        return True

    def destroy(self, project_id: str) -> bool:
        from backend.execution.preview_manager import stop_preview
        stop_preview(project_id)
        return True


global_local_docker_provider = LocalDockerProvider()
