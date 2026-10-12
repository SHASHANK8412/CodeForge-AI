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
- **Verification:** mandatory gates run the project's tests and a generated contract test in the Docker
  sandbox, plus a Security Guardian re-check.
- **Delivery:** only then can the result be delivered, as an Autopilot plan awaiting approval.

- UI: **Engineering Suite → Swarm Intelligence** (the old "Multi-Agent" view opens it too).
- API: `/api/projects/{id}/swarm/missions` and `/api/swarm/agents`.
- Code: `backend/swarm/`.

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

For each **API mismatch**, two proposals are built:
- change the client to the backend's interface;
- change the backend to the client's interface.

They are scored only on checked facts: deviations from the contract on each side, change size, and
security exposure. Then:
- A proposal that would adopt the side that departs from the agreed contract **violates a mandatory
  constraint**.
- `consensus.decide` applies the mandatory constraints first, then the weighted priorities. **Votes are
  never counted.** A tie within 0.05, or missing evidence for the leader, goes to a person.

How a conflict is resolved:
- **Automatic, at most one bounded round:** when exactly one side departs from the contract, the
  deviating agent runs again with the mismatch as feedback, and review and integration run again.
- **Escalated:** in every other case the mission becomes `awaiting_decision`. The Debate Center shows the
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

## Limitations

- Only API-feature missions with a FastAPI backend and a fetch-based JS client.
- Response shapes aren't compared with the contract, only the request side.
- Routes are read per file: a prefix added by `include_router(..., prefix=…)` in another file isn't
  resolved.
- The Critical Reviewer is rule-based. It does not judge business logic.
- Performance and Chaos gates aren't selected for API-contract missions.
- The contract comes from the person creating the mission. An Architecture Agent that proposes contracts
  (with competing designs) isn't implemented.
