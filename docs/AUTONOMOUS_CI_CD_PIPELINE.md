# AIForge Autonomous CI/CD Pipeline

The **AIForge Autonomous CI/CD Pipeline** automatically validates generated and assembled code projects through an isolated, repeatable, multi-stage testing and security pipeline. When failures are detected at any stage, AIForge triggers a closed-loop automated debugging agent that diagnoses root causes, applies targeted code repairs, and re-executes the pipeline up to a configurable maximum retry limit.

---

## 1. Architectural Overview

The Autonomous CI/CD Pipeline is integrated directly into the AIForge multi-agent lifecycle:

```
                  +-----------------------------------+
                  |  AIForge Project Assembly/Export  |
                  +-----------------+-----------------+
                                    |
                                    v
                     +-----------------------------+
                     | CIPipelineEngine (Sandbox)  |
                     +--------------+--------------+
                                    |
            +-----------------------+-----------------------+
            |                                               |
            v                                               v
+-----------------------+                       +-----------------------+
| DockerExecutionBackend|                       | LocalExecutionBackend |
| (Isolated Container)  |                       | (Fallback Subprocess) |
+-----------+-----------+                       +-----------+-----------+
            \                                               /
             +----------------------+----------------------+
                                    |
                                    v
                       [ 1. Dependency Installation ]
                                    |
                                    v
                            [ 2. Build Stage ]
                                    |
                                    v
                            [ 3. Test Stage ]
                                    |
                                    v
                            [ 4. Lint Stage ]
                                    |
                                    v
                          [ 5. Security Stage ]
                                    |
                                    +--------------------+
                                    |                    |
                                 (PASS)               (FAIL)
                                    |                    |
                                    v                    v
                        +--------------------+  +--------------------+
                        | CI Result: PASSED  |  |   Error Analyzer   |
                        | Emit GitHub Actions|  +---------+----------+
                        +--------------------+            |
                                                          v
                                                +--------------------+
                                                |    Debug Agent     |
                                                +---------+----------+
                                                          |
                                                          v
                                                +--------------------+
                                                | Apply Code Repair  |
                                                | (re-run <= MAX_TRY)|
                                                +--------------------+
```

---

## 2. Supported Project Types

AIForge automatically detects the project type via `ProjectDetector`:

| Language / Framework | Detection Indicators | Dependency Command | Build Command | Test Command |
| :--- | :--- | :--- | :--- | :--- |
| **Python (FastAPI / Flask / CLI)** | `requirements.txt`, `pyproject.toml` | `pip install -r requirements.txt` | `python -m py_compile entrypoint.py` | `python -m pytest tests` |
| **Node.js (Express / API)** | `package.json` | `npm install` | `node -c index.js` | `npm test` |
| **React / Vite** | `package.json` with `vite` or `vite.config.js` | `npm install` | `npm run build` | `npm test` |

---

## 3. Pipeline Stages

Each stage produces an isolated, typed `CIStageResult`:

```json
{
  "stage": "tests",
  "status": "passed",
  "exit_code": 0,
  "stdout": "================ 5 passed in 0.12s ================",
  "stderr": "",
  "duration": 0.42,
  "command": "python -m pytest tests"
}
```

### Stage 1: Dependency Installation (`DependencyStage`)
* Resolves package manifest (`requirements.txt`, `package.json`).
* Runs isolated package installation with timeout bounds.

### Stage 2: Build (`BuildStage`)
* Validates full AST compilation and syntax correctness without runtime execution side-effects.
* For Python: compiles files via `py_compile`.
* For Node / React: executes bundle builder (`npm run build`).

### Stage 3: Test (`TestStage`)
* Executes unit and integration test suites (`pytest`, `vitest`, or `npm test`).
* Captures standard output, exit codes, assertion errors, and execution timings.

### Stage 4: Lint (`LintStage`)
* Runs static syntax verification, bare exception audits, wildcard import bans, and type-annotation consistency.
* Evaluates code quality against production-readiness benchmarks.

### Stage 5: Security (`SecurityStage`)
* Static security analysis (SAST) and OWASP checks.
* Detects hardcoded secrets, leaked API keys, AWS credentials (`AKIA...`), GitHub personal access tokens (`ghp_...`), and dangerous calls (`eval()`).

---

## 4. Docker Integration & Isolation

