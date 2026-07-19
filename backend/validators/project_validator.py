import json
import logging
from pathlib import Path
from dataclasses import dataclass, field

_logger = logging.getLogger("aiforge.performance")

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


@dataclass
class ValidationReport:
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    files_checked: list[str] = field(default_factory=list)


class ProjectValidator:
    """
    Performs structural, code import, dependency, and configuration syntax validation
    on the assembled project directory, returning diagnostic reports.
    """

    def __init__(self) -> None:
        pass

    def validate_project(self, project_path: Path) -> ValidationReport:
        """
        Validates the compiled files in the project folder.
        """
        _logger.info(f"Validating project structure at: {project_path}")
        errors: list[str] = []
        warnings: list[str] = []
        files_checked: list[str] = []

        if not project_path.exists():
            errors.append(f"Project directory does not exist: {project_path}")
            return ValidationReport(is_valid=False, errors=errors, warnings=warnings)

        # 1. Directory Tree & Key Files Verification
        required_dirs = ["frontend", "backend", "database", "tests"]
        for r_dir in required_dirs:
            p = project_path / r_dir
            if not p.exists() or not p.is_dir():
                errors.append(f"Missing required subdirectory: {r_dir}/")
            else:
                files_checked.append(r_dir)

        required_files = [
            "README.md", "package.json", "requirements.txt",
            "frontend/Dockerfile", "backend/Dockerfile", "docker-compose.yml",
            ".env.example", ".gitignore", "LICENSE"
        ]

        for r_file in required_files:
            p = project_path / r_file
            if not p.exists():
                errors.append(f"Missing required file: {r_file}")
            else:
                files_checked.append(r_file)
                # Check for empty files
                if p.stat().st_size == 0:
                    warnings.append(f"File is empty: {r_file}")

        # 2. package.json validation
        pkg_path = project_path / "package.json"
        npm_packages = set()
        if pkg_path.exists() and pkg_path.stat().st_size > 0:
            try:
                with open(pkg_path, "r", encoding="utf-8") as f:
                    pkg_data = json.load(f)
                files_checked.append("package.json (JSON Syntax)")

                # Verify package keys
                for key in ["name", "version", "dependencies"]:
                    if key not in pkg_data:
                        errors.append(f"package.json missing key: '{key}'")
                
                # Check duplicate dependency overlap
                if "dependencies" in pkg_data and "devDependencies" in pkg_data:
                    overlap = set(pkg_data["dependencies"].keys()) & set(pkg_data["devDependencies"].keys())
                    for pkg in overlap:
                        warnings.append(f"package.json has duplicate dependency '{pkg}' in both dependencies and devDependencies")

                # Gather deps
                if "dependencies" in pkg_data:
                    npm_packages = set(pkg_data["dependencies"].keys())

            except json.JSONDecodeError as exc:
                errors.append(f"package.json contains invalid JSON: {exc}")

        # 3. requirements.txt validation
        req_path = project_path / "requirements.txt"
        pip_packages = set()
        if req_path.exists() and req_path.stat().st_size > 0:
            try:
                with open(req_path, "r", encoding="utf-8") as f:
                    req_content = f.read()
                files_checked.append("requirements.txt")
                
                seen_reqs = {}
                for line_no, line in enumerate(req_content.splitlines(), 1):
                    line_clean = line.strip()
                    if line_clean and not line_clean.startswith("#"):
                        # E.g. fastapi>=0.100.0 -> fastapi
                        name = line_clean.split(">")[0].split("<")[0].split("=")[0].strip().lower()
                        if name in seen_reqs:
                            warnings.append(f"requirements.txt contains duplicate dependency: '{name}' (line {line_no} duplicates line {seen_reqs[name]})")
                        else:
                            seen_reqs[name] = line_no
                        pip_packages.add(name)
            except Exception as exc:
                errors.append(f"Failed to read requirements.txt: {exc}")

        # 4. docker-compose.yml validation
        compose_path = project_path / "docker-compose.yml"
        if compose_path.exists() and compose_path.stat().st_size > 0:
            if HAS_YAML:
                try:
                    with open(compose_path, "r", encoding="utf-8") as f:
                        yaml.safe_load(f)
                    files_checked.append("docker-compose.yml (YAML Syntax)")
                except Exception as exc:
                    errors.append(f"docker-compose.yml contains invalid YAML: {exc}")
            else:
                # Basic check if pyyaml is missing
                warnings.append("YAML validator skipped (pyyaml not installed in environment)")

        # 5. Dockerfiles basic syntax checks
        for df_rel in ["frontend/Dockerfile", "backend/Dockerfile"]:
            df_path = project_path / df_rel
            if df_path.exists() and df_path.stat().st_size > 0:
                try:
                    with open(df_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    files_checked.append(df_rel)
                    
                    has_from = any(line.strip().upper().startswith("FROM") for line in lines)
                    if not has_from:
                        errors.append(f"{df_rel} is invalid: missing 'FROM' instruction")
                except Exception as exc:
                    errors.append(f"Failed to validate Dockerfile {df_rel}: {exc}")

        # 6. Broken imports / dependencies validation
        # Validate Python imports under backend/main.py or backend files
        backend_main = project_path / "backend/main.py"
        if backend_main.exists() and backend_main.stat().st_size > 0:
            try:
                from backend.generators.dependency_generator import DependencyGenerator
                dep_gen = DependencyGenerator()
                with open(backend_main, "r", encoding="utf-8") as f:
                    main_code = f.read()
                
                # Detect what imports are used
                detected_pip = dep_gen._parse_backend_imports(main_code)
                for pip_dep in detected_pip:
                    base_name = pip_dep.split(">")[0].split("<")[0].split("=")[0].strip().lower()
                    if base_name not in pip_packages and base_name not in {"uvicorn", "fastapi"}:
                        warnings.append(
                            f"Python file backend/main.py imports '{pip_dep}' which is not explicitly defined in requirements.txt"
                        )
            except Exception as exc:
                warnings.append(f"Broken import validation skipped: {exc}")

        is_valid = len(errors) == 0
        if is_valid:
            _logger.info("Validation passed successfully")
        else:
            _logger.warning(f"Validation failed with {len(errors)} errors")

        return ValidationReport(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            files_checked=files_checked
        )
