# AIForge Chaos Engineer

The Chaos Engineer injects controlled failures into a **disposable copy** of a generated app inside an
isolated sandbox. It records what the app does, scores resilience from those records, and verifies
repairs by re-running the same experiment.

- UI: **Engineering Suite → Chaos Engineer**.
- API: `/api/projects/{id}/chaos` and `/api/chaos/scenarios`.
- Code: `backend/chaos/`.

The evidence behind each claim is labelled:

| Label | Meaning |
|---|---|
| **reproduced** | A recorded experiment showed the failure. |
| **static suspicion** | A code pattern that may cause failures. It is never called reproduced. |
| Root cause **probable** | A matching pattern sits on the code path of the endpoint that failed. |
| Root cause **confirmed** | A repair aimed at that cause made the failure disappear in the same experiment. |
| Root cause **unconfirmed hypothesis** | Anything else. |

## Architecture

| Module | Responsibility |
|---|---|
| `scripts.py` | Programs run inside the experiment's own containers (standard library only): the controllable stub dependency, the probe, and the stub control client |
| `sandbox.py` | Preflight checks; the experiment environment: internal network, app, stub dependencies, probe; failure actions; cleanup |
| `scenarios.py` | Scenario registry (preconditions, procedure, limits, expected behaviour, safety, cleanup, verification) and the evaluation criteria |
| `evaluate.py` | Resilience score, findings, static suspicions, root-cause linking, Digital Twin impact |
| `service.py` | Assessment lifecycle, approval, abort, persistence, repair plans, the repair gate |
| `routes.py` | REST API |
| `frontend/src/pages/ChaosEngineerPage.jsx` | Setup, live monitor, report, repairs, history and comparison |

Reused from the rest of AIForge:
- **Preview manager:** the hardened app container and the dependency install.
- **Autopilot:** plans, approval, isolated workspace, correctness checks, bounded self-repair, rollback.
  The executor's measured-gate stage is shared with the Performance Engineer.
- **Digital Twin:** route ownership and dependency impact.
- **Autopilot's store and redaction.**
- **Docker stats parsing** from the Performance Engineer.

## Safety boundaries

- Experiments run only in **`sandbox`**: a Docker network created with `--internal` for each experiment.
  - Containers on it reach each other by name and nothing else: no route to the host, the LAN or the
    internet. This was verified in a test: `http://example.com` is unreachable from inside.
  - Nothing is published on the host.
  - `production` and any other environment are refused at preflight.
- The app runs in the preview's hardened container:
  - non-root, all capabilities dropped, `no-new-privileges`, read-only root;
  - **memory 128–1024 MB, CPU 0.25–1, 128 processes**;
  - a time limit.
- Stub dependencies and the probe also run non-root, with no capabilities, read-only, at 256 MB / 0.5 CPU /
  64 processes. They are AIForge's own code, not the project's.
- Failure actions only target the experiment's own containers, which are labelled `aiforge.chaos=<id>`:
  stop/start the stub, switch its mode, restart the app container. Host processes, host networking,
  firewall rules, real databases and external services are never touched. No container is privileged.
- **Preflight runs before every experiment**, and again at approval:
  - the environment is the sandbox;
  - Docker is available;
  - the app is a supported FastAPI app;
  - dependency names are unique;
  - dependency scenarios have a configured stub dependency;
  - limits are bounded;
  - no other experiment is running on the project.

  If any check fails, the assessment is **refused** and nothing runs.
- **Explicit approval** is required: the assessment waits in `awaiting_approval`, and the UI asks for consent
  that names the disruptive scenarios.
- **Abort:** checked between every step. The sandbox is removed in a `finally` block, so containers, the
  network and the volume are removed after success, errors and aborts.
- **Bounded:** each scenario has a time limit (≤ 300 s), and the whole assessment is limited to 30 min.
  Bursts are ≤ 1,000 requests × ≤ 32 concurrent.
- **Recovery:** a server restart closes jobs that were running as `failed (interrupted)`.
- **Audit:** every action is recorded with a timestamp in the assessment's audit log.

## Scenarios

