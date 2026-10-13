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
- API: `/api/projects/{id}/reality` (including `/plan`, the experiment plan to approve) and `/api/reality/calibration`.
- Code: `backend/reality/` (v2: `probe.py`, `bottlenecks.py`, `calibration.py`; see below).

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

## v2: measured capacity, bottleneck findings and validated calibration

Reality Simulator v2 extends the engine above; it does not replace it. The v1 ("raw") prediction is still
made and kept, unchanged, next to the v2 prediction. Code: `probe.py`, `bottlenecks.py` and `calibration.py`
are new; `analytical.py`, `loadgen.py`, `service.py` and the Performance Engineer runner are extended.

### Why v1 was optimistic under load

v1 assumes a CPU limit is shared perfectly: `speed = cpus / workers`, then the service time is
`S / speed`. Genuine measurements on this machine contradict that. Closed-loop throughput of the sample's
`GET /api/compute` (one worker), by concurrency:

| CPU limit | c=1 | c=2 | c=4 | c=8 | c=16 | Throttled CFS periods |
|---|---|---|---|---|---|---|
| 1 CPU | 22.8 rps | 24.9 | 32.9 | **34.1** | 29.4 | 75% |
| 0.5 CPU | **11.1** | 9.3 | 11.1 | 9.7 | 8.9 | 93% |

What the table shows:
- At 0.5 CPU the real capacity is about 10 rps. v1 assumes 25 rps (20 ms ÷ 0.5), because CFS quota
  throttling costs far more than the proportional slowdown.
- At 1 CPU, one client at a time leaves the server idle while each request travels (client and Docker port
  forwarding). Capacity only shows at higher concurrency.
- Even at 1 CPU the multi-threaded server overshoots its quota and is throttled.

### Model v2 (`reality-model/2`)

The same M/G/c (Allen–Cunneen) queue, but its capacity is **measured**:

```
contention probe (closed loop, in the alternative's own container, before its load):
  S1_i        median latency at concurrency 1 (the response-time floor, network included)
  X_c,i       throughput at concurrency c in {1, 2w, 4w, 8w}  (w = workers, up to 8 s per level)
  capacity_i  = max_c X_c,i              (the peak sustained throughput)
  S_eff_i     = w / capacity_i            (effective service time per server)
  efficiency  = capacity_i / (w / S1_i)   (1 = perfect sharing; < 1 = capacity lost)
E[S] = sum_i w_i S_eff_i ;  rho = lambda E[S] / w ;  Wq, Wq95 as M/G/c (Allen-Cunneen, Cs^2 from the baseline)
R_i  = S1_i + Wq (+ D) ;  R95_i ~ 1.5 S1_i + Wq95 (+ D)
```

When the v2 prediction is made:
- **Load runs:** the probe runs in each alternative's container just before its load, and the v2 prediction
  is recorded at that moment, still before the load (`stage: before the load`).
- **Predict-only:** the baseline probe (1 worker, 1 CPU) is scaled by the v1 rule and labelled *scaled, not
  measured in this configuration*.
- **Fallback:** an endpoint the probe could not measure falls back to v1 scaling and is listed in
  `probe_fallback`.
- **No usable probe:** there is no v2 prediction (`insufficient_evidence`), and nothing is filled in.

Every prediction states:
- the method and model version;
- its calibration groups and the number of comparable observations;
- its assumptions, and the factors the runtime cannot observe (database plans, caches, background jobs,
  garbage-collection pauses, other tenants, client network variance);
- **bounds**, which are the baseline's repetition spread. These are not a statistical confidence interval.

### Measurements (and what is unavailable)

| Metric | Source |
|---|---|
| sent, succeeded, failed (HTTP status), failed (connection), timeouts, success and error rate | the load generator; failed requests always count against reliability |
| mean, median, p90, p95, p99 latency | successful requests, **nearest-rank** percentiles (the same definition as the Performance Engineer); `all_requests_mean_ms` includes failed ones |
| throughput | successful requests per second of the run |
| CPU seconds, CPU use of the limit, CFS periods, throttled periods and time | the container's cgroup `cpu.stat` (kernel counters), read with `docker exec cat` before and after the load |
| CPU % and memory (average, peak) | `docker stats` samples during the load |
| generator: AIForge process CPU time, scheduled vs achieved send rate, scheduling-lag p50/p95/p99, drops | the generator itself, measured separately from the app |
| duration and workload configuration | recorded with every run |

`provenance` names the source of each metric. A metric the runtime could not observe is `None`, with the
reason; it is never shown as 0. For example, when cgroup `cpu.stat` isn't readable, CPU saturation and
throttling are reported as **insufficient evidence**.

