# AIForge Evolution Engine

> Every experiment makes AIForge a better engineer.

The Evolution Engine turns an improvement opportunity into a measured experiment:
1. It plans the experiment.
2. It generates several candidate implementations in isolated copies.
3. It evaluates every candidate with the same tests, security re-check and measurements.
4. It selects one by deterministic rules.
5. It records what happened.

Nothing reaches the project until a person approves it. Promotion re-checks everything and rolls back if
the final tests fail.

It does not train or change a model. "Learning" here means that recorded, measured outcomes are
retrieved, with their scope, when similar work is planned.

- UI: **Engineering Suite → Evolution Engine**.
- API: `/api/projects/{id}/evolution-engine`.
- Code: `backend/evolution_engine/`.

## What is implemented (vertical slice)

| Area | Status |
|---|---|
| Opportunity discovery | Performance Engineer N+1 findings on GET endpoints without path parameters can be experimented on. Verified Security Guardian findings are listed but not experimented on (they are fixed through the Guardian). |
| Candidate strategies | N+1 with raw SQL (`join_query`, `batch_in_query`, `single_query_aggregate`) or SQLAlchemy (`eager_selectinload`, `eager_joinedload`, `batch_in_query`), 1–3 per experiment |
| Evaluation | Correctness (the project's tests in the Docker sandbox), security (Security Guardian static re-check), performance (side-by-side measurement), resources, maintainability (changed lines, branch count). Resilience is shown as `not_evaluated` because no Chaos scenario applies to this kind of opportunity. |
| Selection | Deterministic: mandatory constraints first, then weighted ranking, with every input shown |
| Engineering Memory | Persistent, applicability-labelled retrieval; failed strategies are suppressed; past wins come first |
| Promotion | Approval bound to the source revision and patch hash; Autopilot apply with a re-measure gate; final tests; rollback |

Other opportunity categories (caching, refactoring, error handling, dependency changes) are **not**
implemented yet.

## Architecture

| Module | Responsibility |
|---|---|
| `models.py` | Opportunity, ExperimentPlan, Candidate, Approval, Promotion, Experiment, MemoryRecord. Measured fields are kept separate from model configuration. |
| `discovery.py` | Opportunities from existing evidence (no new scanners), priority from configurable criteria |
| `planner.py` | Hypothesis, baseline, strategies, workload, thresholds, weights, limits, safety, cleanup; rejects plans that cannot be evaluated |
| `service.py` | Experiment lifecycle (snapshot, candidates, evaluation, measurement), approval, promotion, rollback, and the Autopilot gate |
| `selection.py` | Deterministic constraints and ranking |
| `memory.py` | Records, applicability, strategy guidance |
| `routes.py` | REST API |
| `frontend/src/pages/EvolutionEnginePage.jsx` | Opportunity explorer, planner, live monitor, candidate comparison, promotion, memory |

Reused rather than duplicated:
- **Autopilot:**
  - the isolated workspace;
  - the check runner, with the project's tests in the Docker sandbox;
  - the correctness comparison;
  - the secret-hiding model call, now `executor.model_changes`;
  - plans, approval and the executor;
  - the patch engine apply and rollback (`apply_all`);
  - the measured-gate stage (`MEASURED_GATES["evolution"]`).
- **Performance Engineer:**
  - static N+1 detection;
  - its latest measured runs;
  - the side-by-side runner (alternating repetitions in hardened containers);
  - the noise-aware performance gate.
- **Security Guardian:** static analysis of each candidate compared with the snapshot.
- **Digital Twin:** the dependents of the changed file.

## Experiment lifecycle

1. **Discover** (read-only). The test-runner probe runs on a disposable copy, because the runner adds
   package markers to the folder it inspects.
2. **Plan.** The plan records:
   - the hypothesis;
   - the baseline (the project, measured in the same run);
   - strategies, ordered and filtered by Engineering Memory;
   - the workload (5 × 150 requests on the target endpoint, concurrency 2, 30 warm-up requests);
   - thresholds: target at least 10% faster and beyond 2× the run-to-run spread; no endpoint more than
     15% slower; error rate, throughput and memory limits;
   - ranking weights;
   - allowed files (the finding's file only);
   - limits: 1 h, and an app container of 1 CPU / 1 GB / 128 processes;
   - the cleanup steps.

   A plan is **rejected** when the result could not be judged reliably:
   - no route to measure, or path parameters;
   - not a FastAPI app the sandbox can start;
   - **no tests**;
   - fewer than 2 repetitions;
   - more than 3 candidates;
   - every strategy previously failed here.
3. **Run.** This needs explicit approval.
   1. The project is copied once into a frozen snapshot, and its **source revision** is recorded: a
      SHA-256 of all source files.
   2. Each candidate gets its own copy of that snapshot, so candidates cannot see or overwrite one
      another, and the project is never touched.
   3. The coding model, or a fixed generator in tests, writes each candidate. Each model call is
      limited to the plan's files, and lines holding secrets are hidden from it. There are 2 bounded
      attempts with feedback.
   4. Identical patches are marked `duplicate`.
4. **Evaluate** every candidate the same way:
   - **Correctness.** Autopilot's checks, with the project's tests in the Docker sandbox, compared with
     the baseline.
     - A test failure is re-run once. If it passes the second time, it is `flaky`, not a defect; if it
       fails again, it is reproduced.
     - Checks that could not run (`blocked` or `error`) are an **infrastructure** failure, never a
       candidate defect.
   - **Security.** New critical or high Guardian findings in the changed files are a mandatory failure.
     Lower-severity ones reduce the score.
   - **Performance.** The snapshot and every candidate that is still eligible are measured **in one run,
     side by side, with alternating repetitions**, so they face the same conditions. Each candidate is
     judged by the performance gate:
     - per endpoint, median latency;
     - the change must exceed both the threshold and 2× the run-to-run spread;
     - the repetitions must not overlap;
     - at least 2 repetitions are needed;
     - regressions in latency, error rate, throughput or memory are checked.
   - **Measurements that do not exist are never filled in.** A candidate that failed earlier is
     `not_measured`; Docker being unavailable gives `not_measured` (infrastructure).
5. **Select** (`selection.py`, no model input).
   - Mandatory constraints: `generated`, `correctness`, `security`, `performance` (measured and not
     regressed).
   - Eligible candidates are ranked by weighted scores for performance, security, reliability,
     maintainability and resource efficiency. Each input, score, weight and contribution is stored.
   - Only a winner whose target was measured faster beyond the noise becomes `awaiting_approval`.
   - Otherwise the outcome is:
     - `no_improvement`: changes below the threshold;
     - `inconclusive`: a large change that the noise would not confirm, missing evidence, a flaky test or
       an infrastructure failure;
     - `regression`: every candidate broke a constraint;
     - `failed`: nothing was generated, or the plan was rejected.
6. **Record** one Engineering Memory record per candidate. Each holds the strategy, the result, the
   reasons, the failure kind, the measured change with repetitions and noise, the evidence quality
   (strong, moderate, weak or insufficient), and its scope.
7. **Approve.** Only the selected candidate can be approved, and only while the project still has the
   experiment's source revision. The approval stores that revision and the candidate's patch hash.
8. **Promote.**
   - The approval is **invalidated** if the project or the patch changed since it was given.
   - Otherwise an Autopilot plan (`origin: evolution`, `write_files`) carries exactly the approved
     files:
     1. isolated copy;
     2. checks, including tests in Docker;
     3. the **Evolution gate**: the same workload and thresholds, measured on the project and on the
        changed copy;
     4. apply through the patch engine, only on `improved`.
   - The project's tests then run on the promoted project. If they do not pass, the files are restored
     to their exact previous contents (`rolled_back`, outcome `regression`).
   - The final outcome is written to the experiment and to its memory records.

## Engineering Memory

| Applicability | Meaning |
|---|---|
| `direct` | The same project, file and kind of problem |
| `related` | The same kind of problem with the same data-access style elsewhere |
| `weak` | The same kind of problem with a different data-access style: an analogy, not evidence |

How memory affects planning:
- A strategy that failed with a **candidate defect** in the same place is not proposed again unless the
  user gives a written justification (`overrides`).
- Failures caused by infrastructure or flaky tests are never held against a strategy.
- Strategies that won with strong or moderate evidence are tried first.

Each record states that it is not a general rule. Records from other projects are shown without their
file paths.

## Safety

- The original project is not modified until promotion, and promotion requires approval.
- Generated code runs only in containers: tests in the Docker sandbox (no network, non-root), and the
  app in the hardened preview container.
- Model output is treated as untrusted:
  - paths are validated;
  - candidates may change only the plan's files;
  - SQL must use bound parameters, and the Guardian re-check enforces this.
- Every workspace, container and volume is removed in `finally`.
- Only one Evolution job runs per project. Experiments can be aborted, and they have a time limit.
  Experiments interrupted by a restart are closed as failed.

## Measured results (genuine Docker runs on the sample app)

The sample is `tests/evolution_engine/sample_project.py`: 400 authors, an N+1 endpoint, and tests that
pin the exact response.

Experiment, with a 3 × 60 request workload:
- **c1 `join_query`** passed its tests (3 passed). It was measured at **25.0 → 9.7 ms median (−61%)**,
  beyond 2× the run-to-run spread (19%), and was selected.
- **c2 `batch_in_query`** silently dropped authors without books. Its tests failed (1 passed, 2 failed),
  the failure reproduced on a re-run, and it was rejected as a candidate defect. It was never measured.
- The original project was unchanged.

Promotion with that workload:
- The re-measurement saw −73%, but the baseline's repetitions varied by 70%.
- The gate returned `inconclusive`, so Autopilot **refused to apply**.
- That led to the larger default workload (5 × 150 requests). The end-to-end test now runs with it.

Exact numbers vary by machine. The test report records them.

## Limitations

- Only N+1 queries on FastAPI GET endpoints without path parameters can be experimented on.
- The response is checked through the project's own tests. There is no separate response-equivalence
  probe, so a project with weak tests can accept a behaviour change.
- Maintainability is approximate: changed lines and the change in branch count.
- Resilience is not evaluated for this opportunity type.
- Measurements share the machine with everything else running on it. The noise rules make results
  inconclusive rather than wrong, but a noisy machine can block a real improvement.
- Engineering Memory is retrieval and ranking only. There is no fine-tuning and no automatic
  generalisation.

## Related fix found while building this

The performance gate measured run-to-run noise relative to each version's own median. For a candidate
eight times faster, the small median made its spread look like 124%, so a real −88% change could never
be confirmed. Noise is now the larger absolute spread of the two versions' repetitions, expressed
relative to the baseline median. With 5 or more repetitions the single highest and lowest repetition are left
out of that spread (a real run had one disturbed baseline repetition at 28 ms among 49–65 ms that tripled the
noise estimate); every repetition must still be separated from the other version's. Regression tests are in
`tests/performance`.
