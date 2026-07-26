import io
import zipfile
import pytest
from fastapi.testclient import TestClient

from backend.exporter.validator import ProjectValidator
from backend.exporter.dependency_resolver import DependencyResolver
from backend.exporter.readme_generator import ReadmeGenerator
from backend.exporter.env_generator import EnvGenerator
from backend.exporter.metadata import MetadataGenerator
from backend.exporter.zipper import ProjectZipper
from backend.exporter.assembler import ProjectAssembler
from backend.main import app

client = TestClient(app)


def test_project_validator_checks():
    """Test 1: ProjectValidator structure validation rules."""
    validator = ProjectValidator()

    # Valid project files map
    valid_files = {
        "frontend/package.json": '{"name": "app"}',
        "frontend/src/App.jsx": "export default function App() {}",
        "backend/requirements.txt": "fastapi\n",
        "backend/main.py": "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/')\ndef r(): pass",
        "database/schema.sql": "CREATE TABLE users ();",
        "README.md": "# Project"
    }

    res = validator.validate_project(valid_files)
    assert res["is_valid"] is True
    assert res["checks"]["frontend"] is True
    assert res["checks"]["backend"] is True
    assert res["checks"]["database"] is True
    assert res["checks"]["documentation"] is True

    # Invalid missing requirements.txt
    invalid_files = {"frontend/src/App.jsx": "code"}
    res_inv = validator.validate_project(invalid_files)
    assert res_inv["is_valid"] is False
    assert len(res_inv["errors"]) >= 1


def test_dependency_resolver_generation():
    """Test 2: DependencyResolver python requirements.txt and package.json generation."""
    resolver = DependencyResolver()

    reqs = resolver.generate_requirements_txt({"main.py": "import jwt\nimport stripe\nfrom fastapi import FastAPI"})
    assert "fastapi" in reqs
    assert "python-jose" in reqs
    assert "stripe" in reqs

    pkg = resolver.generate_package_json("Learning Platform", {"App.jsx": "import { useState } from 'react';"})
    assert "learning-platform" in pkg
    assert "react" in pkg
    assert "vite" in pkg


def test_readme_and_env_generators():
    """Test 3: ReadmeGenerator and EnvGenerator file creation."""
    readme_gen = ReadmeGenerator()
    env_gen = EnvGenerator()

    readme = readme_gen.generate_readme("Learning Management System", "Build LMS App", {"frontend": "React", "backend": "FastAPI"})
    assert "Learning Management System" in readme
    assert "Quick Start Guide" in readme

    env = env_gen.generate_env_example({"database": "PostgreSQL"})
    assert "DATABASE_URL=postgresql://" in env
    assert "JWT_SECRET=" in env


def test_project_assembler_full_pipeline():
    """Test 4: ProjectAssembler complete project assembly pipeline."""
    assembler = ProjectAssembler()

    state = {
        "prompt": "Build Learning Management System",
        "plan": {"project_name": "Learning Platform"},
        "frontend_code": {"src/App.jsx": "export default function App() {}"},
        "backend_code": {"main.py": "from fastapi import FastAPI\napp = FastAPI()"},
        "project_files": {
            "frontend/src/App.jsx": "export default function App() {}",
            "backend/main.py": "from fastapi import FastAPI\napp = FastAPI()",
            "database/schema.sql": "CREATE TABLE courses (id SERIAL PRIMARY KEY);"
        }
    }

    assembled = assembler.assemble_project(state)

    assert assembled["project_name"] == "Learning Platform"
    assert "README.md" in assembled["project_files"]
    assert ".env.example" in assembled["project_files"]
    assert "project.json" in assembled["project_files"]
    assert len(assembled["zip_bytes"]) > 0


def test_project_zipper_archive_structure():
    """Test 5: ProjectZipper in-memory ZIP archive creation and inspection."""
    zipper = ProjectZipper()

    files = {
        "frontend/src/App.jsx": "App Code",
        "backend/main.py": "Backend Code",
        "README.md": "Documentation"
    }

    zip_bytes = zipper.create_zip_bytes(files, root_folder="lms_project")
    assert len(zip_bytes) > 0

    # Inspect ZIP entries
    buffer = io.BytesIO(zip_bytes)
    with zipfile.ZipFile(buffer, mode="r") as zf:
        names = zf.namelist()
        assert "lms_project/frontend/src/App.jsx" in names
        assert "lms_project/backend/main.py" in names
        assert "lms_project/README.md" in names


def test_export_and_file_tree_api_endpoints():
    """Test 6: GET /api/export/{project_id} and GET /api/project-files/{project_id} endpoints."""
    # 1. File Tree API
    res_tree = client.get("/api/project-files/export_test_01")
    assert res_tree.status_code == 200
    data_tree = res_tree.json()
    assert data_tree["project_id"] == "export_test_01"

    # 2. Export ZIP API
    res_zip = client.get("/api/export/export_test_01")
    assert res_zip.status_code == 200
    assert res_zip.headers["content-type"] == "application/zip"
    assert len(res_zip.content) > 0
