# AIForge Performance Engineer

The Performance Engineer finds performance problems in a generated app, measures the app running in the
Docker sandbox, and verifies optimizations with before-and-after measurements. You approve every
optimization first.

- UI: **Engineering Suite → Performance Engineer**.
- API: `/api/projects/{id}/performance`.
- Code: `backend/performance/engineer/`.

The evidence behind each claim is labelled with one of these levels:

| Level | Meaning |
|---|---|
| **static warning** | The pattern is a problem by itself, for example `time.sleep` in `async def`, or a fetch in a `useEffect` without dependencies. |
| **hypothesis** | The pattern might matter, for example a query inside a loop. It is not measured. |
| **measured** | A baseline workload run showed it: a slow endpoint, errors under load, slow startup. |
| **proposed / applied / verified** | Plan, approved execution, and a gate decision of `improved` from before-and-after measurements. |

It replaces the old "performance engineer" chain (`profiler`, `analyzer`, `optimizer`, `benchmark`,
`regression`), which returned fixed numbers (420 ms → 118 ms). The readiness gate now uses the latest real
baseline, or reports *Not measured*.

## Supported projects

- **FastAPI backends** are measured. The entry point is `backend/main.py`, `main.py`, `app/main.py` or
  `src/main.py`, the same as the live preview.
- **React and JavaScript** get static findings only:
  - `useEffect` without dependencies that fetches;
  - the same URL fetched from several components;
  - heavy dependencies.

  Measuring and optimizing frontends comes later. Plans are refused for non-Python files.

## How a measurement works (`runner.py`, `workload.py`)

1. **Install.** Dependencies are installed into a throwaway Docker volume. No project code runs during the install.
2. **Start.** The app starts in the hardened preview container:
   - non-root user, all capabilities dropped, no-new-privileges;
   - **1 CPU, 1 GB memory, 128 processes**;
   - read-only root filesystem;
   - the project mounted read-only and copied into tmpfs;
   - port published on `127.0.0.1` only;
   - a time limit.
3. **Readiness.** The first successful answer from the health path, or `/health`, `/docs` or `/`.
   - **Startup time** runs from container start to that answer. The dependency install is excluded.
4. **Workload.**
   - **Endpoints:** the given ones, or the app's own `/openapi.json` (GET operations without path or
     required parameters).
   - **Warm-up:** unmeasured requests.
   - **Repetitions:** each one sends up to *N* requests, or for up to *T* seconds, per endpoint, with *C*
     concurrent workers (httpx, keep-alive).
   - **Latency:** wall-clock per request, from the AIForge host to the container.
5. **Resources.** Container CPU and memory are sampled with `docker stats` during the workload.
6. **Statistics:**
   - mean, median, p95 and p99 (nearest rank), throughput, error rate and status codes;
   - each repetition's median, and the **run-to-run spread**: (max − min) / median of those medians.
7. **Clean up.** Containers and volumes are always removed.

To compare two versions, the original project and the changed copy run side by side. Their repetitions
alternate (A B B A …), so drift on the machine affects both.

Function-level profiling is not run for containerized apps, and the report says so.

Limits:
- concurrency ≤ 16;
- ≤ 2,000 requests and ≤ 120 s per endpoint per repetition;
- ≤ 5 repetitions and ≤ 10 endpoints;
- the whole run is limited to `AIFORGE_PERF_DEADLINE_SECONDS` (default 1500 s).

Without Docker, nothing is measured and the run is reported as `unavailable`.

## Static findings (`static.py`)

Python rules (using `ast`):
- a query inside a loop (N+1);
- an HTTP call inside a loop;
- `json.dumps`/`loads` inside a loop;
- a nested loop over the same collection;
- a blocking call in `async def`: `time.sleep`, `requests`, a synchronous DB session;
- the same query run twice in a function;
- a GET route returning `.all()` without pagination;
- a route calling another service without caching;
- work done at import time.

Findings are linked to routes through the decorators (via the Digital Twin graph). A measured slow endpoint
is linked to the static findings in its handler.

## Plans (`service.py`)

A plan for one finding contains:
- the problem and its evidence;
- the proposed change;
- an **expected benefit, labelled as an estimate**;
- the files to change and the related tests (from the Twin graph);
- risks;
- the workload and the endpoints the plan is judged on;
- thresholds, a rollback note and completion criteria;
- a rank: measured impact × confidence ÷ files changed.

Recommendations that change behaviour (pagination, caching) are not bundled into an optimization. They
appear as separate decisions under *risks*.

Plans are created as Autopilot plans with `origin: "performance"`. That means:
- the same approval and isolated workspace;
- the same correctness checks: syntax, quality gate, Bandit, and tests in the Docker sandbox;
- **bounded self-repair**: if a model-written change makes a check regress, the failing output goes back to
  the model once.

