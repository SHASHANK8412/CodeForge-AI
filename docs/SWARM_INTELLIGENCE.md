# AIForge Swarm Intelligence

> One problem. Multiple AI engineers. One verified solution — verified by tests, not by agreement.

A **mission** is an engineering objective plus a shared API contract.

- **Agents:** the Mission Controller turns the mission into a task graph that specialised agents execute.
  Independent tasks run in parallel, each in its own isolated copy of the project.
- **Artifacts:** agents exchange validated artifacts with provenance. The interfaces are read back from
  the generated code, never taken from an agent's description of it.
- **Review:** a rule-based Critical Reviewer challenges the result.
- **Conflicts:** the Integration Agent detects real interface conflicts and resolves them through
  evidence-based consensus or a person.
- **Contract-aware integration (v2):** the integrated backend runs in an isolated Docker network and the
  real generated JavaScript client is called against it from a `node:20-slim` container. Requests and
  responses are validated against the contract's JSON Schemas.
- **Bounded repair (v2):** a mismatch with one demonstrably responsible component gets **one** automatic
  repair with the evidence; everything else goes to a person.
- **Verification:** mandatory gates run the runtime contract tests, isolation and cleanup checks, the
  project's tests and a generated contract test in the Docker sandbox, plus a Security Guardian re-check
  (also after every repair).
- **Autopilot review:** a successful mission produces an Autopilot plan awaiting approval; a failed one
  produces an evidence-backed report and, where appropriate, a remediation plan. The swarm never writes to
  the project or deploys anything.

- UI: **Engineering Suite → Swarm Intelligence** (the old "Multi-Agent" view opens it too).
- API: `/api/projects/{id}/swarm/missions` (plus `…/{mid}/report?format=markdown|json`) and `/api/swarm/agents`.
- Code: `backend/swarm/` (`schemas.py`, `runtime.py`, `harness.mjs` and `findings.py` are new in v2).

It replaces the simulated "collaborative missions" module (`backend/multi_agent`, `/api/multi-agent`),
which hardcoded every task as COMPLETED and every finding as VERIFIED.

## Vertical slice (what is implemented)

**API-feature missions.** A Backend Agent writes FastAPI endpoints and tests, while a Frontend Agent
writes the JavaScript API client, both from the same contract and at the same time. Then the review,
integration and verification run.

Other mission types (database schemas, architecture choices, more agents) are **not** implemented yet.

## Task graph

| Task | Agent | Depends on | Output |
|---|---|---|---|
| t1 validate the contract | Mission Controller | – | `contract` |
| t2 implement the endpoints | Backend Agent | t1 | `source_files` (`backend/**` only), `route_inventory` |
| t3 write the API client | Frontend Agent | t1 | `source_files` (`frontend/src/api/**` only), `client_calls` |
| t4 critical review | Critical Reviewer | t2, t3 | `review` |
| t5 integrate | Integration Agent | t2, t3, t4 | `integration_report` |
| t6 verify | Testing Agent | t5 | `test_report`, gates |

- **Assignment:** agents are assigned from the capability registry by capability and task kind (never by
  name). An unknown dependency, a cycle or a task no agent supports **rejects** the plan.
- **States:** pending → running → completed | failed | blocked | cancelled | awaiting_review.
  - A task starts only when every dependency completed.
  - A failed dependency blocks its dependents.
  - Tasks retry within their limit; verification (t6) has none, so a failed mandatory gate is never
    retried into a pass.

## Scheduler

- A thread pool runs ready tasks, up to the mission's concurrency limit (1–4).
- Each task has a timeout. A task that times out is failed, and its late result is ignored; it ran in an
  isolated folder.
- The mission has a time limit and a cap on messages. Hitting the message cap stops the mission.
- Mission state is persisted after every transition. A restart marks running missions `interrupted`.
  **Resume** continues from the persisted state: completed tasks and their artifacts are not redone.

## Artifacts and messages

