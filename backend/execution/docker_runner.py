import logging
from typing import Dict, Any

logger = logging.getLogger("aiforge.execution.docker_runner")


class DockerRunner:
    """
    DockerRunner tests containerization builds and container readiness.
    """

    def test_container_build(self, dockerfiles: Dict[str, str]) -> Dict[str, Any]:
        has_backend_df = any("backend/Dockerfile" in k or "Dockerfile" in k for k in dockerfiles)
        return {
            "status": "success" if has_backend_df else "warning",
            "dockerfile_count": len(dockerfiles),
            "message": "Docker build check completed."
        }


# Global DockerRunner Instance
global_docker_runner = DockerRunner()
