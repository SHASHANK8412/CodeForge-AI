# AIForge API

The backend is a FastAPI app (`backend.main:app`). Interactive docs for every endpoint are at
`http://localhost:8000/docs`; this page covers the ones the core workflow uses.

Unless `AIFORGE_REQUIRE_AUTH=1` is set, requests without a token act as the default local user.
With it set, send `Authorization: Bearer <token>` from `POST /api/auth/login`.

## Generation runs

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/generations` | Start a run. Body: `{"project_id": "todo", "prompt": "Build a todo app ..."}`. Returns `generation_id` |
| `GET` | `/api/generations` | Your runs (status, progress, agents, prompt, token usage, metrics) |
| `GET` | `/api/generations/{id}` | One run, including `usage` (real token counts) and `metrics` (tests, quality gate, auto-fixes, security, GitHub) |
| `GET` | `/api/generations/{id}/stream` | Server-Sent Events: a snapshot on connect, then agent and approval events |
| `GET` | `/api/generations/{id}/events` | Recorded event log (polling fallback) |
| `POST` | `/api/generations/{id}/approve` | Approve the checkpoint the run is paused at (architecture or final) |
| `POST` | `/api/generations/{id}/reject` | Reject with feedback; at the final checkpoint this sends the run back to debug |
| `POST` | `/api/generations/{id}/cancel` | Cancel a run |

A run pauses twice for a human: after the architecture plan and before packaging. The final
approval request carries the test results, the security scan, the code-quality gate and the
release report (`release_recommendation`: `ready`, `review_required` or `blocked`).

## Projects

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/projects` | Generated projects with measured quality and test counts (null when never measured) |
| `GET` | `/api/projects/{id}` | Project details, activity and recorded versions |
| `GET` | `/api/projects/{id}/files` | Every file with its content |
| `GET` | `/api/projects/{id}/xray` | Static analysis: backend routes, tables and relationships, React component tree |
| `POST` | `/api/projects/{id}/test` | Run the project's tests (Docker sandbox when available) and return real counts |
| `POST` | `/api/projects/{id}/run` | Run the project's build/validation command |
| `GET` | `/api/projects/{id}/quality` | Quality-center evaluation |

`{id}` is the project's folder under `generated_projects/` or a generation id. An unknown id
returns 404; no endpoint falls back to a different project.

## Export and GitHub

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/export/zip/{id}` | ZIP of a completed run or project folder (path-traversal safe) |
| `POST` | `/api/github/publish` | Create a GitHub repository and push a project (needs `GITHUB_TOKEN`; runs a secret scan first) |
| `GET` | `/api/github/repository/{project_id}` | The repository a project was published to, if any |
| `GET` | `/api/github/overview` | Published repository for a project, or nulls |

## Deployment

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/projects/{id}/deployment` | Deployment status and readiness checks |
| `POST` | `/api/projects/{id}/deployment/plan` | Build a deployment plan |
| `POST` | `/api/projects/{id}/deployment/deploy` | Deploy (local process; Vercel/Render/Neon when their tokens are set) |
| `POST` | `/api/projects/{id}/deployment/rollback` | Restore the last file checkpoint |

## Platform

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness |
| `GET` | `/metrics` | Prometheus text format |
| `GET` | `/api/models/installed` | Installed Ollama models and the ones the pipeline uses |
| `GET` | `/api/analytics/metrics` | Token usage and run outcomes aggregated from recorded runs |
| `GET` | `/api/monitoring/overview` | AIForge's own request count, error rate and p95 latency, agent stage durations |
| `POST` | `/api/plugins/execute` | Run an agent tool; code/shell/Docker/database tools need `AIFORGE_ENABLE_CODE_TOOLS=1` |
