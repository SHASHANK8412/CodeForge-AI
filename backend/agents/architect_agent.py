from typing import Dict, Any, List, Optional
from backend.agents.base_agent import BaseAgent


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

    def generate_architecture_blueprint(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        proj_name = plan.get("project_name", "AIForge Application")
        return {
            "project_name": proj_name,
            "architecture_style": "Modular Monolith with Microservice Readiness",
            "technology_stack": {
                "frontend": "React 18, TailwindCSS, React Router v6, Axios",
                "backend": "FastAPI, Python 3.11, Pydantic v2, SQLAlchemy",
                "database": "PostgreSQL 15, Redis 7",
                "devops": "Docker, Docker Compose, GitHub Actions CI/CD"
            },
            "folder_structure": {
                "frontend/": ["src/pages", "src/components", "src/layouts", "src/hooks", "src/context", "src/services"],
                "backend/": ["app/routers", "app/services", "app/models", "app/schemas", "app/middleware"],
                "database/": ["migrations/", "schema.sql", "seed.sql"]
            },
            "component_hierarchy": [
                "App -> MainLayout -> (Navbar, Sidebar, PageView, Footer)",
                "Pages: Home, Dashboard, Login, Settings",
                "State: AuthContext, ProjectContext"
            ],
            "api_flow": "Client -> Auth Middleware -> Router -> Service Layer -> ORM / DB Pool -> JSON Response",
            "execution_plan": [
                "Phase 1: DB Schema & Migration setup",
                "Phase 2: FastAPI Core Routers & Auth Services",
                "Phase 3: React Layouts, Auth Context & Page Components",
                "Phase 4: Review, Testing & Packaging Assembly"
            ],
            "dependency_graph": {
                "backend": ["database"],
                "frontend": ["backend"],
                "testing": ["frontend", "backend"],
                "assembler": ["frontend", "backend", "database", "testing"]
            }
        }
