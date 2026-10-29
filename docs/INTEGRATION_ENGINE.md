# AIForge Integration & Compatibility Engine (AICE)

> Independently generated components only work together if they implement the same contract. AICE establishes that
> contract before the code agents run, checks the frontend, backend and database against it, routes every mismatch to
> the agent responsible, repairs within limits, and reports only what was checked and executed.

- UI: **Engineering Suite → Integration Engine**.
- API: `/api/projects/{id}/contract…` and `/api/projects/{id}/integration…` (see [API](#api)).
- Workflow: the architect node establishes the contract; the `compatibility` node runs after `assembly`
  (`backend/graph/parallel_workflow.py`).
- Code: `backend/compatibility/`, which contains `models.py`, `contract.py`, `extract.py`, `analyzer.py`,
  `testgen.py`, `repair.py`, `service.py` and `routes.py`.

## What it reuses

| Concern | Existing component |
|---|---|
| API contract format | the Swarm contract (`backend/swarm/models.py`: `Contract` / `Endpoint`, JSON Schema subset). AICE adds the data model, conventions, environment and versioning around it rather than defining a second API format. |
| Contract source | the architect's parsed output (`services/validator.py`): its routes, models and Database Schema section |
| Reading backend routes and `fetch` calls | `swarm/interfaces.py` (FastAPI routes from the AST, with request/response schemas, statuses and auth dependencies) |
| Persistence | the Autopilot JSON store (`AutopilotStore`, one document per project, atomic writes). No new database. |
| Project resolution and authorization | `get_current_user` + `_project_dir` (generation ownership, safe project paths) |
| Running tests in isolation | the Execution Guardian's Python runner: Docker sandbox, or the explicit `AIFORGE_TEST_SANDBOX=local` opt-in |
| Repair scope and model repair | the Guardian's scope rules (`in_scope` / `validate`), Autopilot's `model_changes` with the agent's own system prompt |
| Applying changes | the patch engine (`apply_all`: path validation, all-or-nothing, rollback) |
| Delivery of API-run repairs | an Autopilot `write_files` plan awaiting approval |
| History | the Time Machine ledger |

## The shared contract

A contract version (`SharedContract`) holds the following:

- The API operations: method, path, path and query parameters, request schema, success statuses and schemas,
  documented errors, auth.
- The entities: fields with type, format, required, nullable, primary key and references.
- The conventions: error format, pagination, datetime format, and the auth scheme.
- The environment variables per component, the component dependencies, and the requirements it was derived from.

A contract is **never invented**. Anything its source does not state goes into `unspecified` (per operation, or for
the whole contract). Unspecified aspects are reported as *not checked* and keep a run below `COMPATIBLE`.

Conventions that come from the stack, rather than from the source, are recorded in `conventions` along with where
they came from. For example, the error format is FastAPI's `{"detail": ...}`.

### Versions are explicit and traceable

- A new version is created only by `register` with an author and a reason. Registering identical content returns the
  current version unchanged.
- Earlier versions are kept, and nothing overwrites them.
- Each new version records a `ContractChange`: every item, whether it is breaking and why, the affected components,
  and the affected code (file and line) from the last analysis.
- Breaking changes: removed operations or fields, newly required request fields, type changes, auth added, success
  status changed, shape changes, nullability, relationships, and convention changes.
- Backward-compatible changes: added operations, optional fields, added response fields, nullable columns.
- The architect node derives version 1 from the architecture. After review feedback, a revised architecture becomes a
  new version, recorded with that feedback as the reason.
- Each code agent gets its slice of the contract in its prompt: frontend, backend or database.

## Analysis (deterministic)

`extract.snapshot(project)` reads the project's files and executes nothing:

- **Backend:** FastAPI routes, and error bodies returned through `JSONResponse` and exception handlers.
- **Frontend:** `fetch` and axios calls, including instances created with `axios.create` and imported ones.
  - URLs are resolved through string constants, axios `baseURL` and Vite dev-proxy rewrites.
  - Request body keys and the Authorization header are read from the call.
  - The response fields the code reads, and whether it treats the body as a list, are found by a heuristic. Findings
    from it are labelled `static_heuristic`.
- **Database:** SQL DDL, SQLAlchemy and SQLModel models, Alembic and SQL migrations, and `metadata.create_all`.
- **Environment:** the variables each component reads.

`analyzer.analyze(contract, snapshot, previous)` produces structured findings. Each finding carries an id, a rule, a
severity, the affected components, what the contract expects, what the code actually does, evidence (file and line,
URL, fields), a recommended fix, the responsible agent, its basis and its status.

| Area | Rules |
|---|---|
| API (contract vs backend) | `missing_endpoint`, `incorrect_http_method`, `incorrect_url_path` (a prefix such as `/api` added or dropped, singular vs plural), `request_field_mismatch`, `missing_required_field`, `optional_field_inconsistency`, `response_field_mismatch`, `incorrect_data_type`, `incorrect_status_code`, `auth_mismatch`, `error_response_mismatch`, `pagination_mismatch`, `datetime_format_mismatch`, `undeclared_endpoint` (info) |
| API (frontend vs contract) | the same rules, attributed to the frontend; the `taskName`-vs-`title` case is `response_field_mismatch` with the candidate fields |
| Database | `db_missing_table`, `db_missing_field`, `db_field_type_mismatch`, `db_nullability_mismatch`, `db_identifier_format_mismatch` (primary-key types, UUID vs integer, path parameters), `db_missing_relationship`, `db_extra_required_column`, `db_model_schema_drift` (ORM vs persisted schema), `db_missing_migration` |
| Drift | `contract_drift`: what changed in the implementation since the previous analysis that no contract change explains (renamed or removed fields, removed endpoints, auth or status changes, column changes), with whether it is breaking and the consumers that use it |
| Contract | `contract_inconsistency` (for the architect), `environment_mismatch` |

**Who is responsible.** The contract decides. When the frontend and backend agree on something the contract lacks,
or the contract contradicts itself, the finding is a contract decision (`needs_contract_decision`, for the architect).
It is never repaired by changing code, and the contract is never changed to fit the code.

**When a model is used.** A language model is asked only which contract field an unmatched frontend read most likely
means, and only when no name matches deterministically: same name in another convention, or a near-identical name.
Its answer must be one of the candidate fields, is labelled `model suggestion (advisory)`, and is used only for the
fix. It never makes anything pass.

## Contract tests (generated, executed)

`testgen.generate` writes one pytest module that uses FastAPI's TestClient against the project's own app. Every
expectation comes from the contract, none from the implementation.

| Test | Checks |
|---|---|
| `endpoint_exists` | a route serves the contract's method and path |
| `valid_request` | a request built from the contract gets the contract's success status, and the body validates against the response schema. For `/things/{id}`, a resource is created first through the contract's `POST /things`. The test is **skipped, not passed**, when no valid request or resource can be built. |
| `missing_required_field` | a body missing a required field is rejected with 400 or 422, in the error format |
| `unauthenticated` | an operation the contract protects rejects a request without credentials (401 or 403) |
| `frontend_request` | the frontend's exact method, path and body keys reach a route and are accepted |
| `db_schema`, `db_roundtrip` | the SQL schema applies to an isolated in-memory SQLite database and has the contract's tables and columns; a row is written and read back with foreign keys enforced. PostgreSQL-only schemas are skipped, with the reason. |

The tests run on a working copy that holds the project's sources and only the generated tests, through the
Guardian's isolated runner. The project's own tests are the Guardian's job. If the project's requirements lack
`httpx`, it is added to the copy only. Every test records its own outcome. A test that did not run is reported as
`not_run`, and a run whose tests could not execute is `BLOCKED`.

## Repair coordination

On a working copy, at most `max_repair_attempts` times (0–5, default 3):

1. **Pick.** Contract decisions come first, and they defer implementation repairs on the same operation. After that,
   the order is database → backend → frontend: upstream first.
2. **Targeted fix.** Deterministic fixes come first and are line-precise:
   - **Frontend:** the call's URL or method, a body key renamed 1:1, a response read renamed to the established field.
   - **Backend:** the route decorator's path or method, keeping the handler's parameter names.
   - **Database:** in `schema.sql`, a missing column, the column type, NULL / NOT NULL, a missing foreign key.

   Otherwise the responsible agent makes a model repair, given its contract slice, the evidence and the requirements.
   It may touch only the files the findings name, within its own scope. Tests, env and secret files are never
   changed, and secrets are hidden from the model.
3. **Re-check.** Re-analyse and re-run the contract tests. A repair that adds findings without resolving any, or makes
   contract tests fail, is **rolled back**. A finding that survives its repair is never retried, so repeated failures
   stop. Every attempt is recorded with its strategy, files, resolved and new findings, and tests before and after.
4. **Deliver.** API runs never write the project: kept repairs become an Autopilot plan awaiting approval, with the
   base file hashes. The workflow node writes repairs back through the patch engine, and only to files this
   generation's agents wrote. Files from an earlier version are left untouched.

## Final status

| Status | Meaning |
|---|---|
| `COMPATIBLE` | a contract exists, every applicable check ran, the generated tests ran and passed, nothing is open, and nothing is unspecified |
| `COMPATIBLE_WITH_WARNINGS` | nothing blocking, but something was not checked or not executed (an analysis without tests), was only heuristic, or medium/low findings remain |
| `INCOMPATIBLE` | a critical or high finding is open, or a contract test failed |
| `BLOCKED` | there is no contract, or the contract tests could not run (for example, no Docker) |

Compiling, or the agents' own reports, are never evidence of compatibility.

## Workflow

```text
planner → architect (+ shared contract v1) → approval (shows the contract) → frontend | backend | database
(each gets its contract slice) → assembly → compatibility → reviewer → … → testing → execution_guardian → final approval
```

The `compatibility` node's summary appears in the state as `compatibility`. Final approval shows it, and an
`INCOMPATIBLE` result sets the deployment readiness to `INCOMPATIBLE: …`.

- `AIFORGE_AICE_WORKFLOW_TESTS=off` limits the node to static analysis.
- Model repair in the node follows `AIFORGE_LLM_REPAIR`, the same switch the Debug Agent uses.

## API

All routes need an authenticated user who may work on the project (Autopilot ownership checks). Project ids are
validated, and no client-supplied path or file is accepted.

| Method and path | Purpose |
|---|---|
| `POST /api/projects/{id}/contract` `{"contract", "reason"}` | register a new version (201; 422 with `errors` when invalid) |
| `POST /api/projects/{id}/contract/derive` | derive a version from the generation's architecture (409 when none is recorded) |
| `GET /api/projects/{id}/contract?version=&agent=` | the current or a given version, or an agent's slice |
| `GET /api/projects/{id}/contract/versions` | every version: who, why, when, breaking |
| `GET /api/projects/{id}/contract/diff?from=&to=` | the change items between two versions, plus the history |
| `POST /api/projects/{id}/integration/analyze` | static analysis, returns the run |
| `POST /api/projects/{id}/integration/verify` `{"settings"}` | tests and bounded repairs (202; 409 while one is running) |
| `GET /api/projects/{id}/integration/runs[/{run_id}]` | runs; status, findings, tests, repairs, activity |
| `GET /api/projects/{id}/integration/runs/{run_id}/report?format=json\|markdown` | the compatibility report |
| `POST /api/projects/{id}/integration/runs/{run_id}/cancel` | cancel a run |

The proposed `/api/contracts…` and `/api/integration/{run_id}` paths map onto these. Contracts and runs belong to a
project, so they are addressed through it, as every other project resource is.

## Report

The report contains:

- the project, run, contract version and revision;
- the components analyzed and the coverage (what was and was not checked, and why);
- the findings by severity, with evidence;
- drift;
- the repairs performed, and the findings they repaired;
- tests generated, executed, passed, failed, skipped and not run, each with its outcome and detail;
- the unresolved mismatches, the final status with its statement, the warnings and why, the delivery, and the
  limitations.

Every string is redacted (`redact`) before it is stored or returned.

## Running it locally

```bash
python -m pytest tests/compatibility -q
```

```bash
uvicorn backend.main:app --reload
```

Then open **Engineering Suite → Integration Engine**, pick a generated project, choose **Derive from architecture**
(or write a contract), then **Analyze** or **Verify**.

## Limitations

- The response fields a frontend reads are found by pattern matching, with the label `static_heuristic`. A read the
  pattern misses is not checked, and calls built from dynamic URLs are reported as unreadable.
- Frontend requests are replayed from the code's method, path and body keys. The browser itself is not run. Swarm
  missions run the real JavaScript client in a container.
- The project has no frontend test runner, so frontend integration is checked statically and by these replays.
- Database checks apply SQL schemas to SQLite in memory. PostgreSQL-only schemas, and Alembic migrations (which are
  checked statically), are not executed.
- Autopilot `write_files` plans overwrite whole files on approval. The plan lists the base hashes so a reviewer can
  see whether a file changed since the run.