Every artifact records:
- its creator, task and base revision;
- the time it was created and a content hash;
- its schema validation, which can make it `invalid` (for example files outside the task's owned paths,
  an invalid contract, or a missing inventory);
- `supersedes`: a repaired artifact never overwrites the original.

Messages use these types: `request_information`, `submit_artifact`, `report_finding`, `raise_conflict`,
`request_review`, `propose_resolution` and `report_failure`. Each records its sender, recipient, task,
artifact and evidence references, proposed action and stated confidence. Stated confidence is shown, but
never used as evidence.

## Interfaces are read from code

| What | How |
|---|---|
| Backend routes | Python AST: method, full path (including an `APIRouter(prefix=…)` in the same file), path parameters, request fields from the handler's Pydantic model (required = no default), field types |
| Client calls | `fetch(...)` in JS/TS: method, path (template and concatenated parts become parameters), JSON body keys. URLs built dynamically are reported as unresolvable. |
| Matching | Per call: the route it reaches, or why none does (no such path, wrong method, unknown fields, missing required fields) |

## Critical Reviewer

The Critical Reviewer is rule-based and cites the artifacts each finding rests on. It reports:
- contract operations that aren't implemented, and client calls outside the contract (unsupported
  assumptions);
- backend routes the contract doesn't mention, and field drift on either side;
- contract operations with no backend test;
- new critical or high Security Guardian findings in the backend's files;
- client URLs that can't be checked.

## Conflicts and consensus

The Integration Agent first checks file ownership: two tasks writing the same file is a **critical**
conflict and fails the mission. Then it matches every client call against the backend's routes.

For each **API mismatch**, two proposals are built (v2 adds a third when both sides depart):
- repair the frontend client to the contract;
- repair the backend to the contract;
- repair both (only a person may choose it).

They are scored only on checked facts: deviations from the contract on each side, change size, and
security exposure. Then:
- A proposal that would adopt the side that departs from the agreed contract **violates a mandatory
  constraint**.
- `consensus.decide` applies the mandatory constraints first, then the weighted priorities. **Votes are
  never counted.** A tie within 0.05, or missing evidence for the leader, goes to a person.

How a conflict is resolved:
- **Automatic, at most one repair per mismatch:** when exactly one side departs from the contract
  (established by runtime evidence in v2, see below), the deviating agent runs again with the evidence,
  and review, integration and verification run again.
- **Escalated:** in every other case the mission becomes `awaiting_decision` (`NEEDS_HUMAN_REVIEW`). The Debate Center shows the
  proposals, evidence, risks and score breakdown. A person's choice is recorded and the mission resumes.

## Verification gates

| Gate | Mandatory | Evidence |
|---|---|---|
| interface compatibility | yes | every client call matches a backend route |
| contract conformance | yes | every contract operation is implemented and called as agreed; two components that agree with each other but not with the contract fail |
| project and contract tests | yes | the project's tests plus a generated `tests/test_swarm_contract.py`, which sends each client call (exact method, path and body fields) to the backend through `TestClient` and requires it to be accepted, run in the Docker sandbox. A failure is re-run once; passing on the re-run is `flaky`, which is **not** a pass. |
| security | yes | no new critical or high Security Guardian finding in the changed files (advisory lookups skipped; dependency files are not changed) |
| performance, resilience | no | `not_applicable` for API-contract missions, with the reason |

A mandatory gate that fails or can't run fails the mission, whatever the agents reported.

## Delivery

`POST …/deliver` turns the integrated files into an Autopilot plan (`origin: swarm`) **awaiting
approval**. Approving and executing it runs Autopilot's isolated checks and patch-engine apply. The swarm
never writes to the project.

Mission milestones are also recorded in the Time Machine ledger.


## v2: contract-aware integration and evidence-based repair

### Lifecycle

