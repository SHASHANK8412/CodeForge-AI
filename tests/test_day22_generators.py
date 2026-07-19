import json
import shutil
import pytest
from pathlib import Path

from backend.generators.dependency_generator import DependencyGenerator
from backend.generators.package_generator import PackageGenerator
from backend.generators.requirements_generator import RequirementsGenerator
from backend.generators.docker_generator import DockerGenerator
from backend.generators.compose_generator import ComposeGenerator
from backend.generators.env_generator import EnvGenerator
from backend.generators.readme_generator import ReadmeGenerator
from backend.validators.project_validator import ProjectValidator
from backend.generators.project_generator import ProjectGenerator, GENERATED_PROJECTS_DIR


def test_dependency_generator():
    dep_gen = DependencyGenerator()

    state = {
        "frontend": "import React from 'react';\nimport axios from 'axios';\nimport { BrowserRouter } from 'react-router-dom';",
        "backend": "import fastapi\nfrom pymongo import MongoClient\nimport jwt",
        "database": "postgresql database setup"
    }

    deps = dep_gen.detect_dependencies(state)

    assert "react" in deps.frontend
    assert "react-router-dom" in deps.frontend
    assert "axios" in deps.frontend

    assert "fastapi" in deps.backend
    # pymongo mapping -> pymongo
    assert "pymongo" in deps.backend
    # jwt mapping -> pyjwt
    assert "pyjwt" in deps.backend
    # database postgresql adds psycopg2 to backend deps
    assert "psycopg2-binary" in deps.backend

    assert "postgresql" in deps.database


def test_package_generator():
    pkg_gen = PackageGenerator()
    dependencies = ["react", "react-dom", "react-router-dom", "axios", "tailwindcss"]

    json_str = pkg_gen.generate_package_json("Test-App", dependencies)
    data = json.loads(json_str)

    assert data["name"] == "test-app"
    assert "dependencies" in data
    assert data["dependencies"]["react"] == "^18.2.0"
    assert data["dependencies"]["react-router-dom"] == "^6.14.2"
    assert "tailwindcss" in data["dependencies"]
    assert "devDependencies" in data
    assert "vite" in data["devDependencies"]


def test_requirements_generator():
    req_gen = RequirementsGenerator()
    dependencies = ["fastapi", "uvicorn", "pydantic", "pymongo", "redis"]
    extras = ["pytest", "pyjwt"]

    req_str = req_gen.generate_requirements(dependencies, extras)
    lines = [line.strip() for line in req_str.splitlines() if line.strip()]

    # check alphabetical sorting
    assert lines == sorted(lines)
    assert any("fastapi>=0.100.0" in line for line in lines)
    assert any("uvicorn>=0.22.0" in line for line in lines)
    assert any("pydantic>=2.0.0" in line for line in lines)
    assert any("pymongo>=4.5.0" in line for line in lines)
    assert any("redis>=4.6.0" in line for line in lines)
    assert any("pytest>=7.4.0" in line for line in lines)
    assert any("pyjwt>=2.7.0" in line for line in lines)


def test_docker_generator():
    doc_gen = DockerGenerator()

    backend_docker = doc_gen.generate_backend_dockerfile()
    assert "FROM python:3.11-slim" in backend_docker
    assert "WORKDIR /app" in backend_docker
    assert "CMD" in backend_docker

    frontend_docker = doc_gen.generate_frontend_dockerfile()
    assert "FROM node:18-slim AS builder" in frontend_docker
    assert "FROM nginx:alpine" in frontend_docker


def test_compose_generator():
    comp_gen = ComposeGenerator()

    postgres_compose = comp_gen.generate_compose(["postgresql", "redis"])
    assert "image: postgres:15-alpine" in postgres_compose
    assert "image: redis:7-alpine" in postgres_compose

    mongo_compose = comp_gen.generate_compose(["mongodb"])
    assert "image: mongo:6.0" in mongo_compose


def test_env_generator():
    env_gen = EnvGenerator()

    postgres_env = env_gen.generate_env_example(["postgresql"])
    assert "DATABASE_URL=postgresql://" in postgres_env
    assert "JWT_SECRET=" in postgres_env

    mongo_env = env_gen.generate_env_example(["mongodb"])
    assert "DATABASE_URL=mongodb://" in mongo_env


def test_readme_generator():
    readme_gen = ReadmeGenerator()
    state = {
        "plan": "Phase 1: Build Database",
        "architecture": "Architecture overview"
    }

    readme_content = readme_gen.generate_readme("My Project", state)
    assert "# My Project" in readme_content
    assert "Phase 1: Build Database" in readme_content
    assert "Folder Structure" in readme_content
    assert "Docker Compose" in readme_content


def test_project_validator(tmp_path):
    validator = ProjectValidator()

    # Empty validation
    report = validator.validate_project(tmp_path)
    assert report.is_valid is False
    assert any("Missing required file" in err for err in report.errors)

    # Populate dummy directories and files
    (tmp_path / "frontend").mkdir()
    (tmp_path / "backend").mkdir()
    (tmp_path / "database").mkdir()
    (tmp_path / "tests").mkdir()

    (tmp_path / "README.md").write_text("# Readme")
    (tmp_path / "package.json").write_text(json.dumps({"name": "test", "version": "1.0.0", "dependencies": {}}))
    (tmp_path / "requirements.txt").write_text("fastapi\nuvicorn\n")
    (tmp_path / "frontend/Dockerfile").write_text("FROM node:18\nEXPOSE 80")
    (tmp_path / "backend/Dockerfile").write_text("FROM python:3.11\nEXPOSE 8000")
    (tmp_path / "docker-compose.yml").write_text("version: '3.8'\nservices:\n  app:\n    image: node")
    (tmp_path / ".env.example").write_text("PORT=8000")
    (tmp_path / ".gitignore").write_text("node_modules/")
    (tmp_path / "LICENSE").write_text("MIT License")

    report2 = validator.validate_project(tmp_path)
    assert report2.is_valid is True
    assert len(report2.errors) == 0


def test_project_generator_orchestration():
    proj_gen = ProjectGenerator()

    state = {
        "plan": "This is plan outline",
        "architecture": "This is architecture outline",
        "frontend": "```jsx\n// filename: frontend/src/App.jsx\nexport default function App() {}\n```",
        "backend": "```python\n# filepath: backend/main.py\nprint('hello')\n```",
        "database": "CREATE TABLE users (id INT);",
        "tests": "def test_app(): pass",
        "documentation": "README documentation info",
    }

    project_name = "Final-Intelligent-App"
    safe_name = "Final-Intelligent-App"
    project_dir = GENERATED_PROJECTS_DIR / safe_name
    zip_path = GENERATED_PROJECTS_DIR / f"{safe_name}.zip"

    # Clean up first
    if project_dir.exists():
        shutil.rmtree(project_dir)
    if zip_path.exists():
        zip_path.unlink()

    # Generate
    p_dir, report = proj_gen.generate_project_structure(project_name, state)

    assert p_dir == project_dir
    assert project_dir.exists()
    assert (project_dir / "package.json").exists()
    assert (project_dir / "requirements.txt").exists()
    assert (project_dir / "docker-compose.yml").exists()
    assert (project_dir / ".env.example").exists()
    assert (project_dir / "README.md").exists()
    assert (project_dir / "LICENSE").exists()
    assert zip_path.exists()
    assert report.is_valid is True

    # Clean up
    shutil.rmtree(project_dir)
    zip_path.unlink()