After the correctness checks, the **performance gate** measures the original and the changed copy. The
change is written to the project only when the gate decides `improved`. Otherwise the copy is discarded,
and nothing needs rolling back.

## The performance gate (`gate.py`)

Each endpoint's median latency is compared. A change counts only if all of these hold:
- it is at least the threshold;
- it is larger than *noise_factor* × the run-to-run spread;
- every candidate repetition is faster than every baseline repetition, or the reverse;
- each version has at least two repetitions.

| Decision | When |
|---|---|
| `regressed` | Any endpoint slower beyond `max_regression_pct`, error rate up more than `max_error_rate_increase_pp`, throughput down more than `max_throughput_drop_pct`, or peak memory up more than `max_memory_increase_pct` |
| `improved` | Every target endpoint is clearly faster and nothing regressed |
| `inconclusive` | Anything else, including changes within the noise and single repetitions |
| `not_measured` | Either version could not be measured |

Default thresholds (all configurable per plan):

| Threshold | Default |
|---|---|
| Improvement | 10% |
| Regression | 10% |
| Error-rate increase | +1 percentage point |
| Memory increase | +20% |
| Throughput drop | −10% |
| Noise factor | 2× |

## Verified example (real run, sample shop app)

The sample is in `tests/performance/sample_project.py`: FastAPI + SQLAlchemy + SQLite, 300 orders with 4
items each. `GET /api/orders` loads each order's items with a separate query.

- **Analysis:**
  - static: N+1 (hypothesis, line 62) and no pagination (hypothesis);
  - baseline: `GET /api/orders` median **1,998 ms**, about 2 req/s (measured);
  - the other endpoints: 2–6 ms.
- **First attempt:** the local coding model (qwen2.5-coder) fixed the N+1 query but also added a
  `limit=10` default. The tests caught the changed response, the change was **rejected**, and the
  project was untouched. This led to keeping behaviour-changing recommendations out of plans.
- **Second attempt:** the model used `lazy="selectinload"`, which is invalid. The tests failed at import,
  so the change was **rejected**. This led to adding bounded self-repair.
- **Third attempt:** eager loading (`lazy="joined"` / `selectinload`). Tests: 2 passed in Docker. The
  gate decided **improved**:

| GET /api/orders | Before | After |
|---|---|---|
| Median | 1,934 ms | 432 ms (−77.7%; run-to-run spread 12.9%) |
| p95 | 2,280 ms | 670 ms |
| Throughput | 2.1 req/s | 9.3 req/s |
| Errors | 0% | 0% |
| Peak memory (container) | 57.0 MB | 60.9 MB (+6.8%) |

`/health` and `/api/customers/count` showed no clear change.

- **Environment:** `python:3.13-slim`, 1 CPU / 1 GB, Windows 11 host with 16 CPUs.
- **Workload:** concurrency 4, 3 repetitions of up to 100 requests or 15 s per endpoint, 20 warm-up requests.

## API

| Method | Path |
|---|---|
| POST | `/api/projects/{id}/performance/analyses` `{"measure": true, "workload": {...}}` |
| GET | `/api/projects/{id}/performance/analyses/latest` (with the baseline run) |
| GET | `/api/projects/{id}/performance/findings?evidence_kind=&category=&status=` |
| POST | `/api/projects/{id}/performance/baselines` `{"workload": {...}}` |
| GET | `/api/projects/{id}/performance/runs`, `/runs/{run_id}`; POST `/runs/{run_id}/cancel` |
| POST | `/api/projects/{id}/performance/plans` `{"finding_id", "thresholds"?, "workload"?}` |
| GET | `/api/projects/{id}/performance/plans` (ranked), `/plans/{plan_id}/report` |

Approval, execution, status and cancellation use the Autopilot endpoints with the plan's
`autopilot_plan_id`.

Security:
- Ownership is checked as for Autopilot.
- Changes are refused while a generation is paused for approval.
- Endpoint paths must be relative (`/…`, no `..`, no URLs).
- App logs and evidence are redacted.
- Measurements are stored without source code, in `backend/data/performance/`.

## Known limitations

- Only FastAPI backends are measured; React and Node apps get static findings only.
- No function-level profiling inside the container.
- Default workloads use only GET endpoints without parameters. POST and parameterized endpoints need an
  explicit workload, which you should point at test data.
- Data size matters: an N+1 pattern on a 3-row table measures as fast. Seed realistic data before measuring.
- Latency includes the host→container network path. Comparisons are fair because both versions share the
  path, but absolute numbers are machine-specific.
- The model's fix is not deterministic. Some attempts are rejected by the gates, and the report says so.

Tests: `tests/performance/test_performance_engineer.py` (20 scenarios, mocked measurements plus a real
local HTTP server for the load generator).
