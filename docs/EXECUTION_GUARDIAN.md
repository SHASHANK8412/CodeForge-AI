# AIForge Execution Guardian

> Generated code is not working code until it runs. The Guardian verifies an assembled project by executing it,
> classifies what fails, routes it to the responsible agent, repairs within limits, and reports only what ran.

- UI: **Engineering Suite → Execution Guardian**.
- API: `/api/projects/{id}/verifications`. The `/api/verification` prefix already belongs to the Blockchain
  verifiable-records API.
- Workflow: the `execution_guardian` node of the generation graph (`backend/graph/parallel_workflow.py`).
- Code: `backend/execution_guardian/`, which contains `checks.py`, `classify.py`, `repair.py`, `service.py` and
  `routes.py`.

## What it reuses

The Guardian is an orchestration and record layer over existing, already-isolated infrastructure. It
doesn't duplicate any of it:

| Concern | Existing component |
|---|---|
| Static checks | Autopilot validation: Python syntax, the quality gate (ruff, cross-file imports, oxlint), Bandit |
| Python dependencies and tests | the Docker test sandbox: install container with no capabilities; test container with `--network none`, non-root, CPU/memory/process limits |
| Backend startup | the Performance Engineer runner: hardened preview container (non-root, all capabilities dropped, read-only, limits, port on 127.0.0.1), readiness probe, verified cleanup |
| Frontend install, build and tests | `run_npm_in_docker`: install container, then the script with `--network none` |
| Deterministic repairs | the Debug Agent's repair strategies |
| Model repairs | Autopilot's `model_changes`, with the routed agent's own system prompt from `AgentFactory` (which now also returns the existing Backend and Database agents) and secret lines hidden from the model |
| Applying changes | the patch engine (path validation, all-or-nothing, rollback) |
| Delivery | an Autopilot plan awaiting approval |

## Checks

Checks are selected from the stack, which is detected from the files without executing anything: Python
files and tests, `requirements.txt`, a FastAPI app, a `package.json` with a `build` script, and its scripts.
Every check runs a fixed, controlled profile. **No command is taken from a project file.**

| Check | Required | When |
|---|---|---|
| `python_syntax`, `quality_gate` | yes | Python files exist |
| `security_static` | no; findings are warnings | Python files exist |
| `python_dependencies`, `python_tests` | yes | Python files exist. No test files means `SKIPPED`. |
| `backend_startup` | yes | a FastAPI app is found |
| `frontend_dependencies`, `frontend_build` | yes | a buildable `package.json` exists |
| `frontend_tests` | yes | `package.json` has a `test` script |
| `api_contract` | no; always `SKIPPED` | no contract is known (Swarm missions run contract tests) |

**Check statuses:** `PENDING`, `RUNNING`, `PASSED`, `FAILED`, `BLOCKED` (could not run) and `SKIPPED` (not
applicable or not present). A skipped check is never counted as passed.

**Final status:**

| Status | When |
|---|---|
| `VERIFIED` | every required check ran and passed |
| `VERIFIED_WITH_WARNINGS` | every required check that applies ran and passed, but something applicable was skipped (for example, no tests) or an optional check reported issues |
| `FAILED` | a required check failed |
| `BLOCKED` | a required check could not run and none failed, or nothing ran at all |

A **dependency install failure** is an application failure (`FAILED`, `dependency_install_error`). A
**missing isolated environment** (no Docker) is `BLOCKED`. Container checks are never run on the host. The
explicit `AIFORGE_TEST_SANDBOX=local` opt-in, used by AIForge's own tests, runs Python dependencies and tests
in a per-project virtualenv and says so in the check's environment. `AIFORGE_GUARDIAN_CONTAINERS=off`
disables the container checks; they are then `BLOCKED`.

## Classification and routing

Deterministic rules read the real output of each failed or blocked check. A model is asked only when no rule
matches; its answer must be one of the categories, and the finding is labelled as a model classification.
Without a model the finding is labelled `fallback`. Excerpts, files and test names come from the output, or
are left empty.

| Category | Typical evidence | Responsible agent |
|---|---|---|
| `syntax_error`, `compilation_error` | `SyntaxError`, ruff `F821` | by the affected file: Frontend (frontend files), Database (models, schema, migrations), otherwise Backend |
| `dependency_install_error` | pip/npm install failure, `ModuleNotFoundError` | **dependency resolver** (controlled) |
| `frontend_build_error` | `npm run build` failure | Frontend Agent |
| `backend_startup_error` | the app raised at startup | Backend Agent |
| `database_connection_error` | `OperationalError`, `could not connect`, `sqlalchemy.exc` at startup | Database Agent |
| `configuration_error` | a missing environment variable or setting | Debug Agent |
| `api_contract_mismatch` | – | Debug Agent (integration) |
| `unit_test_failure`, `integration_test_failure` | pytest `FAILED tests/x.py::test_y` (integration, e2e or end_to_end in the name) | the implementation file under test |
| `runtime_exception` | a non-assertion exception, or a timeout | by the affected file |
| `infrastructure_error` | a check that could not run | none: not repairable |

Every failure records:
- the category, severity, summary and log excerpt;
- the files and failing tests;
- the responsible agent and how it was classified;
- the next action;
- a **signature** (category, check and normalised message) used to detect repeats.

## Repair loop (API runs)

```
EXECUTE -> COLLECT -> CLASSIFY -> SELECT AGENT -> TARGETED FIX -> VALIDATE SCOPE -> APPLY (copy)
        -> RERUN FAILED CHECKS -> VERIFY THE OTHER CHECKS -> CONTINUE OR STOP
```

