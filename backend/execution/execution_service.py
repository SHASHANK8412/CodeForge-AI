"""
AIForge Execution Service
=========================
Coordinates execution backend selection, fallback policies, and lifecycle management.
Selects between LocalExecutionBackend and DockerExecutionBackend based on configuration
or runtime request parameters.
"""

import logging
from typing import Dict, Any, List, Optional

from backend import config as app_config
from backend.execution.execution_backend import (
    ExecutionBackend,
    LocalExecutionBackend,
    DockerExecutionBackend
)
from backend.execution.models import (
    ProjectExecutionResult,
    AutonomousValidationConfig
)

_logger = logging.getLogger("aiforge.execution.service")


class ExecutionService:
    """
    Execution Service orchestrating sandbox execution backend selection.
    Hierarchy:
    ExecutionService -> ExecutionBackend -> LocalExecutionBackend | DockerExecutionBackend
    """

    def __init__(
        self,
        default_backend: Optional[str] = None,
        local_backend: Optional[LocalExecutionBackend] = None,
        docker_backend: Optional[DockerExecutionBackend] = None
    ):
        configured_backend = default_backend or app_config.EXECUTION_BACKEND
        self.default_backend_name = (configured_backend or "local").lower()
        self.local_backend = local_backend or LocalExecutionBackend()
        self.docker_backend = docker_backend or DockerExecutionBackend()

    def get_backend(
        self,
        backend_name: Optional[str] = None,
        config: Optional[AutonomousValidationConfig] = None,
        strict_docker: bool = False
    ) -> ExecutionBackend:
        """
        Resolves and returns the appropriate execution backend.
        Priority:
        1. Explicit `backend_name` parameter ("docker" | "local")
        2. `config.execution_backend` or `config.docker_enabled`
        3. Default configured backend (`EXECUTION_BACKEND` / `DOCKER_ENABLED`)
        """
        target = backend_name
        if not target and config:
            if config.docker_enabled or config.execution_backend.lower() == "docker":
                target = "docker"
            else:
                target = config.execution_backend.lower()

        if not target:
            target = self.default_backend_name

        target = target.lower()

        if target == "docker":
            # Check docker availability
            if self.docker_backend.is_available():
                # Apply custom resource limits from config if available
                if config:
                    self.docker_backend.memory_limit = config.memory_limit or self.docker_backend.memory_limit
                    self.docker_backend.cpu_limit = config.cpu_limit or self.docker_backend.cpu_limit
                    self.docker_backend.network_mode = config.network_mode or self.docker_backend.network_mode
                    if config.docker_image:
                        self.docker_backend.default_image = config.docker_image
                return self.docker_backend

            if strict_docker:
                raise RuntimeError("DockerExecutionBackend was requested, but Docker is unavailable on host.")

            _logger.warning(
                "DockerExecutionBackend requested but Docker daemon/binary is unavailable. "
                "Falling back to LocalExecutionBackend."
            )
            return self.local_backend

        return self.local_backend

    def execute_command(
        self,
        command: List[str],
        cwd: str,
        timeout_seconds: float,
        max_output_bytes: int,
        custom_env: Optional[Dict[str, str]] = None,
        project_type: Optional[str] = None,
        backend_name: Optional[str] = None,
        config: Optional[AutonomousValidationConfig] = None
    ) -> ProjectExecutionResult:
        """Convenience method to execute a command through the resolved backend."""
        backend = self.get_backend(backend_name=backend_name, config=config)
        return backend.execute_command(
            command=command,
            cwd=cwd,
            timeout_seconds=timeout_seconds,
            max_output_bytes=max_output_bytes,
            custom_env=custom_env,
            project_type=project_type
        )

    def cleanup(self) -> None:
        """Cleans up all managed backend resources."""
        self.local_backend.cleanup()
        self.docker_backend.cleanup()


# Global ExecutionService Instance
global_execution_service = ExecutionService()