`Mission.phase` moves through **PLANNING → CONTRACT_READY → PARALLEL_GENERATION → STATIC_VALIDATION →
INTEGRATION_TESTING → FAILURE_CLASSIFICATION → (REPAIR_REQUIRED → … → REVALIDATION) →
SECURITY_VERIFICATION → AUTOPILOT_REVIEW**. Every transition is recorded in `phase_history`.

`Mission.outcome` is one of four terminal outcomes, each mapped to the existing `status`:

| Outcome | Status | When |
|---|---|---|
| `SUCCEEDED` | `completed` | every task completed, every mandatory gate passed, no open finding |
| `FAILED` | `failed` | a mandatory gate failed (or was flaky), or a task failed |
| `BLOCKED` | `blocked` | the isolated environment or a mandatory check was unavailable; nothing was skipped. Resume after fixing it. |
| `NEEDS_HUMAN_REVIEW` | `awaiting_decision` | the repair failed, both components depart from the contract, or the evidence is insufficient or flaky |

### Contract (JSON Schema subset)

Each endpoint has:
- `method`, `path`, `path_params` (name → schema), `query_params` (name → `{schema, required}`) and
  `headers` (name → `{required}`);
- `auth`: `none` or `bearer`;
- `request_content_type` and `request_schema`;
- `responses` (status → `{content_type, schema}`, the success responses);
- `errors` (the documented error responses).

Schemas are validated with `jsonschema` (Draft 2020-12). The contract's **version** is the hash of its
content, and every result refers to it.

**v1 upgrade.** A v1 contract (field-name lists only) is upgraded on load:
- its fields become required properties of **open** type (`{}`);
- the response becomes `200` JSON;
- `422` is documented for a body.

Where the contract leaves a type open, generated requests use the backend's declared type, and the plan
records that.

### What is read, declared and observed

| Basis | Source | Status of a finding |
|---|---|---|
| static | Python AST: `status_code`, `response_model` / return annotation, `response_class`, request model, query and header parameters, auth dependencies (`Depends`/`Security` on an auth-like function, `HTTPBearer`/`OAuth2PasswordBearer`), raised `HTTPException` statuses. JS: the URL and body expressions, headers, `Authorization`, exported functions and their parameters. | `unverified` |
| declared | the app's own `/openapi.json`, fetched inside the sandbox | `unverified` |
| runtime | checks executed against the running backend and client | `verified` when the responsible component is established |

`Mission.properties` shows, per operation, the contract's, static, declared and verified values of the
success status, response body, request validation, auth and client behaviour, and which source decided
(the runtime wins whenever it observed the property).

### Runtime contract tests

The integrated files are copied into a throwaway workspace. Then:

1. **Backend.** The backend starts in the Chaos Engineer's sandbox: a hardened app container (non-root,
   all capabilities dropped, no-new-privileges, read-only, memory/CPU/process limits, no host port) on a
   `docker network create --internal` network with no route out.
2. **Harness.** A `node:20-slim` container with the same limits joins that network and runs
   `backend/swarm/harness.mjs` with a read-only `/work` mount. The mount holds the client modules
   (`import.meta.env` rewritten to an object the harness provides), the plan and the harness. It runs:
   - **`/openapi.json`**, fetched to record the declared behaviour;
   - **contract tests** built from the contract: a valid request, a missing required field, a malformed
     body, a wrongly typed path parameter, a missing required query parameter, a request without
     credentials (bearer endpoints), and an unknown resource (when `404` is documented). Resources created
     earlier are reused, so `GET /orders/{id}` addresses the order the `POST` created.
   - **the real client**: every exported function is imported and called, with arguments derived from
     the contract through its parameter names. `fetch` is wrapped, so the requests actually sent (method,
     path, query, headers with `Authorization` redacted, body) and the responses are recorded.
   - **egress**: `1.1.1.1` and `host.docker.internal` must be unreachable.
3. **Evaluation.** Everything is evaluated in AIForge (not in the container) against the contract:
   - status codes, content types and response bodies, validated with `jsonschema`;
   - invalid input must get a client error (a documented one when errors are documented);
   - an unauthenticated request must get `401` or `403`;
   - every client request must match a contract operation, a valid request body, the content type, the
     required query parameters and the `Authorization` header.
