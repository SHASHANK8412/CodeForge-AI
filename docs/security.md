# Security model

AIForge runs model-written code, so every generated project is treated as untrusted.

## Generated code

| Control | Where |
|---|---|
| Generated tests run in a throwaway Docker container: `--network none`, non-root user, `--cap-drop ALL`, `no-new-privileges`, 2 GB memory, 2 CPUs, 256 processes, a timeout; containers and volumes are removed afterwards | `backend/execution/docker_test_sandbox.py` |
| Dependencies are installed in a separate container (the only step with network access) into a throwaway volume, never into AIForge's environment | same |
| Code snippets from chat and the execution engine's commands run the same way: `--network none` (installs excepted), non-root where possible, `--cap-drop ALL`, read-only root, memory/CPU/process limits, timeout | `backend/execution/sandbox_executor.py`, `execution_backend.py` |
| Without Docker, generated code is **not run** and the result says so; there is no host fallback. `AIFORGE_TEST_SANDBOX=local` is an explicit opt-in to run it on this machine (per-project venv, scrubbed environment) and is meant for AIForge's own test suite | `backend/execution/docker_test_sandbox.py`, `execution_service.py` |
| Live previews run in hardened containers (non-root, no capabilities, read-only root, limits, port on 127.0.0.1 only, auto-stop) and are shown as running only after an HTTP probe answers | `backend/execution/preview_manager.py` |
| Exported ZIPs never include `.env` files, keys, `.npmrc`/`.pypirc`, local databases, virtualenvs or caches | `backend/exporter/zipper.py` |
| Patches are applied atomically and confined to the project folder (component-wise path checks; traversal rolls the whole patch back) | `backend/repository/patch_engine.py` |
| Code-quality gate (ruff, oxlint), Bandit and pip-audit run before release; critical findings mark the release `blocked` | `backend/validation/quality_gate.py` |
| Secret scan before GitHub publishing; publishing is off unless `AIFORGE_AUTO_PUBLISH_GITHUB=1` | `backend/github/publisher.py` |

Docker is an isolation layer, not an absolute boundary: a container escape or kernel
vulnerability is outside what these controls address.

## The AIForge API

| Control | Setting |
|---|---|
| JWT signing key from `JWT_SECRET`, else a random key generated on first start (`backend/data/jwt_secret.key`, git-ignored) | `backend/auth/security.py` |
| Requests without a valid token act as a default local user. **Set `AIFORGE_REQUIRE_AUTH=1` whenever AIForge is reachable from other machines** | `backend/auth/dependencies.py` |
| Agent tools that run Python, shell commands, Docker or database operations are denied unless `AIFORGE_ENABLE_CODE_TOOLS=1`; Python runs in a separate isolated interpreter | `backend/plugins/permissions.py`, `backend/tools/python_runner.py` |
| CORS: localhost/127.0.0.1 on any port by default; set `CORS_ORIGINS` for anything else | `backend/main.py` |
| Project routes resolve a project exactly or return 404; file paths outside `generated_projects/` are refused | `backend/routes/project.py`, `backend/routes/export.py` |

## Secrets

- `.env`, `backend/data/jwt_secret.key` and generated projects are git-ignored.
- Tokens (`GITHUB_TOKEN`, `VERCEL_TOKEN`, `RENDER_API_KEY`, `NEON_API_KEY`) are read from the
  environment on the server only; nothing exposes them to the frontend or generated code.
- Request traces redact `Authorization`, cookies and other credential headers.

## Known gaps

- ChromaDB 1.5.9 has advisories without a released fix; they concern its HTTP server, which
  AIForge does not run (embedded client only).
- Cloud deployments are tested against mocked APIs only.
