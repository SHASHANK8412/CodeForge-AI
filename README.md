# AIForge — Autonomous Multi-Agent Software Engineering Platform

AIForge turns a natural-language software requirement into a generated full-stack project. A
LangGraph workflow of specialized agents plans, designs, writes, reviews, tests, repairs and
packages the code, using **local LLMs through Ollama** — no cloud model API required.

> **Status:** active development. This README describes what is implemented and verified today;
> see [Feature status](#feature-status) and [Known limitations](#known-limitations).

---

## How it differs from a chatbot

A chatbot answers in one turn. AIForge runs a **stateful, checkpointed pipeline** where each stage
is a separate agent with its own prompt and model profile, and later stages consume earlier
stages' structured output:

```text
Requirement
  → Planner → Architect → [Human approval]
  → Frontend ║ Backend ║ Database      (parallel LangGraph branches)
  → Assembly → Reviewer
  → Build validation ║ Dependencies ║ Security scan ║ Performance
  → Execution validation → Testing
      ├─ pass → Documentation → [Human approval] → Packaging → Export
      └─ fail → Debug → Patch → re-test   (self-healing loop, bounded by MAX_REPAIR_ATTEMPTS)
```

- **LangGraph orchestration** with a persistent checkpointer, so a run can pause for human
  approval and resume (`backend/graph/parallel_workflow.py`, `backend/generation/manager.py`).
- **Live progress**: every agent transition is streamed to the UI over SSE
  (`/api/generations/{id}/stream`) and shown as a live agent org chart.
- **Local LLMs**: models are discovered from your Ollama install and routed per task profile
  (`backend/models/model_router.py`).
- **RAG** over project documents with ChromaDB and sentence-transformer embeddings.
- **Export** of a finished generation as a ZIP (`/api/export/zip/{generationId}`) or to GitHub.

## Feature status

| Area | Status |
|---|---|
| Planner / Architect / Frontend / Backend / Database agents (real LLM calls) | Working — see [verification](#verification) |
| LangGraph pipeline with parallel branches and human-approval checkpoints | Working |
| Live agent status (SSE) and agent org chart in the UI | Working |
| Validation, review, security scan, testing, debug/patch self-healing nodes | Implemented in the graph; see [verification](#verification) for how far a run got |
| ZIP export of a completed generation | Working (tests: `tests/test_export_zip_route.py`) |
| GitHub export | Implemented (`backend/github/`); requires `GITHUB_TOKEN` |
| Docker / docker-compose for AIForge itself | Added; **not verified** — Docker was not available on the development machine |
| Local deployment with smoke tests and rollback | Working — a failed deploy restores the last file checkpoint (`tests/deployment/`) |
| Cloud deployment (Vercel / Render / Neon) | Implemented against the real REST APIs (Neon database → Render backend → Vercel frontend). Tested with mocked HTTP only; **not yet run against live accounts**. Without `VERCEL_TOKEN` / `RENDER_API_KEY` / `NEON_API_KEY` a provider reports `NOT_CONFIGURED`; Render also needs the project exported to GitHub first |

## Quick start (local)

**Prerequisites:** Python 3.13, Node.js 20.19+ (or 22.12+), [Ollama](https://ollama.com) with at
least one chat model pulled (e.g. `ollama pull qwen2.5-coder` or, on CPU-only machines,
`ollama pull llama3.2:3b`).

```bash
git clone https://github.com/SHASHANK8412/CodeForge-AI.git
cd CodeForge-AI
cp .env.example .env          # then edit as needed
```

Backend (run from the repository root):

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173, choose **New Project**, describe the app, and follow the run on the
build dashboard. The run pauses once for architecture approval.

## Docker

```bash
docker compose up --build                    # uses the Ollama already running on your host
docker compose --profile ollama up --build   # also runs Ollama in a container
```

Frontend: http://localhost:8080 · API docs: http://localhost:8000/docs. Generated projects and
app data persist in named volumes. Set `VITE_API_URL` (build arg) and `CORS_ORIGINS` when the
frontend is served from a different origin.

## Configuration

All settings are environment variables; see [`.env.example`](.env.example). The ones that matter
most:

| Variable | Purpose |
|---|---|
| `AIFORGE_GENERAL_MODEL`, `AIFORGE_CODING_MODEL` | Pin specific Ollama models instead of auto-selection |
| `AIFORGE_LLM_TIMEOUT_SECONDS` | Ceiling for one LLM call (default 900; CPU-only inference is slow) |
| `MAX_REPAIR_ATTEMPTS` | Bound on the debug → patch → re-test loop |
| `CORS_ORIGINS`, `VITE_API_URL` | Hosting the frontend and backend on different origins |
| `GITHUB_TOKEN` | GitHub export |
| `VERCEL_TOKEN` (+ optional `VERCEL_TEAM_ID`), `RENDER_API_KEY`, `NEON_API_KEY` | One-click cloud deployment |

## Verification

Last end-to-end run (2026-10-06, CPU-only machine; `llama3.2:3b` for planning, `qwen2.5-coder`
for code; prompt: a recipe box with a FastAPI backend and React frontend). The run **completed**
in about 19 minutes:

| Stage | Result |
|---|---|
| Planner, Architect | Real LLM calls (114s, 108s); paused for and resumed after architecture approval |
| Frontend ∥ Backend ∥ Database | Ran in parallel (282s, 141s, 447s) |
| Reviewer, Documentation | Real LLM calls (127s, 28s) |
| Testing → self-healing | Generated tests were run against the generated code. They failed because the generated project imports packages (`passlib`, `selenium`) that are not installed; the debug → patch loop could not fix that, so the run paused for human review instead of retrying forever |
| Final approval → packaging | Approved; one project folder written (`generated_projects/Recipe_Box_Where_Users`) |
| ZIP export | `GET /api/export/zip/{generationId}` returned a 31-file archive (backend, frontend, schema, tests, Docker, docs) |

Fixed along the way: generated tests imported AIForge's own `backend` package instead of the
generated one; unnamed plans all wrote into one shared folder; the final step crashed on the
quality-score format; and packaging rebuilt the project from raw agent output, discarding repairs.

## Testing

```bash
pip install -r requirements-dev.txt
python -m pytest tests
```

Latest full run (each file in its own process): **779 passed, 52 failed, 3 errors**. The failures
are in 21 older test files (Day 11–14 workflow and memory suites, the project-manager agent,
plugins, RAG routes, the self-correction loop) that target APIs which have since changed. Ten
further files are standalone scripts with no pytest tests. Tests never write to
`backend/data/generations.json`: `tests/conftest.py` gives each test a temporary store.

## Known limitations

- **Speed depends heavily on hardware.** On a CPU-only machine each agent call takes one to a few
  minutes, so a full run takes a long time; a GPU or a small model (`llama3.2:3b`) helps.
- **Cloud deployment is untested against live accounts** (see feature status).
- **Generated projects are tested in AIForge's own Python environment.** Their dependencies are
  not installed per project, so tests that import packages AIForge doesn't have fail to collect.
- **Some legacy modules still return sample data** where no real backend exists for them (for
  example `backend/deployment/cicd_pipeline.py`). Pages backed by real APIs show real data or an
  empty state.
- **Part of the test suite is stale** — tests written against APIs that have since changed.
  See [Testing](#testing) for current numbers.

## License

[MIT](LICENSE)