4. **Re-run.** A failed check is executed once more in the same environment. Failing again means it is
   reproduced. Passing the second time means **flaky**, never a pass.
5. **Isolation and cleanup** are inspected from Docker itself:
   - the network is `Internal`;
   - the app container is unprivileged, with `CapDrop ALL`, a read-only root, memory, CPU and process
     limits, a non-root user and no port bindings;
   - after cleanup, no container or network with the run's label remains.

Explicit timeouts:
- 90 s for the backend to answer;
- 8 s per request;
- 15 s per client call;
- 240 s for the harness, also enforced by `timeout` inside the container.

The following are infrastructure failures (`BLOCKED`, never skipped or passed): Docker unavailable, a
timeout, or a harness failure.

### Findings

Every finding has these fields:
- `id`, `mission_id` and `key` (the identity of the mismatch across rounds);
- the operation or component, `category` and `severity`;
- `expected`, `observed` and `evidence` (check id, runtime run, artifact ids, the request and response
  excerpts);
- `basis`, `responsible`, `confidence`, `recommended_correction` and `status`.

**Categories:** request contract mismatch, response schema mismatch, HTTP status mismatch, frontend
integration error, backend runtime error, authentication mismatch, security violation, test
infrastructure failure, insufficient evidence.

**Responsibility follows from the evidence, never from an agent:**
- A request built from the contract got a non-conforming answer, or invalid input was accepted or
  crashed: **backend**.
- The client sent something the contract does not allow, or threw on a conforming response: **frontend**.
- Otherwise the finding is **unresolved**. For example: a client request that conforms is rejected, but
  the same operation passed its own contract test (it depends on state, not on conformance), or the
  check was flaky.

Severity is fixed per category. No CVSS score is invented. Security Guardian findings are reported as
static-rule findings (`needs_human_review`) and are never repaired automatically.

### Bounded repair

After each integration round:

| Situation | What happens |
|---|---|
| no verified or unresolved runtime finding | integration completes; earlier findings become `repaired` |
| verified findings, all from **one** component, never repaired before, repair rounds left | consensus picks that component's proposal (the other one violates the contract); a `RepairAttempt` records the evidence sent, the time and the artifact before; the agent runs again; review, integration (re-extraction and re-test) and every mandatory gate run again |
| verified findings for **both** components | `NEEDS_HUMAN_REVIEW` (proposals include "repair both"; only a person may choose it) |
| only unresolved (insufficient or flaky evidence) | `NEEDS_HUMAN_REVIEW` |
| a mismatch already had its automatic repair, or no repair rounds are left | the findings become `repair_failed`; `NEEDS_HUMAN_REVIEW` |

**One automatic repair per mismatch** holds even when `max_repair_rounds` allows more. A person's
decision (`…/decide`) can direct a further repair, which is recorded with `requested_by: user <id>`.

Each `RepairAttempt` records:
- the component, the finding keys and ids, who requested it and when;
- the agent that authored the new version;
- the artifact before and after (the new version `supersedes` the old one, which is kept unchanged);
- the changed files;
- validation: the runtime run, the mismatches still remaining, the mandatory gates after the repair and
  the security result after the repair;
- the outcome.

### Gates (v2 additions)

| Gate | Mandatory | Evidence |
|---|---|---|
| runtime contract tests | yes | every check of the latest run passed, and the run tested the current artifact versions. Blocked → `unavailable`; a pass only on re-run → `flaky`. |
| isolation and cleanup | yes | Docker inspection (internal network, hardened container), no reachable egress target, verified cleanup |
| security | yes | re-run on the final files after every repair (`rechecked_after_repairs` lists the repairs) |

**Test-only runtime.** The fast tests use a test-only runtime (`tests/swarm/local_runtime.py`: fixed
sample code under host uvicorn and node). It reports itself as **not isolated**:
- its engines are built with `require_isolation=False`, so the isolation gate shows `not_applicable` with
  that reason;
