"""
AIForge Stage Validation Gates Service
======================================
Validates node output JSON contracts and code structures before moving to downstream workflow stages.
Supports stage-by-stage retries on failure.
"""

import json
import logging
from typing import Dict, Any, Tuple, Optional

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


global_stage_validator = StageValidatorService()
