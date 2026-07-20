import pytest
from pathlib import Path
from backend.services.deployment.docker_generator import DockerGenerator
from backend.services.deployment.compose_generator import ComposeGenerator
from backend.services.deployment.env_detector import EnvDetector
from backend.services.deployment.validator import DeploymentValidator
from backend.services.deployment.github_actions import GitHubActionsGenerator
from backend.services.deployment.bundle_exporter import BundleExporter
from backend.agents.deployment_agent import DeploymentAgent

def test_docker_generation():
    docker_gen = DockerGenerator()
    
    # 1. Test frontend React
    fe_df = docker_gen.generate_frontend_dockerfile("react", 80)
    assert "FROM node" in fe_df
    assert "FROM nginx" in fe_df
    assert "EXPOSE 80" in fe_df

    # 2. Test Next.js
    next_df = docker_gen.generate_frontend_dockerfile("next.js", 3000)
    assert "FROM node:20-alpine" in next_df
    assert "EXPOSE 3000" in next_df

    # 3. Test backend FastAPI
    be_df = docker_gen.generate_backend_dockerfile("fastapi", 8000)
    assert "FROM python" in be_df
    assert "EXPOSE 8000" in be_df
    assert "uvicorn" in be_df

    # 4. Test Express
    exp_df = docker_gen.generate_backend_dockerfile("express", 5000)
    assert "EXPOSE 5000" in exp_df
    assert "node" in exp_df

    # 5. Test dockerignore
    ignore = docker_gen.generate_dockerignore()
    assert "node_modules" in ignore
    assert "__pycache__" in ignore

def test_compose_generation():
    compose_gen = ComposeGenerator()
    databases = ["postgres", "redis"]
    compose_yml = compose_gen.generate_compose(
        databases=databases,
        frontend_framework="react",
        backend_framework="fastapi",
        frontend_port=80,
        backend_port=8000
    )
    assert "postgres:" in compose_yml
    assert "redis:" in compose_yml
    assert "frontend:" in compose_yml
    assert "backend:" in compose_yml
    assert "aiforge-network" in compose_yml

def test_env_detection():
    detector = EnvDetector()
    mock_code = """
    db_conn = os.environ.get("DATABASE_URL")
    jwt_sec = os.getenv("JWT_SECRET")
    secret = os.environ["SECRET_KEY"]
    app_port = process.env.PORT
    """
    vars_map = detector.detect_variables(mock_code)
    assert "DATABASE_URL" in vars_map
    assert "JWT_SECRET" in vars_map
    assert "SECRET_KEY" in vars_map
    assert "PORT" in vars_map

    example = detector.generate_env_example(vars_map)
    assert "DATABASE_URL=" in example
    assert "JWT_SECRET=" in example

def test_github_actions_generation():
    actions_gen = GitHubActionsGenerator()
    workflows = actions_gen.generate_workflows("test-app", "react", "fastapi")
    
    assert ".github/workflows/lint.yml" in workflows
    assert ".github/workflows/test.yml" in workflows
    assert ".github/workflows/deploy.yml" in workflows
    
    assert "black" in workflows[".github/workflows/lint.yml"]
    assert "pytest" in workflows[".github/workflows/test.yml"]
    assert "docker/build-push-action" in workflows[".github/workflows/deploy.yml"]

    badges = actions_gen.generate_badges("https://github.com/user/test-app")
    assert "actions/workflows/test.yml/badge.svg" in badges

def test_deployment_validator():
    validator = DeploymentValidator()
    
    # Mock parameters
    state = {
        "requirements": "fastapi\npsycopg2",
        "backend": "from fastapi import FastAPI\napp = FastAPI()",
        "frontend": "import React from 'react';"
    }
    deployment_files = {
        "frontend/Dockerfile": "FROM node:20\nCMD npm run start\nEXPOSE 80",
        "backend/Dockerfile": "FROM python:3.11\nCMD uvicorn main:app\nEXPOSE 8000",
        ".env.example": "DATABASE_URL=\nPORT=\n"
    }
    env_vars = {"DATABASE_URL": "...", "PORT": "..."}
    frameworks = {"frontend": "react", "backend": "fastapi"}
    databases = ["postgres"]

    report = validator.validate("test-app", state, deployment_files, env_vars, frameworks, databases)
    assert report.ready is True
    assert report.readiness_score >= 80
    assert report.suggested_platform == "Railway"  # postgres + fastapi -> Railway

def test_bundle_exporter():
    exporter = BundleExporter()
    guide = exporter.generate_deployment_guide("test-app", "Render", "Simple setup")
    assert "# Deployment Guide" in guide
    assert "Render" in guide
    assert "docker-compose up" in guide

def test_deployment_agent_run():
    agent = DeploymentAgent()
    state = {
        "user_prompt": "Create an e-commerce backend",
        "prompt": "Create an e-commerce backend",
        "frontend": "import React from 'react';\nprocess.env.PORT",
        "backend": "from fastapi import FastAPI\nimport os\ndb = os.getenv('DATABASE_URL')",
        "database": "CREATE TABLE users (id INT);"
    }
    
    result = agent.run(state)
    assert "deployment_files" in result
    assert "deployment_report" in result
    assert "deployment_platform" in result
    assert "deployment_guide" in result
    
    # Verify exact files are in mapping
    files = result["deployment_files"]
    assert "frontend/Dockerfile" in files
    assert "backend/Dockerfile" in files
    assert "docker-compose.yml" in files
    assert ".dockerignore" in files
    assert ".env.example" in files
    assert ".github/workflows/test.yml" in files

def test_edge_cases():
    agent = DeploymentAgent()
    # Test fallback database when empty
    state = {
        "prompt": "Simple app",
        "frontend": "",
        "backend": ""
    }
    result = agent.run(state)
    assert "sqlite" in result["deployment_report"]["detected_databases"]