- the application's engine always requires isolation and uses Docker;
- no API can change either setting.

### Autopilot review

`Mission.autopilot_review` holds:
- the objective, outcome and contract version;
- the backend and frontend artifact versions (id, hash, version number, superseded artifact);
- contract validation, the generated tests, the integration tests, security and isolation;
- the repair history, unresolved findings, evidence references (runtime runs, artifacts, findings) and
  proposed actions;
- the approval status, and `project_modified: false` and `deployed: false`.

What happens next depends on the outcome:
- **`SUCCEEDED`**: the integrated files become a `write_files` Autopilot plan awaiting approval
  (`…/deliver` returns that same plan).
- **`NEEDS_HUMAN_REVIEW`**, or **`FAILED`** with open findings: a review plan of `manual` tasks (the
  proposed actions, no file contents) awaits approval.
- **`BLOCKED`**: no plan; the report says what to fix.

`GET …/{mid}/report?format=markdown|json` returns the redacted, evidence-backed report.

### Example (genuine run on this machine, Docker)

The contract says `POST /api/orders` answers `201` with an `Order`. The Backend Agent's first version
answers `200`.

1. **Round 1** (`rt_a7df1721f6`, 18.1 s, node v20.20.2):
   - 8 checks: 6 passed, 2 failed, and both failed again on the re-run.
   - `e0:valid`: expected status 201, observed status 200.
   - `client:createOrder`: the client's own request got status 200; the contract allows `201`.
   - Both are verified `http_status_mismatch` findings, and the backend is responsible.
   - The app's OpenAPI document declared `['200', '422']`, recorded as a declared (unverified) finding.
2. **Repair `rp_38c4634ee9`:**
   - Consensus selected `p_backend` (score 0.718); repairing the client violates the contract.
   - The Backend Agent received both pieces of evidence (check ids and run id) and produced
     `art_edbb14d2f6`, which supersedes `art_5ff1535a7d`. Only `backend/main.py` changed.
3. **Round 2** (`rt_2f4061f1a0`, 14.2 s, a fresh isolated environment):
   - 8 of 8 checks passed. The status is now 201 by static analysis, declaration and runtime alike.
   - The network was `Internal`. The app container was unprivileged, with `CapDrop ALL`, a read-only
     root, 512 MB, 1 CPU, 128 processes, user `1000:1000`, `no-new-privileges` and no port bindings.
   - `1.1.1.1` and `host.docker.internal` were unreachable.
   - Cleanup removed 2 containers, the network and the volume, and left 0 behind.
4. **Gates.** Every mandatory gate passed: interface compatibility, contract conformance, runtime
   contract tests, isolation and cleanup, project and contract tests (4 passed in the Docker sandbox), and
   security (re-checked after `rp_38c4634ee9`).
5. **Result.** `SUCCEEDED`. Plan `pln_4a3ddae58c45` (`write_files`) is `awaiting_approval`.
   `project_modified` and `deployed` are both false.

## Limitations

- Only API-feature missions with a FastAPI backend and a fetch-based JS client.
- Client calls are found in `fetch(...)` calls inside exported functions. Arguments are derived from the
  contract through the functions' parameter names, so unusual signatures can leave arguments undefined.
  The resulting failure is reported, never hidden.
- Operations behind authentication can only be checked as far as a dummy credential allows. A rejected
  valid request is `inconclusive` (insufficient evidence), not a pass.
- Business logic beyond the contract (correct totals, persistence) isn't judged.
- Routes are read per file: a prefix added by `include_router(..., prefix=…)` in another file isn't
  resolved.
- The Critical Reviewer is rule-based. It does not judge business logic.
- Performance and Chaos gates aren't selected for API-contract missions.
- The contract comes from the person creating the mission. An Architecture Agent that proposes contracts
  (with competing designs) isn't implemented.
