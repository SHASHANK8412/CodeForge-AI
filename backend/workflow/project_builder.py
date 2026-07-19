import json
import re
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.workflow.file_writer import write_project_file

_logger = logging.getLogger("aiforge.performance")

# Base directory where all projects are exported
GENERATED_PROJECTS_DIR = Path(__file__).resolve().parent.parent.parent / "generated_projects"


def extract_code_files(text: str) -> dict[str, str]:
    """
    Scans a text block for markdown code blocks containing file annotations
    such as `# filepath: backend/main.py` or `// filename: src/App.jsx`.
    Returns a dictionary of relative_path -> file_content.
    """
    files = {}
    if not text:
        return files

    # Look for code blocks with path annotations:
    # ```language
    # # filepath: relative/path/to/file
    # content
    # ```
    pattern = re.compile(
        r"```[a-zA-Z0-9_\-]*\s*\n(?:#|//)\s*(?:filepath|filename|file|path):\s*([^\n\r]+)\s*\n(.*?)\n```",
        re.DOTALL | re.IGNORECASE
    )

    for match in pattern.finditer(text):
        filepath = match.group(1).strip()
        # Remove common code blocks delimiters or extra leading/trailing whitespace
        content = match.group(2)
        # Normalize path delimiters for cross-platform compatibility
        normalized_path = filepath.replace("\\", "/")
        files[normalized_path] = content

    return files


def build_project(project_name: str, state: dict[str, Any]) -> Path:
    """
    Takes the compiled ProjectState output and structures it into a downloadable project folder on disk.
    Generates folder layouts, code files, README.md, requirements.txt, package.json, docker-compose.yml,
    metadata JSON, and packages the project into a ZIP archive.
    """
    GENERATED_PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

    # Normalize folder name
    safe_name = "".join([c if c.isalnum() or c in " -_" else "_" for c in project_name]).strip()
    project_dir = GENERATED_PROJECTS_DIR / safe_name
    project_dir.mkdir(parents=True, exist_ok=True)

    _logger.info(f"Assembling project: {project_name} at {project_dir}")

    # 1. Parse code files from agent output blocks
    extracted_files: dict[str, str] = {}
    for key in ["frontend", "backend", "database", "tests", "documentation"]:
        extracted_files.update(extract_code_files(state.get(key, "")))

    # 2. Write extracted files
    for rel_path, content in extracted_files.items():
        write_project_file(project_dir / rel_path, content)

    # 3. Fallback defaults if no file path annotations were found in agent blocks
    # Backend fallback
    if "backend/main.py" not in extracted_files and state.get("backend"):
        # Strip out general code blocks
        backend_content = re.sub(r"```[a-zA-Z0-9_\-]*\n|```", "", state["backend"]).strip()
        write_project_file(project_dir / "backend/main.py", backend_content)

    # Frontend fallback
    if "frontend/src/App.jsx" not in extracted_files and state.get("frontend"):
        frontend_content = re.sub(r"```[a-zA-Z0-9_\-]*\n|```", "", state["frontend"]).strip()
        write_project_file(project_dir / "frontend/src/App.jsx", frontend_content)

    # Database fallback
    if "database/schema.sql" not in extracted_files and state.get("database"):
        db_content = re.sub(r"```[a-zA-Z0-9_\-]*\n|```", "", state["database"]).strip()
        write_project_file(project_dir / "database/schema.sql", db_content)

    # Testing fallback
    if "tests/test_app.py" not in extracted_files and state.get("tests"):
        test_content = re.sub(r"```[a-zA-Z0-9_\-]*\n|```", "", state["tests"]).strip()
        write_project_file(project_dir / "tests/test_app.py", test_content)

    # 4. Standard structural templates if not already present
    if "requirements.txt" not in extracted_files:
        req_template = "fastapi>=0.100.0\nuvicorn>=0.22.0\npydantic>=2.0.0\npytest>=7.0.0\nhttpx>=0.24.0\n"
        write_project_file(project_dir / "requirements.txt", req_template)

    if "package.json" not in extracted_files:
        package_template = {
            "name": safe_name.lower().replace(" ", "-"),
            "version": "1.0.0",
            "private": True,
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0"
            },
            "devDependencies": {
                "vite": "^4.4.5"
            },
            "scripts": {
                "dev": "vite",
                "build": "vite build"
            }
        }
        write_project_file(project_dir / "package.json", json.dumps(package_template, indent=4))

    if "docker-compose.yml" not in extracted_files:
        compose_template = """version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
"""
        write_project_file(project_dir / "docker-compose.yml", compose_template)

    # 5. Core documents
    if state.get("plan"):
        write_project_file(project_dir / "plan.md", state["plan"])
    if state.get("architecture"):
        write_project_file(project_dir / "architecture.md", state["architecture"])
    if state.get("review"):
        write_project_file(project_dir / "review.md", state["review"])

    # Documentation/README
    if state.get("documentation"):
        readme_content = re.sub(r"```[a-zA-Z0-9_\-]*\n|```", "", state["documentation"]).strip()
        write_project_file(project_dir / "README.md", readme_content)
    elif "README.md" not in extracted_files:
        default_readme = f"# {project_name}\n\nGenerated autonomously by AIForge.\n"
        write_project_file(project_dir / "README.md", default_readme)

    # 6. Metadata file: project.json
    metadata = {
        "project_name": project_name,
        "framework": "React + FastAPI",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "agents_used": [
            "Planner",
            "Architect",
            "Frontend",
            "Backend",
            "Database",
            "Reviewer",
            "Documentation"
        ]
    }
    write_project_file(project_dir / "project.json", json.dumps(metadata, indent=4))

    # 7. ZIP Export Archive Generation
    zip_base_path = GENERATED_PROJECTS_DIR / safe_name
    try:
        shutil.make_archive(str(zip_base_path), "zip", root_dir=str(project_dir))
        _logger.info(f"ZIP project archive created: {zip_base_path}.zip")
    except Exception as exc:
        _logger.error(f"Failed to create ZIP archive for project {project_name}: {exc}")
        raise

    return project_dir
