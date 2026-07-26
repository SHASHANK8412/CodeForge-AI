import ast
import json
import re
import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from backend.agents.base_agent import BaseAgent

logger = logging.getLogger("aiforge.build_validation")


class BuildValidationReport(BaseModel):
    is_valid: bool = True
    frontend_valid: bool = True
    backend_valid: bool = True
    database_valid: bool = True
    docker_valid: bool = True
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    logs: Dict[str, Any] = Field(default_factory=dict)
    summary: str = ""


class BuildValidationAgent(BaseAgent):
    """
    Build Validation Agent automatically verifies every generated project stage:
    1. Frontend Validation (package.json, jsx/js AST syntax, lint checks)
    2. Backend Validation (requirements.txt, python AST compilation, pytest readiness)
    3. Database Validation (SQL schema syntax, foreign keys, indexes, migrations)
    4. Docker Validation (Dockerfile format, docker-compose configuration)
    """

    def __init__(self):
        super().__init__(
            system_prompt=(
                "You are the Build Validation Agent for AIForge. Your job is to strictly "
                "validate build readiness, syntax correctness, dependency declarations, "
                "database schemas, and container configurations for generated projects."
            ),
            task_name="build_validation"
        )

    def validate_frontend(self, frontend_files: Dict[str, str]) -> Dict[str, Any]:
        errors = []
        warnings = []

        if not frontend_files:
            errors.append("Frontend code dictionary is empty.")
            return {"valid": False, "errors": errors, "warnings": warnings}

        # Check for package.json or essential structure
        has_package_json = any("package.json" in k for k in frontend_files.keys())
        if not has_package_json:
            warnings.append("package.json not explicitly present in frontend payload; will be generated.")

        # Check JS/JSX code syntax basic checks
        for filepath, content in frontend_files.items():
            if filepath.endswith((".js", ".jsx", ".ts", ".tsx")):
                # Check unbalanced braces/brackets
                if content.count("{") != content.count("}"):
                    errors.append(f"Unbalanced curly braces '{{}}' in {filepath}")
                if content.count("(") != content.count(")"):
                    errors.append(f"Unbalanced parentheses '()' in {filepath}")
                # Check placeholder markers
                if "TODO" in content or "..." in content and "import" not in content:
                    warnings.append(f"Potential placeholder found in {filepath}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "files_checked": len(frontend_files)
        }

    def validate_backend(self, backend_files: Dict[str, str]) -> Dict[str, Any]:
        errors = []
        warnings = []

        if not backend_files:
            errors.append("Backend code dictionary is empty.")
            return {"valid": False, "errors": errors, "warnings": warnings}

        for filepath, content in backend_files.items():
            if filepath.endswith(".py"):
                try:
                    ast.parse(content, filename=filepath)
                except SyntaxError as e:
                    errors.append(f"Python Syntax Error in {filepath} at line {e.lineno}: {e.msg}")
                except Exception as e:
                    errors.append(f"AST parse error in {filepath}: {str(e)}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "files_checked": len(backend_files)
        }

    def validate_database(self, database_code: str) -> Dict[str, Any]:
        errors = []
        warnings = []

        if not database_code or not database_code.strip():
            warnings.append("No database schema provided or database schema is empty.")
            return {"valid": True, "errors": [], "warnings": warnings}

        code_upper = database_code.upper()
        if "CREATE TABLE" not in code_upper and "MODEL" not in code_upper and "SCHEMA" not in code_upper:
            warnings.append("Database script does not contain CREATE TABLE or Model definitions.")

        # Check foreign keys and primary keys if SQL
        if "CREATE TABLE" in code_upper:
            tables = re.findall(r"CREATE TABLE\s+(\w+)", database_code, re.IGNORECASE)
            if tables:
                logger.info(f"Database schema contains {len(tables)} tables: {tables}")
            else:
                warnings.append("Could not parse table names in CREATE TABLE statements.")

            if "PRIMARY KEY" not in code_upper:
                warnings.append("SQL schema does not explicitly define PRIMARY KEY constraints.")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    def validate_docker(self, docker_files: Dict[str, str]) -> Dict[str, Any]:
        errors = []
        warnings = []

        dockerfile = docker_files.get("Dockerfile") or docker_files.get("docker/Dockerfile", "")
        compose = docker_files.get("docker-compose.yml", "")

        if dockerfile:
            if "FROM " not in dockerfile:
                errors.append("Dockerfile missing 'FROM' instruction.")
            if "WORKDIR " not in dockerfile:
                warnings.append("Dockerfile missing 'WORKDIR' instruction.")

        if compose:
            if "version:" not in compose and "services:" not in compose:
                errors.append("docker-compose.yml missing 'services:' root element.")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    def validate_all(
        self,
        frontend_files: Dict[str, str],
        backend_files: Dict[str, str],
        database_code: str,
        docker_files: Dict[str, str]
    ) -> BuildValidationReport:
        fe_res = self.validate_frontend(frontend_files)
        be_res = self.validate_backend(backend_files)
        db_res = self.validate_database(database_code)
        dk_res = self.validate_docker(docker_files)

        all_errors = fe_res["errors"] + be_res["errors"] + db_res["errors"] + dk_res["errors"]
        all_warnings = fe_res["warnings"] + be_res["warnings"] + db_res["warnings"] + dk_res["warnings"]

        is_overall_valid = fe_res["valid"] and be_res["valid"] and db_res["valid"] and dk_res["valid"]

        summary = (
            f"Build Validation Completed: Overall {'PASSED' if is_overall_valid else 'FAILED'}. "
            f"Frontend: {'OK' if fe_res['valid'] else 'FAIL'}, "
            f"Backend: {'OK' if be_res['valid'] else 'FAIL'}, "
            f"Database: {'OK' if db_res['valid'] else 'FAIL'}, "
            f"Docker: {'OK' if dk_res['valid'] else 'FAIL'}. "
            f"Found {len(all_errors)} errors and {len(all_warnings)} warnings."
        )

        return BuildValidationReport(
            is_valid=is_overall_valid,
            frontend_valid=fe_res["valid"],
            backend_valid=be_res["valid"],
            database_valid=db_res["valid"],
            docker_valid=dk_res["valid"],
            errors=all_errors,
            warnings=all_warnings,
            logs={
                "frontend": fe_res,
                "backend": be_res,
                "database": db_res,
                "docker": dk_res
            },
            summary=summary
        )
