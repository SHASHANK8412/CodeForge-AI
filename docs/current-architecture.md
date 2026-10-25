# AIForge System Architecture & Multi-Agent Flow

AIForge is an autonomous multi-agent AI coding platform that converts high-level natural language prompts into complete, tested, documented, quality-evaluated, and deployable software applications.

---

## 1. High-Level Flow Architecture

```text
               User Browser UI (React + Vite)
                            │
                            ▼
               FastAPI Central REST API Server
                            │
                            ▼
          LangGraph Multi-Agent Orchestrator
                            │
     ┌──────────────────────┼──────────────────────┐
     │                      │                      │
     ▼                      ▼                      ▼
Planner Agent       Architect Agent       Context RAG Engine
     │                      │                      │
     └──────────────────────┼──────────────────────┘
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
   Frontend Agent    Backend Agent     Database Agent
   (React / Vite)    (FastAPI / REST)  (PostgreSQL / Schema)
          └─────────────────┬─────────────────┘
                            │
                            ▼
                     Reviewer Agent
                   (AST & SAST Audit)
                            │
                            ▼
                     Testing Agent
                   (Pytest Assertions)
                            │
                    ┌───────┴───────┐
                    │               │
                 PASSED          FAILED
                    │               │
                    │         Debug Agent
                    │          (Auto-Fix)
                    │               │
                    └───────◄───────┘
                            │
                            ▼
                  Documentation Agent
                    (README & Spec)
                            │
                            ▼
                   Project Assembly
              (ProjectBuilder + Exporter)
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
   Quality Gate      ZIP Export      Deployment Engine
   (15 Criteria)    (Download)       (Vercel / Render)
```

---

## 2. Subsystem Descriptions

1. **Frontend Workspace (React + Vite + Tailwind CSS)**:
   - **Landing Page (`/`)**: SaaS presentation & feature breakdown.
   - **Authentication (`/login`, `/register`, `/forgot-password`, `/reset-password`)**: Session management, JWT storage, HTTP-Only cookies.
   - **Project Dashboard (`/dashboard`)**: Central project list, stats cards, filtering, sorting, pagination, and project ownership controls.
   - **Project Creation (`/create`)**: Input specification & technology preferences selector.
   - **Live Build Dashboard (`/projects/:id/build`)**: Streaming LangGraph agent workflow visualization with real-time SSE progress logs.
   - **Code Workspace (`/projects/:id/code`)**: Dynamic file tree, syntax-highlighted code editor, and live preview.
   - **Quality & Testing Center (`/projects/:id/quality`)**: 15 Quality Gates, test pass metrics, SAST audit, performance metrics, and automatic repair workflow.
   - **Deployment Center (`/projects/:id/deploy`)**: Target provider selection (Vercel, Render, Docker), secret vault, 9-step deployment tracker, and live health probes.
   - **Account Settings (`/settings`, `/settings/api-keys`)**: User profile, security, and API key management.

2. **Backend API Gateway (FastAPI)**:
   - Houses REST endpoints for authentication, project management, workflow generation, file inspection, quality evaluation, ZIP export, and DevOps deployment.

3. **LangGraph Workflow Orchestrator**:
   - Manages stateful agent transitions and parallel execution. Handles conditional edges for automatic debug loops (up to 3 retries).

4. **LLM Engine**:
   - Executes via local Ollama models (`Qwen 2.5` & `Qwen 2.5-Coder`) with fallback to deterministic mock mode (`AI_MODE=mock`) for rapid CI integration testing.

5. **Storage & Memory**:
   - **Project Memory**: Stores execution traces and generated files in `generated_projects/`.
   - **Export Gate**: Ensures failed projects cannot be exported without passing mandatory quality gates.
