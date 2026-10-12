# AIForge Reality Simulator

> Test the future before building it. Predictions are labelled as predictions until a run measures them.

Describe a hypothetical situation: traffic shape and rate, the endpoint mix, worker and CPU settings, an
external dependency getting slower. The simulator then:

1. builds an **application model** from real evidence;
2. **measures** your app's per-request service times at low load in an isolated container;
3. **predicts** the scenario with a documented queueing model;
4. if you approve, **runs** the workload against isolated copies of the app;
5. **compares** predictions with observations and records each pair for calibration.

- UI: **Engineering Suite → Reality Simulator**.
- API: `/api/projects/{id}/reality` and `/api/reality/calibration`.
- Code: `backend/reality/`.

## Three kinds of number

| Kind | Source | Shown as |
|---|---|---|
| assumption | you: rate, pattern, mix, resources, dependency latency, prices, free-text assumptions | "assumption" |
| measured | a run against an isolated copy, with its environment | "measured" |
| predicted | the analytical model, from measured inputs and assumptions, with formulas and bounds | "analytical estimate (not a measurement)" |

A prediction is never stored or shown as a measurement. Unknown facts (background jobs, production data
volume, real traffic shape) are listed as unknown, never invented.

## Application model

The model comes from the Digital Twin graph and the code:
- **Routes:** method, path and `file:line`. Only GET routes without path parameters are marked measurable.
- **Outbound calls:** HTTP calls (`requests`, `httpx`, `urllib`, `aiohttp`) and database connections,
  each with its `file:line`.
- **Static suspicions:** from the Performance Engineer's static analysis (for example N+1 queries).

## Scenario limits

Scenarios are validated before anything runs:

| Setting | Limit |
|---|---|
| Traffic pattern | `constant`, `ramp` (start → end rate) or `burst` (a base rate with a peak in the middle) |
| Rate | at most **200 requests/s** |
| Duration | at most **120 s** |
| Total requests | at most **20,000** |
| Endpoint mix | weights over GET endpoints without path parameters |
| Workers | 1–4 |
| CPU limit | 0.25–2 |
| Memory | 128–2048 MB |
| Alternatives | up to 4 per scenario |
| Dependency latency | 0–5000 ms. It needs the list of endpoints that call the dependency, and, to be measured, the stub definition (name, env var, routes), the same as in the Chaos Engineer. |

Running the workload needs explicit approval.

## Analytical model

The model is M/G/c with the **Allen–Cunneen** approximation. It falls back to M/M/c (Erlang C) when the
baseline lacks the spread needed to estimate service-time variability. Its formulas are returned with every
prediction:

```
speed = min(1, cpus / workers);  S'_i = S_i / speed
E[S] = sum_i w_i S'_i;  a = lambda E[S];  rho = a / workers
C(c,a) = (a^c/c! * c/(c-a)) / (sum_{k<c} a^k/k! + a^c/c! * c/(c-a))
Wq = C / (c/E[S] - lambda);  Wq95 = max(0, ln(C/0.05) / (c/E[S] - lambda))
R_i = S'_i + Wq (+ D);  R95_i ~ 1.5 S'_i + Wq95 (+ D)
rho >= 1: X = c/E[S]; queue growth = lambda - X; mean over T ~ E[S] + (lambda - X) T / (2X)
rho_threads = sum_dep lambda_i (S'_i + D) / (40 * workers)
M/G/c: Wq, Wq95 x (1 + Cs^2)/2,  Cs = ((p95 - p50)/1.645) / mean  (from the baseline)
```

**Inputs.**
- `S_i` is the measured median per-request time at low load: one request at a time, three repetitions,
  1 worker and 1 CPU.
- The **bounds** come from the fastest and slowest repetition medians.

**Assumptions** (also listed in every result):
- Arrivals are Poisson and service times exponential.
- The work is CPU-bound Python, so one worker uses at most one CPU.
- A CPU limit below the worker count slows the workers proportionally.
- Dependency waits use no CPU but hold one of the 40 threadpool slots per worker.
- The database is inside the measured service time.

**Ramp and burst scenarios** are evaluated at the peak rate. They also report the predicted *saturation
onset*: the first second at which the offered rate exceeds the predicted capacity.

## Execution

**Configuration alternatives** run one at a time, each in a fresh preview container (non-root, read-only,
no extra capabilities) with that alternative's workers, CPU and memory:
- Load comes from an **open-loop generator**: Poisson arrivals at the pattern's rate, seeded, with the
  endpoint picked by weight. Unlike closed-loop workers, queues can really build up.
