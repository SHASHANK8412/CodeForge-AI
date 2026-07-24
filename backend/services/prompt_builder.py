"""
AIForge Context Scoper & Minimal Prompt Builder
==============================================
Constructs minimal, role-scoped prompts to prevent token inflation and context pollution:
- Planner gets: user_prompt
- Architect gets: plan JSON
- Frontend gets: architecture JSON
- Backend gets: architecture JSON
- Database gets: architecture JSON
- Reviewer gets: generated code files
- Testing gets: backend & frontend code files
- Documentation gets: plan & architecture JSON
"""

import json
import logging
from typing import Dict, Any, Optional

_logger = logging.getLogger("aiforge.prompt_builder")


class ContextScopedPromptBuilder:
    """
    Minimal Prompt Builder for specialized multi-agent execution.
    """

    def build_planner_prompt(self, user_prompt: str) -> str:
        return (
            f"Analyze user requirements and return ONLY a valid JSON object matching this schema:\n"
            f'{{"project_name": "Name", "type": "Full Stack Web App", "frontend": "React", "backend": "FastAPI", '
            f'"database": "PostgreSQL", "pages": ["Home", "Dashboard"], "features": ["Auth", "API"]}}\n\n'
            f"User Prompt: {user_prompt}"
        )

    def build_architect_prompt(self, plan_json: Dict[str, Any]) -> str:
        return (
            f"Design system architecture JSON based on this Plan JSON:\n"
            f"{json.dumps(plan_json, indent=2)}\n\n"
            f"Return ONLY valid JSON matching: {{\x22components\x22: [], \x22routes\x22: [], \x22models\x22: [], \x22dependencies\x22: [], \x22folder_structure\x22: {{}}}}"
        )

    def build_frontend_prompt(self, arch_json: Dict[str, Any]) -> str:
        components = arch_json.get("components", ["Navbar", "DashboardCard"])
        return f"Generate React (Vite + TailwindCSS) source code for components: {components}"

    def build_backend_prompt(self, arch_json: Dict[str, Any]) -> str:
        routes = arch_json.get("routes", ["GET /health", "POST /api/auth"])
        return f"Generate FastAPI source code for REST routes: {routes}"

    def build_database_prompt(self, arch_json: Dict[str, Any]) -> str:
        models = arch_json.get("models", ["User", "Session"])
        return f"Generate PostgreSQL SQL schema and SQLAlchemy models for entities: {models}"

    def build_reviewer_prompt(self, generated_files: Dict[str, str]) -> str:
        file_summary = list(generated_files.keys())
        return f"Review generated project files: {file_summary}"

    def build_testing_prompt(self, backend_code: str, frontend_code: str) -> str:
        return f"Generate Pytest unit tests for Backend:\n{backend_code[:500]}\nand React Testing Library tests for Frontend."


global_prompt_builder = ContextScopedPromptBuilder()