A run is **unsuitable for model comparison** in any of these cases:
- the generator did not sustain the rate (dropped requests, a p95 lag above 200 ms, or fewer than 95% of the
  scheduled requests sent);
- more than 1% of requests failed;
- the run was cancelled.

### Bottleneck findings

Each finding (`Simulation.findings`) records:
- an id, the kind, and the evidence strength;
- the supporting measurements and the detection method;
- the potential impact and a recommended experiment.

| Kind | Rule | Evidence |
|---|---|---|
| CPU saturation | cgroup CPU seconds ÷ (wall × CPU limit) ≥ 0.85 (`docker stats` ≥ 85% of the limit when cgroup is unavailable) | strong (moderate) |
| CPU throttling | cgroup throttled periods ÷ periods ≥ 0.25 (≥ 0.10) | strong (moderate) |
| thread contention | probe efficiency < 0.8 in this configuration | moderate: the probe can't separate the GIL from scheduling or throttling |
| insufficient worker capacity | served < 90% of offered while the CPU is < 60% of the limit (and the generator sustained); model threadpool saturation | moderate; weak (predicted) |
| external service latency | dependency run: slowed − normal ≥ 0.8 × the added latency | strong |
| memory pressure | `docker stats` peak ≥ 90% of the memory limit | strong |
| load-generator limitation | the generator did not sustain the rate; generator CPU ≥ 80% of one core | strong; moderate |
| insufficient or contradictory evidence | a shortfall or errors that no observed signal explains; missing counters; a model that predicted the opposite of what the run showed | – |

Database, cache and background-job metrics aren't observable by this runtime and are never reported. The
v1 bottleneck list (`bottlenecks`) is kept as before.

### Calibration v2 (`median-ratio, leave-one-out validated (calibration/2)`)

Each comparable run adds one record per model (raw and v2) and metric. A record holds:
- the prediction made **before** the run (`predicted_at`) and the measured outcome;
- the absolute and relative error (`observed / predicted − 1`, so a value above 0 means the model was
  optimistic);
- the group, and the calibration method and version.

**Groups.** Records are combined only within a group:
`model version | method | metric | kind | stable/saturated | workers | CPU limit | utilisation band`.
The utilisation band is low (< 0.5), mid (< 0.85) or high. Records written before v2 stay in their own
legacy groups.

**Per group:**
- **Bias** is the mean relative error.
- **Correction** is the median of observed ÷ predicted.
- **Validation is leave-one-out.** Each record is corrected with the factor from the *other* records only.
  The correction's accuracy is reported only from those held-out errors, never from the records it was
  fitted to.
- **Established** means at least **5** comparable runs (the v1 minimum, unchanged).
- **Applied.** A calibrated value is attached to new predictions only when the group is established *and*
  the held-out error after correction is lower than the raw model's error on the same runs. Otherwise the
  prediction carries no calibrated value, together with the reason.
- **Error range.** The held-out error range shown with a calibrated value is empirical. It is labelled as
  not a statistical confidence interval.

### Safe experiments

`POST /api/projects/{id}/reality/plan` returns the experiment plan. It lists:
- every step, with its container (workers, CPU, memory) and workload (pattern, rate, duration, maximum
  requests, probe levels);
- the limits, isolation and cleanup;
- a hash.

A load run through the API needs `approved: true` **and** that plan's hash, so the approval covers exactly
what was shown. The UI shows the plan and asks for approval of it.

The safety caps are unchanged: 200 rps, 120 s, 20,000 requests, 1–4 workers, 0.25–2 CPUs, 128–2048 MB, 10 s
per request, 256 requests in flight and 1800 s per simulation.

Isolation is the same as v1:
- the hardened preview container, with the port on 127.0.0.1 only;
- the Chaos sandbox for dependency runs;
- traffic goes only to containers started for the run, never to a live service.

Cleanup runs after success, failure, cancellation or timeout. It is **verified**: the run's containers and
volumes are listed afterwards, and `cleanup.verified` records that none remain.

### Comparison report

For each alternative the report shows:
- raw and v2 predictions against the measurement, with absolute and relative error;
- the calibrated value and its error, when a validated correction exists;
- the resource configuration and workload;
- whether the generator sustained the rate;
- whether the run is comparable (and why not);
- each calibration group's record count and whether it is established.

Discrepancies are explained with the observed counters (CPU use, throttling, probe efficiency, generator
CPU) and the assumption each model makes. A failed or overloaded run is reported, but it is never a
calibration observation.


### v2 measured results (genuine runs on this machine)