- Container CPU and memory are sampled with `docker stats`.
- Requests the generator could not send (too many in flight), and its own scheduling lag, are reported as
  **limits of the test rig**. A run limited by the generator isn't compared with the model.

**Dependency-latency alternatives** run in the **Chaos Engineer's** isolated network with its stub:
1. The endpoints that call the dependency are probed at low load with the stub at normal speed.
2. The stub is slowed by the scenario's latency, and the endpoints are probed again.
3. The prediction is the normal latency plus the added latency, a no-queue additive model.

Everything is cleaned up, cancellation is checked between steps, and a simulation has a 30-minute limit.

## Comparison and calibration

**What is compared** (constant scenarios): throughput, plus mean and p95 latency when the model doesn't
predict saturation. A metric is "within" if the observation falls inside the prediction's bounds or
within 10% of it.
- Ramp and burst runs are compared by saturation onset only. The observed onset is the first second whose
  p50 is twice the service time, or that has errors.
- Each mismatch is explained with its likely causes: contention the model doesn't capture, such as the
  GIL, the database, or the generator sharing the machine; or caching effects.

**Calibrated estimates.** Once a comparable group has at least 5 records, new predictions also carry a
**calibrated estimate**: the model value times the median observed/predicted ratio of those runs, with the
ratio range and the number of runs. It is an empirical correction for that machine and is still labelled as
an estimate. With less history it shows "insufficient history", and no correction is made.

**Calibration.** Every compared pair becomes a calibration record: method, metric, inputs, revision,
predicted value, bounds, observed value and error.
- `/api/reality/calibration` aggregates records **only within the same comparable key** (method, metric,
  load or dependency, saturated or stable).
- Fewer than 5 records in a group is reported as **insufficient history**. No accuracy claim is made
  without them.

## Capacity analysis, cost and recommendation

Bottlenecks are labelled by the evidence behind them:

| Label | When |
|---|---|
| **measured bottleneck** | served under 90% of the offered rate, errors above 1%, or CPU at 85% or more of the limit |
| **model-predicted bottleneck** | utilisation of 0.85 or more, or threadpool saturation |
| **static-analysis suspicion** | a Performance Engineer static finding on an endpoint in the mix |
| **insufficient evidence** | no baseline for the endpoint |

**Resource need:** vCPUs = λ · E[S at 1 CPU] / target utilisation. A **cost** is estimated only from unit
prices you enter (per vCPU-hour and per GB-hour); no pricing data is built in. Without prices, the cost is
"not estimated".

**Recommendation:** the alternative with the lowest latency (measured if run, otherwise predicted), using
the fewest workers × CPUs among those within 10% of the best. It always says whether it rests on a
measurement or a prediction, and suggests next experiments. Code-level options such as caching or query
changes are evaluated by the Evolution Engine, not here.

**Report:** Markdown or JSON (`/report`), redacted, with predicted and measured values side by side and
the limitations.

## Measured results (genuine runs on this machine)

The sample (`tests/reality/sample.py`) is a FastAPI app with CPU-bound endpoints and a checkout endpoint that
calls a payments service. The scenario was 20 requests/s, constant, for 20 s.

| Alternative | Predicted mean | Observed mean | Notes |
|---|---|---|---|
| 1 CPU | 26.8 ms (M/G/c) | 63.6 ms | Throughput 20.0 predicted vs 20.9 observed |
| 0.5 CPU | 120 ms, not saturated | 3.6 s, saturated at 11 rps | Docker's CPU-quota throttling and threadpool/GIL contention, which the model doesn't capture |
| Payments +200 ms (Chaos stub) | 216 ms | 210 ms (−2.9%) | Within tolerance |

Two earlier runs exposed mistakes that are now fixed:
- **A flawed sample.** The sample used a wall-clock wait instead of CPU work, so the CPU limit had no
  effect.
- **A pessimistic model.** Plain M/M/c overestimated waiting for steady service times (−32% on the mean), so
  the model became M/G/c.

The remaining underestimation under load is exactly what the calibration records hold; after five
comparable runs it becomes a calibrated correction. These numbers are from one machine and are **not** a
claim of accuracy.

## Limitations

- The model is deliberately simple. It doesn't model the database, locks, the GIL's effect on threads,
  garbage collection, or network variance.
- The generator runs on the same machine as Docker, so at higher rates it competes with the app. When it
  falls behind, the comparison is withheld.
- Only GET endpoints without path parameters can be driven, and request payloads aren't varied.
- Dependency-latency runs use the Chaos sandbox's fixed single worker and low load (no queueing).
- Cache hit rate, database growth and background jobs aren't modelled. They are listed as unknown, not
  guessed.
- Calibration needs repeated comparable runs before any accuracy statement is meaningful.
