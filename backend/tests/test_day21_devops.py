import pytest
from fastapi.testclient import TestClient

from backend.deployment.docker_generator import DockerGenerator
from backend.deployment.compose_generator import ComposeGenerator
from backend.deployment.github_actions import GithubActionsGenerator
from backend.deployment.kubernetes import KubernetesGenerator
from backend.deployment.nginx import NginxGenerator
from backend.deployment.scripts import DeploymentScriptGenerator
from backend.deployment.validator import DeploymentValidator
from backend.deployment.exporter import DeploymentExporter
from backend.main import app

client = TestClient(app)


def test_docker_generator():
    """Test 1: DockerGenerator backend and frontend Dockerfiles."""
    gen = DockerGenerator()

    be_df = gen.generate_backend_dockerfile()
    assert "FROM python:3.12-slim" in be_df
    assert "uvicorn" in be_df
    assert "HEALTHCHECK" in be_df

    fe_df = gen.generate_frontend_dockerfile()
    assert "FROM node:20-alpine" in fe_df
    assert "nginx:alpine" in fe_df


def test_compose_generator():
    """Test 2: ComposeGenerator docker-compose.yml multi-container configuration."""
    gen = ComposeGenerator()

    compose = gen.generate_compose_yml("Streaming Platform")
    assert "streaming_platform_backend" in compose
    assert "postgres:" in compose
    assert "redis:" in compose
    assert "postgres_data:" in compose


def test_github_actions_generator():
    """Test 3: GithubActionsGenerator CI/CD pipeline generation."""
    gen = GithubActionsGenerator()

    ci = gen.generate_ci_workflow()
    assert "AIForge Autonomous CI/CD Pipeline" in ci
    assert "actions/setup-python" in ci
    assert "actions/setup-node" in ci


def test_kubernetes_and_nginx_generators():
    """Test 4: KubernetesGenerator manifests and NginxGenerator config."""
    k8s_gen = KubernetesGenerator()
    nginx_gen = NginxGenerator()

    deploy_yml = k8s_gen.generate_deployment_yaml("Streaming App")
    assert "kind: Deployment" in deploy_yml
    assert "streaming-app-backend" in deploy_yml

    svc_yml = k8s_gen.generate_service_yaml("Streaming App")
    assert "kind: Service" in svc_yml

    ingress_yml = k8s_gen.generate_ingress_yaml("Streaming App")
    assert "kind: Ingress" in ingress_yml

    nginx = nginx_gen.generate_nginx_conf()
    assert "location /api/" in nginx
    assert "proxy_pass http://backend:8000/;" in nginx


def test_deployment_script_generator():
    """Test 5: DeploymentScriptGenerator Linux deploy.sh & Windows deploy.ps1."""
    gen = DeploymentScriptGenerator()

    sh = gen.generate_deploy_sh()
    assert "#!/usr/bin/env bash" in sh
    assert "docker compose up -d" in sh

    ps1 = gen.generate_deploy_ps1()
    assert "Write-Host" in ps1
    assert "docker compose up -d" in ps1


def test_deployment_validator_and_api_routes():
    """Test 6: DeploymentValidator score calculation and FastAPI deployment endpoints."""
    exp = DeploymentExporter()
    bundle = exp.generate_deployment_bundle("DevOps Platform")

    assert bundle["total_deployment_files"] == 10
    assert bundle["validation"]["readiness_score"] == 100.0
    assert bundle["validation"]["is_ready"] is True

    # Test GET /api/deployment/files/{project_id}
    res_files = client.get("/api/deployment/files/devops_test_01")
    assert res_files.status_code == 200
    data_files = res_files.json()
    assert "files" in data_files
    assert "docker-compose.yml" in data_files["files"]

    # Test GET /api/deployment/report/{project_id}
    res_rep = client.get("/api/deployment/report/devops_test_01")
    assert res_rep.status_code == 200
    data_rep = res_rep.json()
    assert data_rep["readiness_score"] == 100.0
    assert data_rep["is_ready"] is True