When Docker is enabled (`docker_enabled=True` or `execution_backend="docker"`):
* **Workspace Isolation**: Mounts only the dedicated temporary sandbox directory. The host filesystem is protected.
* **Network Containment**: Supports `none` (isolated air-gapped test execution) or restricted bridge mode.
* **Resource Quotas**: Enforces CPU limits (e.g., 1.0–2.0 cores) and RAM limits (e.g., `512m` to `2g`).
* **Container Lifecycle & Cleanup**: Guarantees container termination and removal upon stage completion or timeout.
* **Local Fallback**: Automatically and transparently falls back to `LocalExecutionBackend` if the Docker daemon is unreachable.

---

## 5. Automated Failure Handling & Self-Repair Loop

When any stage returns a failure (`status="failed"`) or timeout (`status="timeout"`):

1. **Error Analyzer & Classifier**: Classifies failure category (`SyntaxError`, `ImportError`, `AssertionError`, `SecurityVulnerability`, etc.).
2. **Debug Agent Consultation**: Passes the failed command, stdout, stderr, exit code, and project files manifest to `DebugAgent`.
3. **Patch Generation**: `DebugAgent` pinpoints the root cause and emits code patches for target files.
4. **Patch Application**: Applies changes directly to the sandbox workspace.
5. **Pipeline Re-Execution**: The pipeline restarts from the beginning.
6. **Bounded Retries**: Bounded by `MAX_CI_REPAIR_ATTEMPTS` (default `3`). If repairs fail across all attempts, the pipeline exits with `FAILED`.

---

## 6. GitHub Actions Workflow Generation

The pipeline automatically generates `.github/workflows/aiforge-ci.yml` customized for the project stack:

* **Python Workflow**:
  - Sets up Python with version matrix (3.11, 3.12).
  - Installs requirements and test/lint tools (`pytest`, `ruff`, `bandit`).
  - Executes build, tests, linting, and vulnerability scanning.
* **Node / React Workflow**:
  - Sets up Node.js.
  - Installs dependencies using `npm ci` or `npm install`.
  - Runs `npm run build`, `npm test`, and `npm run lint`.

---

## 7. Configuration

Configure CI pipeline parameters via environment variables or `CIConfig`:

| Configuration Key | Default Value | Description |
| :--- | :--- | :--- |
| `MAX_CI_REPAIR_ATTEMPTS` | `3` | Maximum automated self-healing iterations before marking pipeline FAILED |
| `CI_DEFAULT_TIMEOUT` | `30.0` | Timeout per stage command in seconds |
| `EXECUTION_BACKEND` | `"local"` | Default execution backend (`"local"` or `"docker"`) |
| `DOCKER_MEMORY_LIMIT` | `"512m"` | Memory quota per Docker container |
| `DOCKER_CPU_LIMIT` | `1.0` | CPU quota per Docker container |
| `DOCKER_NETWORK_MODE` | `"none"` | Docker container networking mode |

---

## 8. Frontend Dashboard

The AIForge UI includes a dedicated glassmorphic **CI/CD Pipeline Dashboard**:
* Accessible via the Sidebar under Engineering Suite (`CI/CD Pipeline`).
* Real-time stage cards displaying status indicators (✅ Passed, ⚠️ Warning, ❌ Failed, ⏳ Running).
* Visual repair attempt timeline showing Debug Agent diagnoses, applied file diffs, and restart events.
* Tabbed views for Live Console Logs, Historical Pipeline Runs, and the generated GitHub Actions YAML workflow.

---

## 9. API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/projects/{project_id}/ci/run` | Triggers the autonomous CI pipeline for a project |
| `GET` | `/api/projects/{project_id}/ci/history` | Lists past CI runs for a project |
| `GET` | `/api/projects/{project_id}/ci/runs/{run_id}` | Retrieves detailed results for a specific run |
| `GET` | `/api/projects/{project_id}/ci/workflow` | Returns the tailored `.github/workflows/aiforge-ci.yml` |
| `POST` | `/api/ci/run` | Direct CI execution endpoint accepting file manifest |
| `GET` | `/api/ci/runs/{run_id}` | Direct CI run retrieval endpoint |

---

## 10. Troubleshooting

| Issue | Likely Cause | Solution |
| :--- | :--- | :--- |
| `DockerDaemonConnectionError` | Docker daemon is not running | CI engine automatically falls back to `LocalExecutionBackend`. Ensure Docker Desktop is started if containerization is desired. |
| Stage status `TIMEOUT` | Long-running test or build script | Increase `timeout_seconds` in `CIConfig` or optimize test suite execution. |
| Security stage fails on `AKIA...` | Leaked secret or token in code | Move API keys and credentials to environment variables or `.env` files. |
| Repair attempts exhausted | Complex logical bug requires human review | Check the CI Run History tab to review the Debug Agent's diagnosis and error tracebacks. |
