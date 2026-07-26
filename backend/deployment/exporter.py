import logging
from typing import Dict, Any

from backend.deployment.docker_generator import global_docker_generator
from backend.deployment.compose_generator import global_compose_generator
from backend.deployment.github_actions import global_github_actions_generator
from backend.deployment.kubernetes import global_kubernetes_generator
from backend.deployment.nginx import global_nginx_generator
from backend.deployment.scripts import global_deployment_script_generator
from backend.deployment.validator import global_deployment_validator

logger = logging.getLogger("aiforge.deployment.exporter")


class DeploymentExporter:
    """
    DeploymentExporter generates a complete, production-ready DevOps deployment manifest bundle:
    - backend/Dockerfile & frontend/Dockerfile
    - docker-compose.yml
    - .github/workflows/ci.yml
    - kubernetes/ (deployment.yaml, service.yaml, ingress.yaml)
    - nginx.conf
    - deploy.sh & deploy.ps1
    """

    def generate_deployment_bundle(self, project_name: str = "AIForge App") -> Dict[str, Any]:
        files = {
            "backend/Dockerfile": global_docker_generator.generate_backend_dockerfile(),
            "frontend/Dockerfile": global_docker_generator.generate_frontend_dockerfile(),
            "docker-compose.yml": global_compose_generator.generate_compose_yml(project_name),
            ".github/workflows/ci.yml": global_github_actions_generator.generate_ci_workflow(),
            "kubernetes/deployment.yaml": global_kubernetes_generator.generate_deployment_yaml(project_name),
            "kubernetes/service.yaml": global_kubernetes_generator.generate_service_yaml(project_name),
            "kubernetes/ingress.yaml": global_kubernetes_generator.generate_ingress_yaml(project_name),
            "nginx.conf": global_nginx_generator.generate_nginx_conf(),
            "deploy.sh": global_deployment_script_generator.generate_deploy_sh(),
            "deploy.ps1": global_deployment_script_generator.generate_deploy_ps1()
        }

        validation = global_deployment_validator.validate_deployment_files(files)

        return {
            "project_name": project_name,
            "total_deployment_files": len(files),
            "files": files,
            "validation": validation
        }


# Global DeploymentExporter Instance
global_deployment_exporter = DeploymentExporter()
