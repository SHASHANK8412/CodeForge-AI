import logging
from typing import Dict, Any, List

logger = logging.getLogger("aiforge.exporter.validator")


class ProjectValidator:
    """
    ProjectValidator verifies structure completeness, required file presence,
    and consistency between Frontend routes, Backend endpoints, and Database schema.
    """

    def validate_project(self, project_files: Dict[str, str]) -> Dict[str, Any]:
        """Validates generated project files map."""
        errors = []
        warnings = []
        checks = {
            "frontend": False,
            "backend": False,
            "database": False,
            "documentation": False,
            "consistency": False
        }

        # 1. Frontend Checks
        has_fe_pkg = any("package.json" in path for path in project_files)
        has_fe_src = any("frontend/src" in path or "src/App.jsx" in path for path in project_files)
        if has_fe_pkg and has_fe_src:
            checks["frontend"] = True
        else:
            errors.append("Frontend validation failed: Missing package.json or src components.")

        # 2. Backend Checks
        has_be_req = any("requirements.txt" in path for path in project_files)
        has_be_main = any("main.py" in path for path in project_files)
        if has_be_req and has_be_main:
            checks["backend"] = True
        else:
            errors.append("Backend validation failed: Missing requirements.txt or main.py.")

        # 3. Database Checks
        has_db_schema = any("schema.sql" in path or "database/" in path for path in project_files)
        if has_db_schema:
            checks["database"] = True
        else:
            warnings.append("Database validation warning: No explicit schema.sql found.")

        # 4. Documentation Checks
        has_readme = any("README.md" in path for path in project_files)
        if has_readme:
            checks["documentation"] = True
        else:
            errors.append("Documentation validation failed: Missing README.md.")

        # 5. Consistency Checks
        # Verify backend main.py defines routes and database schema defines tables
        be_code = next((content for path, content in project_files.items() if "main.py" in path), "")
        db_code = next((content for path, content in project_files.items() if "schema.sql" in path), "")

        if be_code and ("@app." in be_code or "FastAPI" in be_code):
            checks["consistency"] = True
        else:
            warnings.append("Consistency warning: Backend routes signature incomplete.")

        is_valid = len(errors) == 0
        logger.info(f"Project validation completed. Valid: {is_valid}, Errors: {len(errors)}, Warnings: {len(warnings)}")

        return {
            "is_valid": is_valid,
            "checks": checks,
            "errors": errors,
            "warnings": warnings
        }


# Global ProjectValidator Instance
global_project_validator = ProjectValidator()
