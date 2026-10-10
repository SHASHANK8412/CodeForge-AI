# Setup

## Requirements

- Python 3.13, Node.js 20.19+ (or 22.12+)
- [Ollama](https://ollama.com) with at least one chat model. A coding model gives much better
  results: `ollama pull qwen2.5-coder`. On a CPU-only machine `llama3.2:3b` is the fastest planner.
- Optional: Docker Desktop, for the test sandbox and the Docker stack.

## Local

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
python -m uvicorn backend.main:app --reload --port 8000
```

```bash
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173. The backend reads its settings from environment variables; copy
`.env.example` and export the ones you need (the backend does not load `.env` by itself when run
with uvicorn directly).

## Docker

```bash
docker compose up --build
```

Frontend http://localhost:8080, API http://localhost:8000/docs. The backend uses the Ollama on
your host (`host.docker.internal:11434`). On Windows, if Docker Desktop fails to start with a
`dockerInference ... cannot be accessed by the system` error, run
`powershell -ExecutionPolicy Bypass -File scripts\start-docker.ps1`.

## Settings that matter

| Variable | Default | Purpose |
|---|---|---|
| `AIFORGE_GENERAL_MODEL`, `AIFORGE_CODING_MODEL`, `AIFORGE_DEBUG_MODEL` | auto | Pin Ollama models per role |
| `AIFORGE_LLM_TIMEOUT_SECONDS` | 900 | Ceiling for one model call (CPU inference is slow) |
| `AIFORGE_TEST_SANDBOX` | `auto` | `docker`, `local` or `auto` (Docker when available) |
| `AIFORGE_LLM_REPAIR` | `1` | Let the debug loop ask the coding model to rewrite a failing file |
| `MAX_REPAIR_ATTEMPTS` | 3 | Bound on debug → patch → retest cycles |
| `AIFORGE_AUTO_PUBLISH_GITHUB` + `GITHUB_TOKEN` | off | Publish approved projects to a private repo |
| `AIFORGE_REQUIRE_AUTH` | off | Reject unauthenticated API requests |
| `AIFORGE_ENABLE_CODE_TOOLS` | off | Allow agent tools that run code or commands |
| `JWT_SECRET` | generated | Login token signing key |
| `AIFORGE_COST_PER_1K_PROMPT` / `_COMPLETION` | 0 | Price runs as if they used a hosted model |
| `VERCEL_TOKEN`, `RENDER_API_KEY`, `NEON_API_KEY` | unset | Cloud deployment |

## Tests

```bash
python -m pytest tests
```

Tests use a temporary generation store and the local sandbox by default; Docker tests run only
when the Docker daemon answers.
