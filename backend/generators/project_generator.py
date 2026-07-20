import logging
import json
from pathlib import Path
from typing import Any

from backend.generators.dependency_generator import DependencyGenerator
from backend.generators.package_generator import PackageGenerator
from backend.generators.requirements_generator import RequirementsGenerator
from backend.generators.docker_generator import DockerGenerator
from backend.generators.compose_generator import ComposeGenerator
from backend.generators.env_generator import EnvGenerator
from backend.generators.readme_generator import ReadmeGenerator
from backend.generators.gitignore_generator import GitIgnoreGenerator
from backend.generators.license_generator import LicenseGenerator
from backend.validators.project_validator import ProjectValidator, ValidationReport
from backend.services.zip_service import ZipService
from backend.workflow.project_builder import extract_code_files
from backend.workflow.file_writer import write_project_file
from backend.config import GENERATED_PROJECTS_DIR_NAME, DEFAULT_LICENSE_TYPE

_logger = logging.getLogger("aiforge.performance")

# Base directory where all projects are exported
GENERATED_PROJECTS_DIR = Path(__file__).resolve().parent.parent.parent / GENERATED_PROJECTS_DIR_NAME


class ProjectGenerator:
    """
    Orchestrates the entire project compilation engine. It parses outputs,
    invokes sub-generators, writes structures, runs diagnostics validation,
    and packages the output into a downloadable ZIP archive.
    """

    def __init__(self) -> None:
        self.dependency_generator = DependencyGenerator()
        self.package_generator = PackageGenerator()
        self.requirements_generator = RequirementsGenerator()
        self.docker_generator = DockerGenerator()
        self.compose_generator = ComposeGenerator()
        self.env_generator = EnvGenerator()
        self.readme_generator = ReadmeGenerator()
        self.gitignore_generator = GitIgnoreGenerator()
        self.license_generator = LicenseGenerator()
        self.project_validator = ProjectValidator()
        self.zip_service = ZipService()

    def generate_project_structure(self, project_name: str, state: dict[str, Any]) -> tuple[Path, ValidationReport]:
        """
        Builds, configures, validates, and archives a complete project directory structure.
        """
        _logger.info(f"Initiating intelligent project generation engine for: {project_name}")
        GENERATED_PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

        # Normalize folder name
        safe_name = "".join([c if c.isalnum() or c in " -_" else "_" for c in project_name]).strip()
        project_dir = GENERATED_PROJECTS_DIR / safe_name
        project_dir.mkdir(parents=True, exist_ok=True)

        # 1. Create subdirectories layout
        for sub_dir in ["frontend/src/components", "backend", "database", "tests", "docs"]:
            (project_dir / sub_dir).mkdir(parents=True, exist_ok=True)

        # 2. Extract code blocks from agent outputs
        extracted_files: dict[str, str] = {}
        for key in ["frontend", "backend", "database", "tests", "documentation"]:
            extracted_files.update(extract_code_files(state.get(key, "")))

        # Write extracted files
        for rel_path, content in extracted_files.items():
            write_project_file(project_dir / rel_path, content)

        # Fallbacks check (main.py, App.jsx, schema.sql, test_app.py)
        if "backend/main.py" not in extracted_files and state.get("backend"):
            write_project_file(project_dir / "backend/main.py", state["backend"])
        if "frontend/src/App.jsx" not in extracted_files and state.get("frontend"):
            write_project_file(project_dir / "frontend/src/App.jsx", state["frontend"])
        if "database/schema.sql" not in extracted_files and state.get("database"):
            write_project_file(project_dir / "database/schema.sql", state["database"])
        if "tests/test_app.py" not in extracted_files and state.get("tests"):
            write_project_file(project_dir / "tests/test_app.py", state["tests"])

        # 3. Detect dependencies
        deps = self.dependency_generator.detect_dependencies(state)

        # 4. Generate package config files
        pkg_json = self.package_generator.generate_package_json(project_name, deps.frontend)
        write_project_file(project_dir / "package.json", pkg_json)

        req_txt = self.requirements_generator.generate_requirements(deps.backend)
        write_project_file(project_dir / "requirements.txt", req_txt)

        # 5. Generate Docker assets and deployment configurations
        if state.get("deployment_files"):
            for rel_path, content in state["deployment_files"].items():
                write_project_file(project_dir / rel_path, content)
            if state.get("deployment_guide"):
                write_project_file(project_dir / "docs/DEPLOYMENT.md", state["deployment_guide"])
        else:
            backend_df = self.docker_generator.generate_backend_dockerfile()
            write_project_file(project_dir / "backend/Dockerfile", backend_df)

            frontend_df = self.docker_generator.generate_frontend_dockerfile()
            write_project_file(project_dir / "frontend/Dockerfile", frontend_df)

            compose_yml = self.compose_generator.generate_compose(deps.database)
            write_project_file(project_dir / "docker-compose.yml", compose_yml)

            # 6. Generate configuration settings
            env_example = self.env_generator.generate_env_example(deps.database)
            write_project_file(project_dir / ".env.example", env_example)

        # 7. Core project files (.gitignore, LICENSE, plan.md, architecture.md, review.md)
        gitignore_content = self.gitignore_generator.generate_gitignore()
        write_project_file(project_dir / ".gitignore", gitignore_content)

        license_content = self.license_generator.generate_license(DEFAULT_LICENSE_TYPE)
        write_project_file(project_dir / "LICENSE", license_content)

        if state.get("plan"):
            write_project_file(project_dir / "plan.md", state["plan"])
            write_project_file(project_dir / "docs/plan.md", state["plan"])
        if state.get("architecture"):
            write_project_file(project_dir / "architecture.md", state["architecture"])
            write_project_file(project_dir / "docs/architecture.md", state["architecture"])
        if state.get("review"):
            write_project_file(project_dir / "review.md", state["review"])

        # 8. Generate README
        readme_md = self.readme_generator.generate_readme(project_name, state)
        write_project_file(project_dir / "README.md", readme_md)

        # 9. Diagnostic Validation
        report = self.project_validator.validate_project(project_dir)

        # 10. Package to ZIP Archive
        zip_output_path = GENERATED_PROJECTS_DIR / f"{safe_name}.zip"
        self.zip_service.zip_project(project_dir, zip_output_path)

        _logger.info("Project exported successfully")
        return project_dir, report
