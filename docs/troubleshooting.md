# Troubleshooting

**A stage takes many minutes.** On CPU-only machines each model call can take minutes. Use a
smaller planner (`AIFORGE_GENERAL_MODEL=llama3.2:3b`) and raise `AIFORGE_LLM_TIMEOUT_SECONDS`.
The build view shows the current agent and live token counts, so a slow stage is visible.

**"Ollama offline" on the dashboard.** Start Ollama and pull a model (`ollama pull qwen2.5-coder`).
`GET /api/models/installed` shows what the backend can see.

**Generated tests fail to import their own packages.** The project's `requirements.txt` is
installed into its sandbox (Docker or `<project>/.venv`). If a package is missing from it, the
debug loop adds it; if the install itself fails, the error appears in the test output.

**The run pauses with "Automatic fix failed — human guidance required".** The debug loop stopped
because the same failure repeated or the attempt limit was reached. Read the failures in the
approval panel; reject with guidance to send it back to debugging, or approve to export as is.

**"Release blocked" at the final approval.** The release report found blocking issues: the
code-quality gate failed (e.g. undefined names), Bandit reported a high-severity issue, or
pip-audit found a vulnerable dependency. Each finding is listed with file and line.

**Runs stuck "in progress" after a restart.** Runs that were executing when the server stopped
are closed as failed ("Interrupted") on the next start. Runs paused for approval are kept and can
be resumed.

**Docker Desktop crashes at start on Windows** (`initializing Inference manager ... The file cannot
be accessed by the system`). It left socket files behind that Windows will not delete. Run
`powershell -ExecutionPolicy Bypass -File scripts\start-docker.ps1`.

**The backend container exits immediately in Docker.** Check `docker compose logs backend`. A
`DATABASE_URL` pointing at a Postgres on `localhost` is unreachable from the container; compose
uses SQLite unless `DOCKER_DATABASE_URL` is set.

**The frontend shows "Backend offline".** It calls `VITE_API_URL` (default
`http://127.0.0.1:8000`). For a different host or port, rebuild the frontend with that variable
and add the frontend's origin to `CORS_ORIGINS`.
