# AIForge Docker-Based Isolated Code Execution Sandbox

This document explains the architecture, security model, configuration, and operation of AIForge's Docker execution backend.

---

## 1. Overview

AIForge provides two isolated execution sandbox backends:
1. **LocalExecutionBackend**: Subprocess sandbox on the host with temporary directory isolation, sanitized environment variables, and strict timeouts.
2. **DockerExecutionBackend**: High-security, ephemeral container sandbox providing filesystem containment, CPU/memory quotas, network isolation, non-root execution where practical, and automatic container lifecycle cleanup.

The pipeline architecture:
```
ExecutionService
  ├── LocalExecutionBackend (Host Subprocess Sandbox)
  └── DockerExecutionBackend (Ephemeral Container Sandbox)
```

Pipeline execution loop:
```
Project Assembly
      ↓
Docker Sandbox Initialization (🐳)
      ↓
Workspace Volume Mount (/workspace)
      ↓
Dependency Installation (pip / npm inside container)
      ↓
Test & Verification Execution (pytest / npm test inside container)
      ↓
Captured Outputs (stdout, stderr, exit code, duration, container ID)
      ↓
Testing Agent Evaluation
      ↓
Failure Detected? ─── No ───> Final Report: SUCCESS (VERIFIED)
      │
     Yes
      ↓
Debug Agent Root-Cause Diagnosis
      ↓
Targeted Patch Generation
      ↓
Apply Patch to Project Files
      ↓
Retest in Docker Container (Bounded by MAX_REPAIR_ATTEMPTS)
      ↓
Final Validation Report
```

---

## 2. Docker Prerequisites

To run generated projects inside Docker containers:
- **Docker Engine or Docker Desktop**: Must be installed and running.
  - Windows: Docker Desktop with WSL2 backend enabled.
  - Linux: `docker-ce` and `containerd` with docker daemon active (`systemctl status docker`).
  - macOS: Docker Desktop or OrbStack.
- **Base Container Images**:
  The following images are pulled automatically on first use:
  - Python projects: `python:3.11-slim` (or `python:3.12-slim`)
  - Node.js / React / Vite projects: `node:20-slim`
- Verify Docker is operational:
  ```bash
  docker info
  ```

---

## 3. How to Enable Docker Execution

### Option A: Environment Variables
Set the following in your environment or `.env` file before starting the backend:
```bash
DOCKER_ENABLED=true
EXECUTION_BACKEND=docker
```

### Retired: request-payload and Validation Sandbox options
The old `POST /api/projects/{project_id}/autonomous-validate` endpoints (and the `/api/execution/validate` aliases)
accepted files, image, limits and network mode from the request body. They now return **410 Gone**.
The sidebar's **Validation Sandbox** entry opens the **Execution Guardian**, which verifies the project's own files
on disk (with ownership checks) on an isolated copy using server-controlled execution profiles:
`POST /api/projects/{project_id}/verifications`.

---

## 4. Configuration Reference

| Environment Variable | Default | Description |
| :--- | :--- | :--- |
| `DOCKER_ENABLED` | `false` | Master toggle to enable containerized execution sandbox. |
| `EXECUTION_BACKEND` | `local` | Default execution backend: `local` or `docker`. Automatically set to `docker` when `DOCKER_ENABLED=true`. |
| `EXECUTION_TIMEOUT` | `30.0` | Execution timeout in seconds per command (dependencies, test runs). |
| `MEMORY_LIMIT` | `512m` | Container memory quota (e.g. `256m`, `512m`, `1g`, `2g`). Enforced via `--memory` and `--memory-swap`. |
| `CPU_LIMIT` | `1.0` | Maximum CPU core quota (e.g. `0.5`, `1.0`, `2.0`). Enforced via `--cpus`. |
| `NETWORK_MODE` | `none` | Docker network isolation mode. Default `none` disables all network access to prevent code from exfiltrating data or making untrusted external requests. |

---

## 5. Supported Project Types

AIForge automatically detects the project framework and runs inside the optimized container:

1. **Python Projects**:
   - Detected by: `requirements.txt`, `pyproject.toml`, or `.py` files.
   - Base Image: `python:3.11-slim`
   - Dependency Command: `pip install -r requirements.txt`
   - Test Command: `python -m pytest tests --rootdir=. -q`
2. **Node.js Projects**:
   - Detected by: `package.json` with scripts or entry points.
   - Base Image: `node:20-slim`
   - Dependency Command: `npm install --no-audit --no-fund`
   - Test Command: `npm test`
3. **React / Vite Projects**:
   - Detected by: `package.json` with `vite` dependency and JSX/TSX components.
   - Base Image: `node:20-slim`
   - Dependency Command: `npm install --no-audit --no-fund`
   - Build/Test Command: `npm test` or `npm run build`

---

## 6. Security Model

Generated code is treated as untrusted. When Docker mode is enabled:
- **Filesystem Isolation**: Only the ephemeral project sandbox directory is mounted into `/workspace`. The container has no access to host root directories, user profile directories, or other projects.
- **Credential Scrubbing**: Host credentials, API keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GITHUB_TOKEN`), database connection strings, and `.env` files are stripped before container execution.
- **Resource Containment**: Memory limits (`--memory 512m`) and CPU caps (`--cpus 1.0`) prevent fork bombs and denial-of-service loops.
- **Network Isolation**: Default `--network none` cuts off all inbound and outbound network connectivity.
- **Privilege Capping**: Containers run with `--security-opt no-new-privileges` to prevent privilege escalation.
- **Automatic Cleanup**: Every container is started with `--rm` and tracked with a unique container ID (`aiforge_exec_<uuid>`). Cleanup handlers ensure containers are killed and removed even on timeouts or exceptions.

---

## 7. Troubleshooting

### Issue 1: Docker daemon is not running
- **Symptom**: Logs show `"DockerExecutionBackend requested but Docker daemon/binary is unavailable. Falling back to LocalExecutionBackend."`
- **Fix**: Start Docker Desktop or run `sudo systemctl start docker`. Ensure your user has permissions to run docker (`sudo usermod -aG docker $USER`).

### Issue 2: Network error during dependency installation
- **Symptom**: `pip install` or `npm install` fails with network resolution errors when `NETWORK_MODE=none`.
- **Fix**: If projects require downloading packages during the initial validation step, set `NETWORK_MODE=bridge` or configure pre-cached container images with dependencies pre-installed.

### Issue 3: Container out-of-memory (OOM)
- **Symptom**: Process exit code 137 or `Killed`.
- **Fix**: Increase `MEMORY_LIMIT` in `.env` (e.g. `MEMORY_LIMIT=1g`) or through the frontend Docker Limits dropdown.

### Issue 4: Command timed out
- **Symptom**: `ProjectExecutionResult` status `TIMEOUT`.
- **Fix**: Increase `EXECUTION_TIMEOUT` in config (e.g. `EXECUTION_TIMEOUT=60.0`) or pass a higher timeout in the request payload.
