"""
AIForge Context Scoper & Prompt Builder
=======================================
Role-scoped prompts for the generation pipeline, each augmented with RAG context from uploaded
documents. Every code agent gets the same project brief (name, requirements, features) and the
architecture contract (routes, models, components, files parsed from the architect's output),
plus a file-layout contract and the exact output format the extractor reads, so the agents'
files fit together: one owner per file, imports only of files that exist.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from backend.rag.pipeline import global_rag_pipeline

_logger = logging.getLogger("aiforge.prompt_builder")

OUTPUT_FORMAT = (
    "Output format - each file as a `### <path>` line followed by one fenced block with the "
    "complete file (this works for every file type, including JSON):\n"
    "### backend/main.py\n```python\n<complete file>\n```\n"
    "No prose between files, no placeholders, no TODOs."
)

def _template(template_id: Optional[str]) -> Dict[str, Any]:
    from backend.generation.templates import get_template
    return get_template(template_id)


def _stack(template_id: Optional[str]) -> str:
    stack = _template(template_id)["stack"]
    return "Stack: " + ", ".join(f"{k} {v}" for k, v in stack.items())


def _brief(plan: Optional[Dict[str, Any]]) -> str:
    """Project brief from the planner's spec: only the fields it actually filled in."""
    plan = plan if isinstance(plan, dict) else {}
    lines = [f"Project: {plan.get('project_name') or 'the application'}"]
    if plan.get("executive_summary"):
        lines.append(f"Summary: {plan['executive_summary']}")
    reqs = plan.get("functional_requirements") or plan.get("requirements") or []
    if reqs:
        lines.append("Requirements:\n" + "\n".join(f"- {r}" for r in reqs[:20]))
    if plan.get("features"):
        lines.append("Features: " + ", ".join(map(str, plan["features"][:20])))
    if plan.get("pages"):
        lines.append("Pages: " + ", ".join(map(str, plan["pages"][:12])))
    return "\n".join(lines)


def _bullets(items: List[Any], empty: str) -> str:
    return "\n".join(f"- {i}" for i in items) if items else f"- ({empty})"


def _context(agent: str, query: str) -> str:
    rag = global_rag_pipeline.get_context_string_for_agent(agent, query)
    return f"{rag}\n\n" if rag else ""


