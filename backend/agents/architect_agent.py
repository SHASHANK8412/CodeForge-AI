import json
import re
import logging
from typing import Dict, Any, List, Optional
from backend.agents.base_agent import BaseAgent
from backend.schemas.agent_contract import ArchitectureSpec

_logger = logging.getLogger("aiforge.architect_agent")


class ArchitectAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            """
You are the Chief Software Architect of AIForge, continuing the technical design after the
Planner's requirements report (executive summary, functional/non-functional requirements,
user stories, domain, and recommended tech stack) has already been produced. Do NOT repeat
that report — expand it into an execution-ready technical architecture and delivery plan that
downstream AI agents (Backend, Frontend, Database, Testing, Deployment) can consume directly,
with zero additional clarification. Prioritize scalability, maintainability, and security.

Produce EXACTLY these 11 sections, in this order, using Markdown `##` headings:

## 10. High-Level Architecture
Name the architecture style (monolith, modular monolith, microservices) and list the major
components/services and how they communicate (e.g. client -> API -> DB).

## 11. Database Schema
For each core entity/table: name, key fields with types, and relationships (foreign keys).
Use compact bullets, one table per bullet group.

## 12. API Specifications
Core REST endpoints grouped by resource: `METHOD /path — one-line purpose`.

## 13. Folder Structure
A tree-style listing of top-level project folders/files for frontend and backend.

## 14. Development Roadmap
Ordered delivery milestones (M0 Setup, M1 Core Backend, M2 Frontend, M3 Integration, M4
Launch, ...) with a one-line goal each.

## 15. Task Breakdown
Numbered concrete engineering tasks derived from the roadmap, each tagged with the responsible
agent: Backend, Frontend, Database, Testing, or Deployment.

## 16. Dependency Graph
Each task's direct prerequisites, one line each, e.g. `frontend depends_on: backend, database`.

## 17. Risk Analysis
Bullets in the form: `Risk — Severity (Low/Medium/High) — Mitigation`.

## 18. Cost & Resource Estimation
Rough team size/roles needed and an infra cost tier for MVP scale (e.g. managed Postgres +
serverless backend, $/month range).

## 19. Testing Strategy
Bullets covering unit, integration, and end-to-end testing approach and tooling.

## 20. Deployment Strategy
Bullets covering CI/CD, environments (dev/staging/prod), hosting choice, and rollback approach.

Rules:
- Be concrete: name real tables, real endpoints, real folder names — never placeholders.
- No code. Use bullets, short trees, and one-line tables, not paragraphs. Keep each section
  under ~80 words.
- End the response with one fenced ```json code block — nothing after it — containing a
  machine-readable summary in exactly this shape (omit a field only if genuinely not
  applicable):

```json
{
  "architecture_style": "",
  "components": [""],
  "database_schema": [{"table": "", "fields": [""], "relationships": [""]}],
  "api_endpoints": [{"method": "", "path": "", "purpose": ""}],
  "folder_structure": {"frontend": [""], "backend": [""]},
  "roadmap": [{"milestone": "", "goal": ""}],
  "tasks": [{"task": "", "agent": ""}],
  "dependency_graph": {"task_name": ["depends_on"]},
  "risks": [{"risk": "", "severity": "", "mitigation": ""}],
  "cost_estimate": "",
  "testing_strategy": [""],
  "deployment_strategy": [""]
}
```

- The JSON must be syntactically valid and must match the Markdown content above.
""",
        task_name="architect",
        )

    def run(self, plan: str, memory_context: str = "", previous_output: str = ""):
        return super().run(plan, memory_context, previous_output)

    async def run_async(self, plan: str, memory_context: str = "", previous_output: str = ""):
        return await super().run_async(plan, memory_context, previous_output)

    def parse_architecture_json(self, raw_output: str, allow_fallback: bool = False) -> Dict[str, Any]:
        """
        Extracts JSON code block from LLM output, parses via json.loads,
        and validates schema via Pydantic ArchitectureSpec.
        Raises ValueError on malformed/invalid JSON unless allow_fallback=True.
        """
        if not raw_output or not isinstance(raw_output, str):
            if not allow_fallback:
                raise ValueError("Empty or non-string output received from ArchitectAgent.")
            _logger.warning("Empty output passed to parse_architecture_json. Returning default spec.")
            return ArchitectureSpec().model_dump()

        extracted_json_str = ""
        # 1. Regex search used ONLY to locate fenced JSON block ```json ... ```
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_output, re.IGNORECASE)
        if json_match:
            extracted_json_str = json_match.group(1).strip()
        else:
            # 2. Substring search fallback for first { and last }
            first_brace = raw_output.find("{")
            last_brace = raw_output.rfind("}")
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                extracted_json_str = raw_output[first_brace:last_brace + 1].strip()

        if not extracted_json_str:
            if not allow_fallback:
                raise ValueError("Architect output did not contain a valid JSON block.")
            _logger.warning("No JSON block found in architect output. Returning fallback spec.")

        parsed_data = {}
        if extracted_json_str:
            try:
                parsed_data = json.loads(extracted_json_str, strict=False)
            except Exception as e:
                if not allow_fallback:
                    raise ValueError(f"Architect output JSON parsing failed: {e}")
                _logger.warning(f"Failed to parse JSON from architect output: {e}. Attempting fallback.")

        # Extract routes / endpoints list
        raw_routes = parsed_data.get("routes") or parsed_data.get("api_endpoints", [])
        routes_list = []
        if isinstance(raw_routes, list):
            for item in raw_routes:
                if isinstance(item, dict):
                    m = item.get("method", "GET")
                    p = item.get("path", "/api")
                    routes_list.append(f"{m} {p}")
                else:
                    routes_list.append(str(item))

        # Extract database models / schema list
        raw_models = parsed_data.get("models") or parsed_data.get("database_schema", [])
        models_list = []
        if isinstance(raw_models, list):
            for item in raw_models:
                if isinstance(item, dict):
                    models_list.append(item.get("table", "Entity"))
                else:
                    models_list.append(str(item))

        # Folder structure mapping
        folder_struct = parsed_data.get("folder_structure") if isinstance(parsed_data.get("folder_structure"), dict) else {
            "frontend": ["src/App.jsx", "src/components/Navbar.jsx"],
            "backend": ["main.py", "models.py", "auth.py"],
            "database": ["schema.sql"]
        }

        spec_kwargs = {
            "project_name": parsed_data.get("project_name") or "AIForge Application",
            "architecture_style": parsed_data.get("architecture_style") or "Modular Monolith",
            "frontend": parsed_data.get("frontend") or "React",
            "backend": parsed_data.get("backend") or "FastAPI",
            "database": parsed_data.get("database") or "PostgreSQL",
            "components": parsed_data.get("components") or ["Navbar", "Sidebar", "DashboardCard", "LoginForm"],
            "routes": routes_list or ["GET /health", "POST /api/auth/login", "GET /api/data"],
            "models": models_list or ["User", "Session", "Item"],
            "dependencies": parsed_data.get("dependencies") or ["react", "fastapi", "sqlalchemy", "pydantic"],
            "folder_structure": folder_struct,
            "auth_strategy": parsed_data.get("auth_strategy") or "JWT Bearer Authentication",
            "environment_variables": parsed_data.get("environment_variables") or ["DATABASE_URL", "SECRET_KEY"],
            "architectural_decisions": parsed_data.get("architectural_decisions") or ["Modular service separation"]
        }

        validated_spec = ArchitectureSpec(**spec_kwargs)
        arch_dict = validated_spec.model_dump()
        return arch_dict

    def generate_architecture_from_spec(self, project_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates architecture blueprint using ProjectSpec as single source of truth.
        """
        proj_name = project_spec.get("project_name", "AIForge Application")
        frontend_fw = project_spec.get("frontend", "React")
        backend_fw = project_spec.get("backend", "FastAPI")
        database_engine = project_spec.get("database", "PostgreSQL")

        return {
            "project_name": proj_name,
            "architecture_style": "Modular Monolith",
            "frontend": frontend_fw,
            "backend": backend_fw,
            "database": database_engine,
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

    def generate_architecture_blueprint(self, project_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Backward compatibility alias for generate_architecture_from_spec."""
        return self.generate_architecture_from_spec(project_spec)