**Isolation.**
- The project is copied into an isolated working copy, and **the project itself is never written**.
- When repairs make the copy pass (`VERIFIED` or `VERIFIED_WITH_WARNINGS`), the changed files become an
  Autopilot plan (`origin: execution_guardian`) awaiting approval.

**Order of repair.** Each attempt repairs the most upstream group of failures first: dependencies, then
syntax, compilation, configuration, database, startup, build, contract, runtime and tests.

**Strategies, in order:**
1. **Deterministic** (the Debug Agent's fixes): missing imports, shadowed modules, misplaced imports and
   missing requirements. The strategy that edits test assertions is **not** used.
2. **Dependency resolver** (controlled). It only adds a package for a failed import from a fixed
   module→package map, or removes a version pin pip could not find, in `requirements.txt` or `package.json`.
   It never guesses a package name.
3. **The routed agent's model repair**, given the failure's evidence, the failing tests (read-only context),
   the next action and the project requirements. It is limited to the files of that agent's scope.

**Scope validation**, before anything is written. A change is rejected and recorded with its reason when it
is:
- outside the workspace (`..`, absolute or drive paths);
- outside the agent's scope (the Frontend Agent edits frontend files only; the Database Agent edits models,
  schema and database files; the Backend Agent edits Python backend files);
- a **test file**: tests are the specification;
- a `.env`, key or credentials file.

**After a repair:**
- The failed and blocked checks run again; if they pass, every other check runs again.
- A repair that adds failures without resolving any, or that leaves fewer checks passing, is **rolled back**,
  and the checks return to their earlier state.

**Bounds:**
- `max_repair_attempts`: default 3, range 0–5;
- `check_timeout_seconds`: 60–1800;
- `run_seconds`: 120–7200;
- cancellation.

**Stopping.** A failure whose signature survives its repair is not attempted again (repeated failure). The
loop stops when nothing repairable is left, and the reason is recorded in the activity log. The original
checks and failures are kept next to the final ones.

## In the generation workflow

```
... execution_validation -> testing -> execution_guardian --VERIFIED*--> final_approval (export gate marked verified)
                                          |--BLOCKED------------------> final_approval (not verified)
                                          |--FAILED (stop)------------> final_approval (escalation)
                                          '--FAILED-> debug -> patch -> execution_validation -> testing -> ...
```

**The node** verifies the freshly generated workspace through a copy. Failures go into the **existing**
`debug → patch` loop, under its existing bound (`MAX_REPAIR_ATTEMPTS`, default 3):
- `debug` receives the Guardian's evidence, for example a backend that doesn't start while the tests pass.
- When the Debug Agent's deterministic strategies find nothing, the **routed agent** repairs. Its changes are
  scope-validated, then applied by the existing `patch` node with backups.

**The loop stops** (`guardian_escalation`) in three cases:
- `STOPPED_MAX_ATTEMPTS`: the attempt bound is reached;
- `STOPPED_REPEATED_FAILURE`: the failure signatures are unchanged since the previous verification;
- `STOPPED_NOT_REPAIRABLE`: no failure is repairable.

**Final approval** shows the verification. Unless the status is `VERIFIED*`, readiness is
`NOT VERIFIED (status)`: passing tests alone no longer read as "ready for export".

## API

| Method and path | Purpose |
|---|---|
| `POST /api/projects/{id}/verifications` | `{"settings": {max_repair_attempts, check_timeout_seconds, run_seconds}, "requirements": "..."}` → `202` with `verification_id` (runs in the background) |
| `GET /api/projects/{id}/verifications` | recent verifications |
| `GET …/{vid}` | status, current operation, checks, failures, repairs, agent activity |
| `GET …/{vid}/checks` | the checks, and the original checks |
| `GET …/{vid}/repairs` | the repair history, original and remaining failures, the limit, the delivery |
| `GET …/{vid}/report?format=json\|markdown` | the final report (`409` while running) |
| `POST …/{vid}/cancel` | cancel |

The project comes from its id with Autopilot's ownership checks (`403` or `404` otherwise); clients pass no
paths. Settings outside their bounds, or unknown ones, return `422`. Reports are redacted.

## Report

The report contains:
- the project and verification ids, the stack, and the start and finish times;
- every check (status, duration, environment, error or reason) and counts by status;
- test summaries and the runtime startup result;
- the repair attempts, and the failures discovered, resolved and remaining (with the responsible agent and
  next action);
- warnings;
- **what was tested** and **what was not tested**: skipped and blocked checks, each with its reason, and the
  API contract, which is never tested here;
- how to run the project, and the limitations.

## Security

**The generated project is untrusted:**
- it runs only in containers (or the explicit local test opt-in) under fixed profiles;
- the app's code runs without network;
- runs are non-root, with capabilities dropped and CPU, memory, process and time limits;
- the containers get no credentials, and no host directories beyond the read-only project copy.

**Repairs** go through scope validation and the patch engine. Test, env and secret files are read-only.
Lines holding secrets are hidden from the model.

**The project is never modified by an API run.** Repaired files reach it only through an approved Autopilot
plan.

## Limitations

- The Guardian checks what the project's own tests and startup exercise. Behaviour the tests don't cover isn't
  verified. Frontend-to-backend calls aren't exercised without an API contract (Swarm missions do that).
- Frontend checks need a `package.json` with a `build` script. Other project types (Java, Go) aren't selected
  yet.
- Model repairs depend on the local coding model. When it proposes nothing usable, the attempt is recorded as
  `no_fix` and the failure remains.
- The older "Validation Sandbox" (`/api/projects/{id}/autonomous-validate`) still exists alongside the
  Guardian. Retiring or hardening it is a separate decision: it accepts client-supplied files without an
  ownership check.