class ContextScopedPromptBuilder:
    """
    Prompt builder for the specialized agents of the generation pipeline.
    """

    def build_planner_prompt(self, user_prompt: str) -> str:
        return (
            f"{_context('planner', user_prompt)}"
            f"Analyze user requirements and return ONLY a valid JSON object matching this schema:\n"
            f'{{"project_name": "Name", "type": "Full Stack Web App", "frontend": "React", "backend": "FastAPI", '
            f'"database": "PostgreSQL", "pages": ["Home", "Dashboard"], "features": ["Auth", "API"]}}\n\n'
            f"User Prompt: {user_prompt}"
        )

    def build_architect_prompt(self, plan_json: Dict[str, Any], template: Optional[str] = None) -> str:
        plan_json = plan_json if isinstance(plan_json, dict) else {}
        proj_name = plan_json.get("project_name", "")
        # The architect writes Markdown sections (its system prompt); the API Specifications,
        # Database Schema and Folder Structure sections become the code agents' contract, so
        # they must be concrete: `METHOD /path` lines, one top-level bullet per table, file paths.
        return (
            f"{_context('architect', f'{proj_name} architecture design')}"
            f"Design the architecture for this plan:\n{json.dumps(plan_json, indent=2)}\n{_stack(template)}\n\n"
            "Write the Markdown sections from your instructions. Be concrete where the code agents "
            "will build from them:\n"
            "- API Specifications: one endpoint per line as `METHOD /path` - purpose\n"
            "- Database Schema: one top-level bullet per table (`- **table**: field (type), ...`)\n"
            "- Folder Structure: real file paths such as backend/main.py and frontend/src/components/X.jsx\n"
            "List only the components, routes and models this project needs."
        )

    def build_backend_prompt(self, arch_json: Dict[str, Any], plan: Optional[Dict[str, Any]] = None,
                             template: Optional[str] = None) -> str:
        arch_json = arch_json if isinstance(arch_json, dict) else {}
        routes, models = arch_json.get("routes", []), arch_json.get("models", [])
        return (
            f"{_context('backend', f'FastAPI REST routes {routes}')}"
            f"{_brief(plan)}\n{_stack(template)}\n\n"
            f"Build the backend.\nAPI endpoints to implement:\n{_bullets(routes, 'derive them from the requirements')}\n"
            f"Data models:\n{_bullets(models, 'derive them from the requirements')}\n\n"
            f"File layout (other agents rely on it):\n{_template(template)['backend_layout']}\n\n{OUTPUT_FORMAT}"
        )

    def build_frontend_prompt(self, arch_json: Dict[str, Any], plan: Optional[Dict[str, Any]] = None,
                              template: Optional[str] = None) -> str:
        arch_json = arch_json if isinstance(arch_json, dict) else {}
        components, routes = arch_json.get("components", []), arch_json.get("routes", [])
        return (
            f"{_context('frontend', f'React UI {components}')}"
            f"{_brief(plan)}\n{_stack(template)}\n\n"
            f"Build the frontend.\nComponents:\n{_bullets(components, 'choose the components the pages need')}\n"
            f"Backend API endpoints available:\n{_bullets(routes, 'none listed - keep data local')}\n\n"
            f"File layout:\n{_template(template)['frontend_layout']}\n\n{OUTPUT_FORMAT}"
        )

    def build_database_prompt(self, arch_json: Dict[str, Any], plan: Optional[Dict[str, Any]] = None,
                              template: Optional[str] = None) -> str:
        arch_json = arch_json if isinstance(arch_json, dict) else {}
        models = arch_json.get("models", [])
        return (
            f"{_context('database', f'Database models {models}')}"
            f"{_brief(plan)}\n{_stack(template)}\n\n"
            f"Write the data schema for these entities:\n{_bullets(models, 'derive them from the requirements')}\n\n"
            + ("Write exactly one file, database/schema.md: each collection with its fields, types, "
               "indexes and references. The backend owns the Mongoose models, so do not write code.\n\n"
               if "Mongo" in _template(template)["stack"]["database"] else
               "Write exactly one file, database/schema.sql: CREATE TABLE statements (portable SQL that "
               "runs on SQLite and PostgreSQL), primary and foreign keys, and useful indexes. The "
               "backend owns the ORM models, so do not write application code.\n\n") + OUTPUT_FORMAT
        )

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

    def build_testing_prompt(self, backend_code: str, frontend_code: str,
                             files: Optional[Dict[str, str]] = None, max_chars: int = 9000,
                             template: Optional[str] = None) -> str:
        """
        Tests are written against the assembled backend files (all of them, up to max_chars),
        not the first 1500 characters of one agent's raw reply.
        """
        python_backend = "Python" in _template(template)["stack"]["backend"]
        source_ext = (".py",) if python_backend else (".js", ".mjs", ".ts")
        backend_files = {p: c for p, c in (files or {}).items()
                         if p.endswith(source_ext) and not p.startswith(("tests/", "frontend/")) and "/test" not in p}
        if backend_files:
            shown, used = [], 0
            for path, content in sorted(backend_files.items(), key=lambda kv: (kv[0] != "backend/main.py", kv[0])):
                block = f"### {path}\n```\n{content}\n```"
                if used + len(block) > max_chars:
                    shown.append(f"### {path}\n(omitted: {len(content)} characters)")
                    continue
                shown.append(block)
                used += len(block)
            code = "\n\n".join(shown)
        else:
            code = f"Backend Code\n{backend_code[:max_chars] or '(none generated)'}"
        return (
            f"{code}\n\n"
            f"Write tests for this backend. {_template(template)['test_instructions']} Only call endpoints "
            "and import names that exist in the code above; assert on the status codes and JSON the code "
            "actually returns. Each test must be independent (create the data it needs).\n\n"
            f"Frontend (for context only):\n{frontend_code[:1500] or '(none generated)'}"
        )


global_prompt_builder = ContextScopedPromptBuilder()