The sample app's `GET /api/compute` endpoint (fixed CPU work), seven rounds, each against fresh containers
(21 runs):
- scenario A: 15 rps for 20 s, with 1 worker / 1 CPU and with 2 workers / 2 CPUs;
- scenario B: 6 rps for 20 s, with 1 worker / 0.5 CPU.

Every run was comparable: the generator sustained the rate, 0% of requests failed, and cleanup was verified.

Mean-latency error, as relative error observed ÷ predicted − 1 (positive means the model was optimistic):

| Configuration | Observed mean | Raw v1: mean \|error\| (bias) | v2: mean \|error\| (bias) | Throughput error (v2) |
|---|---|---|---|---|
| 1 worker, 0.5 CPU (CFS throttled in 28–37% of periods) | 117–165 ms | 77.5% (+77.5%) | **24.0%** (+21.1%) | 12.4% |
| 1 worker, 1 CPU (throttled in 9–18% of periods) | 100–130 ms | 137.1% (+137.1%) | 114.6% (+114.6%) | 8.3% |
| 2 workers, 2 CPUs (no throttling) | 57–65 ms | 93.2% (+93.2%) | **24.4%** (−24.4%) | 8.3% |

Leave-one-out evaluation of the calibration groups (mean latency):

| Group | Records | Raw error | Error after held-out correction | Correction |
|---|---|---|---|---|
| v2, 0.5 CPU, mid utilisation | 6 | 21.1% | 10.5% | ×1.25, validated |
| v2, 1 CPU, mid utilisation | 6 | 105.4% | 17.4% | ×2.02, validated |
| v2, 2 workers / 2 CPUs, low utilisation | 7 | 24.4% | 5.7% | ×0.78, validated |
| raw v1, 0.5 CPU, low utilisation | 7 | 77.5% | 19.7% | ×1.90, validated |
| raw v1, 2 workers / 2 CPUs, low utilisation | 7 | 93.2% | 18.0% | ×1.80, validated |
| raw v1 and v2, 1 CPU, the other utilisation band | 1–4 | – | – | insufficient history |

The calibrated values attached to predictions in rounds 5 and 6 came only from earlier runs, so they are
genuinely out of sample. Their errors were:
- 2 workers: −5% and +3%;
- 1 CPU: −8%;
- 0.5 CPU: +14%.

That is four predictions, too few for any accuracy claim beyond these runs.

What the numbers say:
- **CPU-limited and multi-worker configurations.** Measuring capacity removes most of v1's error: from 77%
  to 24%, and from 93% to 24%.
- **1 CPU.** v2 is still strongly optimistic (+115%). Throttling is only 9–18% of periods there, so the
  remaining gap is something the closed-loop probe doesn't capture. Candidates are open-loop burstiness
  combined with GIL contention, and the generator sharing the host. The runtime can't separate these, so the
  gap is reported, not explained away.
- **2 workers.** v2 is pessimistic: the probe's one-at-a-time latency (about 85 ms) exceeds what this
  configuration shows under load.
- **Calibration.** The per-configuration corrections are consistent enough to pass held-out validation. They
  are empirical corrections for this machine; they are not general accuracy claims.

A first evidence run used a probe without warm-up; it was stopped and discarded (the probe now warms every
worker before measuring). The utilisation band can split one configuration across two groups when its
predicted utilisation sits near a band edge (as with 1 CPU here, 6 + 1 records). Each group still needs its
own 5 runs.

## Limitations

- v2's capacity comes from a short closed-loop probe. It doesn't capture contention that only appears under
  open-loop bursts, and at 1 CPU v2 still underestimates latency by about 2x on this machine. Calibration
  corrects such a bias only once a group has 5 comparable runs and the correction beats the raw model on
  held-out runs.
- Calibration groups are per machine in effect: records don't carry a hardware identity, and the corrections
  measured here aren't valid elsewhere.
- A hard-killed AIForge process can't run its cleanup. The app container stops itself by its time limit, but
  its dependency volume remains until removed. Normal completion, failures, cancellation and timeouts are
  cleaned up and verified.
- cgroup counters need a Docker host that exposes `cpu.stat` inside containers. Elsewhere, CPU saturation and
  throttling are reported as insufficient evidence.
- The model is deliberately simple. It doesn't model the database, locks, the GIL's effect on threads,
  garbage collection, or network variance.
- The generator runs on the same machine as Docker, so at higher rates it competes with the app. When it
  falls behind, the comparison is withheld.
- Only GET endpoints without path parameters can be driven, and request payloads aren't varied.
- Dependency-latency runs use the Chaos sandbox's fixed single worker and low load (no queueing).
- Cache hit rate, database growth and background jobs aren't modelled. They are listed as unknown, not
  guessed.
- Calibration needs repeated comparable runs before any accuracy statement is meaningful.
