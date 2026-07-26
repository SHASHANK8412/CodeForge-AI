import logging
from typing import Dict, Any, List

logger = logging.getLogger("aiforge.deployment.validator")


class DeploymentValidator:
    """
    DeploymentValidator verifies deployment files completeness and computes
    a Deployment Readiness Score out of 100.
    """

    def validate_deployment_files(self, project_files: Dict[str, str]) -> Dict[str, Any]:
        checks = {
            "backend_dockerfile": False,
            "frontend_dockerfile": False,
            "docker_compose": False,
            "github_actions": False,
            "kubernetes": False,
            "nginx": False,
            "deploy_scripts": False
        }
        errors = []
        warnings = []

        for path in project_files:
            if "backend/Dockerfile" in path or "Dockerfile.backend" in path:
                checks["backend_dockerfile"] = True
            elif "frontend/Dockerfile" in path or "Dockerfile.frontend" in path or "Dockerfile" in path:
                checks["frontend_dockerfile"] = True
            elif "docker-compose.yml" in path:
                checks["docker_compose"] = True
            elif ".github/workflows" in path:
                checks["github_actions"] = True
            elif "kubernetes" in path or "deployment.yaml" in path:
                checks["kubernetes"] = True
            elif "nginx.conf" in path:
                checks["nginx"] = True
            elif "deploy.sh" in path or "deploy.ps1" in path:
                checks["deploy_scripts"] = True

        passed_count = sum(1 for v in checks.values() if v)
        total_checks = len(checks)
        readiness_score = round((passed_count / total_checks) * 100, 1)

        if not checks["backend_dockerfile"]:
            errors.append("Missing backend/Dockerfile.")
        if not checks["docker_compose"]:
            errors.append("Missing docker-compose.yml.")
        if not checks["kubernetes"]:
            warnings.append("Kubernetes manifests not found.")

        logger.info(f"Deployment Validation Readiness Score: {readiness_score}% ({passed_count}/{total_checks} passed)")

        return {
            "readiness_score": readiness_score,
            "is_ready": readiness_score >= 80.0,
            "checks": checks,
            "errors": errors,
            "warnings": warnings
        }


# Global DeploymentValidator Instance
global_deployment_validator = DeploymentValidator()
