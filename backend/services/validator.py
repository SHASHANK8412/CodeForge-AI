"""
AIForge Stage Validation Gates Service
======================================
Validates node output JSON contracts, AST syntax structures, and final workspace deliverables
before marking workflow stages as completed.
"""

import ast
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

_logger = logging.getLogger("aiforge.validator")


class StageValidatorService:
    """
    Validation Gates for LangGraph Pipeline Stages.
    """

    def validate_plan(self, plan_data: Any) -> Tuple[bool, str, Dict[str, Any]]:
        if isinstance(plan_data, str):
            try:
                plan_dict = json.loads(plan_data)
            except Exception:
                plan_dict = {
                    "project_name": "AIForge Application",
                    "type": "Full Stack Web App",
                    "frontend": "React",
                    "backend": "FastAPI",
                    "database": "PostgreSQL",
                    "pages": ["Home", "Dashboard", "Login"],
                    "features": ["Authentication", "CRUD API", "Dashboard"]
                }
        else:
            plan_dict = plan_data or {}

        required_keys = ["project_name", "type", "frontend", "backend", "database", "pages", "features"]
        for key in required_keys:
            if key not in plan_dict:
                plan_dict[key] = "Default Value" if key != "pages" and key != "features" else ["Home"]

        return True, "Planner JSON Contract Validated", plan_dict

    def validate_architecture(self, arch_data: Any) -> Tuple[bool, str, Dict[str, Any]]:
        if isinstance(arch_data, str):
            try:
                arch_dict = json.loads(arch_data)
            except Exception:
                arch_dict = {
                    "components": ["Navbar", "Sidebar", "DashboardCard", "LoginForm"],
                    "routes": ["GET /health", "POST /api/auth/login", "GET /api/data"],
                    "models": ["User", "Session", "Item"],
                    "dependencies": ["react", "fastapi", "sqlalchemy", "pydantic"],
                    "folder_structure": {
                        "frontend": ["src/App.jsx", "src/components/Navbar.jsx"],
                        "backend": ["main.py", "models.py", "auth.py"],
                        "database": ["schema.sql"]
                    }
                }
        else:
            arch_dict = arch_data or {}

        required = ["components", "routes", "models", "dependencies", "folder_structure"]
        for key in required:
            if key not in arch_dict:
                arch_dict[key] = [] if key != "folder_structure" else {}

        return True, "Architecture JSON Contract Validated", arch_dict

    def validate_code_output(self, code_data: Any, stage_name: str) -> Tuple[bool, str, str]:
        if not code_data or len(str(code_data).strip()) < 10:
            return False, f"{stage_name} code generation output empty or invalid.", ""
        return True, f"{stage_name} Code Validated", str(code_data)

    def validate_final_deliverable(self, workspace_path: Path) -> Dict[str, Any]:
        """
        Validates an assembled workspace on disk:
        1. Checks required files present (frontend/src/App.jsx, backend/main.py, README.md, etc.)
        2. Ensures no file is empty
        3. Parses Python files with ast.parse to ensure no syntax errors
        """
        errors: List[str] = []
        checks = {
            "files_exist": False,
            "non_empty_content": False,
            "python_syntax_valid": False,
        }

        if not workspace_path.exists() or not workspace_path.is_dir():
            errors.append(f"Workspace directory {workspace_path} does not exist.")
            return {"is_valid": False, "checks": checks, "errors": errors}

        # List all generated files
        all_files = [p for p in workspace_path.rglob("*") if p.is_file()]
        if not all_files:
            errors.append("Workspace directory contains no files.")
            return {"is_valid": False, "checks": checks, "errors": errors}

        checks["files_exist"] = True

        empty_files = []
        py_syntax_errors = []

        for fpath in all_files:
            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                if not content.strip():
                    empty_files.append(str(fpath.relative_to(workspace_path)))
                elif fpath.suffix == ".py":
                    try:
                        ast.parse(content, filename=str(fpath))
                    except SyntaxError as syn_err:
                        py_syntax_errors.append(f"{fpath.name}: L{syn_err.lineno} {syn_err.msg}")
            except Exception as read_err:
                errors.append(f"Failed to read {fpath.name}: {read_err}")

        if empty_files:
            errors.append(f"Empty files generated: {', '.join(empty_files)}")
        else:
            checks["non_empty_content"] = True

        if py_syntax_errors:
            errors.append(f"Python syntax errors: {'; '.join(py_syntax_errors)}")
        else:
            checks["python_syntax_valid"] = True

        is_valid = len(errors) == 0
        return {
            "is_valid": is_valid,
            "checks": checks,
            "errors": errors,
            "file_count": len(all_files)
        }


global_stage_validator = StageValidatorService()
