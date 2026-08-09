"""
AIForge Context Scoper & Minimal Prompt Builder
==============================================
Constructs role-scoped prompts augmented with RAG retrieved context from uploaded PRDs and documentation:
- Planner gets: user_prompt + RAG retrieved PRD context
- Architect gets: plan JSON + RAG retrieved architecture requirements
- Frontend gets: architecture JSON + RAG retrieved UI specs
- Backend gets: architecture JSON + RAG retrieved API & Auth specs
- Database gets: architecture JSON + RAG retrieved DB schemas
"""

import json
import logging
from typing import Dict, Any, Optional
from backend.rag.pipeline import global_rag_pipeline

_logger = logging.getLogger("aiforge.prompt_builder")


class ContextScopedPromptBuilder:
    """
    Minimal Prompt Builder for specialized multi-agent execution with RAG document context injection.
    """

    def build_planner_prompt(self, user_prompt: str) -> str:
        rag_context = global_rag_pipeline.get_context_string_for_agent("planner", user_prompt)
        context_prefix = f"{rag_context}\n\n" if rag_context else ""
        return (
            f"{context_prefix}"
            f"Analyze user requirements and return ONLY a valid JSON object matching this schema:\n"
            f'{{"project_name": "Name", "type": "Full Stack Web App", "frontend": "React", "backend": "FastAPI", '
            f'"database": "PostgreSQL", "pages": ["Home", "Dashboard"], "features": ["Auth", "API"]}}\n\n'
            f"User Prompt: {user_prompt}"
        )

    def build_architect_prompt(self, plan_json: Dict[str, Any]) -> str:
        proj_name = plan_json.get("project_name", "") if isinstance(plan_json, dict) else ""
        rag_context = global_rag_pipeline.get_context_string_for_agent("architect", f"{proj_name} architecture design")
        context_prefix = f"{rag_context}\n\n" if rag_context else ""
        return (
            f"{context_prefix}"
            f"Design system architecture JSON based on this Plan JSON:\n"
            f"{json.dumps(plan_json, indent=2)}\n\n"
            f"Return ONLY valid JSON matching: {{\x22components\x22: [], \x22routes\x22: [], \x22models\x22: [], \x22dependencies\x22: [], \x22folder_structure\x22: {{}}}}"
        )

    def build_frontend_prompt(self, arch_json: Dict[str, Any]) -> str:
        components = arch_json.get("components", ["Navbar", "DashboardCard"]) if isinstance(arch_json, dict) else ["Navbar"]
        rag_context = global_rag_pipeline.get_context_string_for_agent("frontend", f"React UI {components}")
        context_prefix = f"{rag_context}\n\n" if rag_context else ""
        return f"{context_prefix}Generate React (Vite + TailwindCSS) source code for components: {components}"

    def build_backend_prompt(self, arch_json: Dict[str, Any]) -> str:
        routes = arch_json.get("routes", ["GET /health", "POST /api/auth"]) if isinstance(arch_json, dict) else ["GET /health"]
        rag_context = global_rag_pipeline.get_context_string_for_agent("backend", f"FastAPI REST routes {routes}")
        context_prefix = f"{rag_context}\n\n" if rag_context else ""
        return f"{context_prefix}Generate FastAPI source code for REST routes: {routes}"

    def build_database_prompt(self, arch_json: Dict[str, Any]) -> str:
        models = arch_json.get("models", ["User", "Session"]) if isinstance(arch_json, dict) else ["User"]
        rag_context = global_rag_pipeline.get_context_string_for_agent("database", f"Database models {models}")
        context_prefix = f"{rag_context}\n\n" if rag_context else ""
        return f"{context_prefix}Generate PostgreSQL SQL schema and SQLAlchemy models for entities: {models}"

    def build_reviewer_prompt(
        self,
        frontend_code: str = "",
        backend_code: str = "",
        database_code: str = "",
        duplicate_report: Optional[Dict[str, Any]] = None,
    ) -> str:
        duplicate_report = duplicate_report or {}
        duplicate_count = duplicate_report.get("duplicate_count", 0)
        duplicate_files = [
            entry.get("files", []) for entry in duplicate_report.get("duplicates", [])
        ]
        duplicate_summary = (
            f"{duplicate_count} duplicate code block(s) already detected across: {duplicate_files}"
            if duplicate_count
            else "No duplicate code blocks detected by the automated scanner."
        )
        return (
            "Review the following real generated project source code.\n\n"
            f"Automated Duplicate Scan Result\n{duplicate_summary}\n"
            "Reference this scan instead of re-deriving duplicate findings yourself.\n\n"
            f"Frontend Code\n{frontend_code[:1500] or '(none generated)'}\n\n"
            f"Backend Code\n{backend_code[:1500] or '(none generated)'}\n\n"
            f"Database Code\n{database_code[:1500] or '(none generated)'}"
        )

    def build_testing_prompt(self, backend_code: str, frontend_code: str) -> str:
        return (
            f"Backend Code\n{backend_code[:1500] or '(none generated)'}\n\n"
            f"Frontend Code\n{frontend_code[:1500] or '(none generated)'}"
        )


global_prompt_builder = ContextScopedPromptBuilder()