| Scenario | Failure injected | Judged on |
|---|---|---|
| `dependency_unavailable` | stop the stub dependency container | containment, fail-fast, controlled errors, no leaked internals, graceful degradation, recovery, post-recovery |
| `dependency_errors` | stub answers HTTP 500 | same |
| `dependency_slow` | stub delays answers by 2× the timeout budget | fail-fast (the app's own timeout), the rest as above |
| `malformed_response` | stub answers invalid JSON | controlled errors, no leaked internals, degradation, recovery |
| `app_restart` | `docker restart` of the app container | time to healthy, post-restart correctness; data integrity is **not evaluated** unless a write/read pair is configured |
| `request_burst` | bounded burst (limits) | the process survives (no OOM kill), ≤ 1% uncontrolled errors (429/503 are deliberate), recovery |

Each dependency scenario runs these steps:
1. Baseline: every endpoint probed 3 times.
2. Inject the failure.
3. Probe until an endpoint degrades or exceeds the budget. That gives the **time to detect**.
4. Probe the failure state 3 times.
5. Restore the dependency.
6. Probe until every endpoint answers as at baseline. That gives the **time to recover**.
7. Probe the recovered state 3 times.

If the app is not healthy at baseline, the scenario is **inconclusive** and nothing is injected.

Endpoints come from the configuration, or from the app's own `/openapi.json`: GET operations without
parameters. The health endpoint is always included.

### Configuring a dependency

```json
{"scenarios": ["dependency_unavailable", "dependency_slow", "app_restart"],
 "dependencies": [{"name": "inventory", "env_var": "INVENTORY_URL", "routes": {"/stock": {"A1": 5}}}],
 "limits": {"timeout_budget_ms": 3000, "recovery_budget_s": 30}}
```

The app is started with `INVENTORY_URL=http://inventory:8080`. The stub answers the given routes with the
given JSON until a scenario changes its mode.

Unsupported:
- Real databases, Redis and message queues. Only stub HTTP dependencies are used, on the image already
  present.
- Network partitions between arbitrary containers.
- CPU or memory stress beyond the bounded burst.
- Non-FastAPI apps.
- Data integrity without a configured write/read pair.

## Resilience score

Every criterion is `passed`, `failed` or `not_evaluated`, with the evidence recorded by the probe:
status codes, latencies, container state, response bodies checked for stack traces and secrets.

- Category score = passed ÷ evaluated criteria.
- Overall score = the mean of the evaluated categories.
- Unevaluated criteria and scenarios are counted and shown. They are never scored as passes.
- The score is separate from performance and security scores.

Categories:
- containment
- timeout
- recovery
- error handling
- degradation
- data integrity
- post-recovery

## Repair workflow

1. **Propose repair** on a reproduced finding creates an Autopilot plan with `origin: "chaos"`.
   - One coding-model task, scoped to the file with the probable cause.
   - The request keeps successful responses unchanged and asks for explicit timeouts, handled dependency
     errors, and degraded answers or a deliberate 503 without exception details.
2. Approval, the isolated workspace, the correctness checks (syntax, quality gate, Bandit, tests in the
   Docker sandbox) and bounded self-repair work as in Autopilot.
3. **Chaos gate:** the finding's scenario runs against the original project and the changed copy, each in
   its own sandbox.

   | Decision | When |
   |---|---|
   | `improved` | The target criterion failed before and passes after, or the endpoints it concerned are no longer affected by the failure, and no criterion that passed before fails after |
   | `regressed` | A criterion that passed before fails after |
   | `inconclusive` | Anything else |

4. The change is written to the project only on `improved`. Otherwise the copy is discarded and nothing
   needs rolling back.
5. On `improved`, the finding becomes `verified` and its root cause `confirmed`.

## Verified behaviour (real runs, sample app in `tests/chaos/sample_project.py`)

The sample shop's `/api/products` calls an inventory service with `urllib.request.urlopen` (no timeout, no
error handling). `/api/catalog` and `/health` don't use the service.

A full assessment of 6 scenarios ran in 123 s, on Docker Desktop with Windows 11:

| Scenario | Result | Evidence |
|---|---|---|
| dependency unavailable | failed | `/api/products` answered 500 (3/3); `/health` and `/api/catalog` 100%; detected after 1.0 s; recovered 0.9 s after restore |
| dependency errors | failed | 500s; recovered after 1.4 s |
| dependency slow | failed | `/api/products` took 6,011 ms (budget 3,000 ms); answered 200 |
| malformed response | failed | 500s |
| request burst | passed | 300/300 requests 200, container alive |
| app restart | passed | healthy after 0.87 s; data integrity not evaluated |

The overall score was 77.8, with data integrity not evaluated. Root cause (probable) for every failure:
`backend/main.py:24`, `urlopen` without a timeout or error handling.

**Repair:** the local coding model (qwen2.5-coder) added `timeout=2`, caught `URLError` / `HTTPError`,
and returned `stock: null`.
- The Docker tests passed: 2.
- The re-run showed `/api/products` no longer affected (scenario passed).
- The first real run exposed a gate bug: a complete fix leaves no affected endpoint, so the gate reported
  "inconclusive". This was fixed and covered by a test.

## API

| Method | Path |
|---|---|
| GET | `/api/chaos/scenarios` |
| POST | `/api/projects/{id}/chaos/preflight` (configuration; runs nothing) |
| POST | `/api/projects/{id}/chaos/assessments` → `awaiting_approval` or `refused` |
| GET | `/api/projects/{id}/chaos/assessments`, `/assessments/{aid}` (live status, observations, report, audit) |
| POST | `/api/projects/{id}/chaos/assessments/{aid}/approve`, `/abort` |
| GET | `/api/projects/{id}/chaos/compare?first=&second=` |
| GET | `/api/projects/{id}/chaos/findings`; POST `/findings/{fid}/plan` |
| GET | `/api/projects/{id}/chaos/gates/{execution_id}` (the repair's before/after experiment) |

Assessment states: `preflight`, `awaiting_approval`, `refused`, `queued`, `running`, `recovering`,
`evaluating`, `completed`, `inconclusive`, `failed`, `aborted`.

Ownership checks work as for Autopilot. All configuration values are validated:
- dependency names;
- env var names (no `PATH`, `PYTHONPATH`, …);
- route and endpoint paths (relative, no `..`, no URLs);
- limit ranges.

Data is stored in `backend/data/chaos/` (directory set by `AIFORGE_CHAOS_DIR`).

## Troubleshooting

| Symptom | What to do |
|---|---|
| Refused: "Docker is not running" | Start Docker Desktop. Nothing runs without isolation. |
| Refused: "needs a test dependency" | Add a stub dependency with the env var your app reads its URL from. |
| Scenario `inconclusive`: "not healthy before" | The app failed at baseline. Run the Performance Engineer or the preview to see why. |
| No endpoint affected by a dependency failure | The app doesn't read the configured env var. Check its name. |
| The repair is `inconclusive` | The failure still shows, or could not be evaluated. The project was not changed. |
