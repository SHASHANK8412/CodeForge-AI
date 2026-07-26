import time
import logging
from typing import Dict, Any, List

from backend.graph.state import WorkflowState
from backend.exporter.validator import global_project_validator
from backend.exporter.dependency_resolver import global_dependency_resolver
from backend.exporter.readme_generator import global_readme_generator
from backend.exporter.env_generator import global_env_generator
from backend.exporter.metadata import global_metadata_generator
from backend.exporter.zipper import global_project_zipper

logger = logging.getLogger("aiforge.exporter.assembler")


class ProjectAssembler:
    """
    ProjectAssembler compiles agent outputs into a unified production-ready project folder tree:
    - Merges Frontend, Backend, Database, Test, and Documentation files
    - Generates requirements.txt and package.json via DependencyResolver
    - Generates README.md and .env.example
    - Creates project.json metadata file
    - Validates project structure and returns final ZIP archive bytes
    """

    def assemble_project(self, state: WorkflowState) -> Dict[str, Any]:
        """Assembles, validates, and packages complete software project."""
        start_time = time.time()
        prompt = state.get("prompt", "AIForge Application")
        project_name = state.get("plan", {}).get("project_name", "AIForge Application") if isinstance(state.get("plan"), dict) else "AIForge Application"

        # 1. Base Files Dictionary
        files = dict(state.get("project_files", {}))

        # 2. Extract Frontend & Backend File Maps
        fe_files = state.get("frontend_code", {}) if isinstance(state.get("frontend_code"), dict) else {}
        be_files = state.get("backend_code", {}) if isinstance(state.get("backend_code"), dict) else {}

        # 3. Generate Dependencies
        req_txt = global_dependency_resolver.generate_requirements_txt(be_files)
        pkg_json = global_dependency_resolver.generate_package_json(project_name, fe_files)

        files["backend/requirements.txt"] = req_txt
        files["frontend/package.json"] = pkg_json

        # 4. Generate README & Env Example
        tech_stack = {
            "frontend": "React (Vite)",
            "backend": "FastAPI",
            "database": "PostgreSQL",
            "auth": "JWT"
        }
        routes = state.get("architecture", {}).get("routes", []) if isinstance(state.get("architecture"), dict) else []

        readme_md = global_readme_generator.generate_readme(project_name, prompt, tech_stack, routes)
        env_example = global_env_generator.generate_env_example(tech_stack)

        files["README.md"] = readme_md
        files[".env.example"] = env_example

        # 5. Add Docker Compose if not present
        if "docker-compose.yml" not in files:
            files["docker-compose.yml"] = (
                "version: '3.8'\n"
                "services:\n"
                "  backend:\n"
                "    build: ./backend\n"
                "    ports:\n"
                "      - '8000:8000'\n"
                "  frontend:\n"
                "    build: ./frontend\n"
                "    ports:\n"
                "      - '5173:5173'\n"
            )

        # 6. Validate Project Structure
        val_result = global_project_validator.validate_project(files)

        # 7. Generate Project Metadata
        assembly_time = round(time.time() - start_time, 3)
        proj_json = global_metadata_generator.generate_project_metadata(
            project_name=project_name,
            tech_stack=tech_stack,
            file_count=len(files),
            assembly_time_seconds=assembly_time
        )
        files["project.json"] = proj_json

        # 8. Create ZIP Bytes Archive
        zip_bytes = global_project_zipper.create_zip_bytes(files, root_folder=project_name.lower().replace(" ", "_"))

        logger.info(f"ProjectAssembler assembled {len(files)} files for '{project_name}' in {assembly_time}s")

        return {
            "project_name": project_name,
            "project_files": files,
            "validation": val_result,
            "assembly_time_seconds": assembly_time,
            "zip_bytes": zip_bytes
        }


# Global ProjectAssembler Instance
global_project_assembler = ProjectAssembler()
