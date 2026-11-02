# AIForge Time Machine

> Every change has a history. Every failure has an explanation — when the evidence supports one.

The Time Machine records what AIForge's subsystems actually do in an append-only, hash-chained ledger. It
uses that ledger to show a project's history, how events relate, and what each task changed. From the
same records it can:
- create checkpoints and restore them safely;
- run the **Regression Detective**, which finds and verifies the change behind a failing test;
- re-run a recorded Autopilot or Evolution task in isolation.

- UI: **Engineering Suite → Time Machine**.
- API: `/api/projects/{id}/time-machine`.
- Code: `backend/time_machine/`.

## What is recorded, and by whom

Only subsystems that did something emit events (`recorder.emit`). The ledger never infers events.
Recording is best effort: a recording failure is logged and never fails the engineering task.

| Subsystem | Events |
|---|---|
| Generation pipeline (`generation/store.py`) | `task_created` (the prompt, redacted, and model environment), `agent_started` / `agent_completed` per agent, `artifact_generated` (project written), `task_completed` / `task_failed` |
| Autopilot (`executor.py`, `service.py`) | `approval_granted` / `approval_rejected`; `agent_started` (with configuration); `test_executed` for the baseline and for the changed copy (with environment and counts); `patch_applied` (each file's exact before and after content, by hash); `task_completed` / `task_failed` |
| Security Guardian | `security_finding` (assessment summary), `security_verification`, `approval_granted` (accepted risk) |
| Performance Engineer | `performance_measured` (per-endpoint medians, workload and environment) |
| Chaos Engineer | `resilience_assessed` |
| Evolution Engine | `experiment_evaluated` (candidates, model configuration, source revision), `approval_granted`, `rollback_performed` (with file versions), `task_completed` / `task_failed` |
| Time Machine | `checkpoint_created`, `restore_previewed`, `restore_performed`, `investigation_completed`, `rerun_completed` |

Subsystems that are known to be simulated, such as browser testing, do not emit ledger events.

**Not yet instrumented.** The generation pipeline's file contents (only the final project is
fingerprinted), the Benchmark Lab, and the Digital Twin's own analyses. History from those is incomplete,
and the UI says so where it matters (for example, replay shows gaps).

The older **Flight Recorder** events are shown read-only as *legacy*. They are not hash-chained, and some
of the subsystems that wrote them were simulated.

## Event schema

Each event has these fields:
- `id`, `seq`, `project_id`, `task_id`, `type`, `at`, `source`, `summary`, `outcome`;
- `revision` (source-tree fingerprint) and `git_commit` (when the project is a git repository);
- `parents` (recorded causal links) and `refs` (plan, execution, experiment and other ids);
- `files`: `{path, before, after, change, content_stored}`, where `before` and `after` are content hashes;
- `data` (small, redacted details), `config` (model, generator, workload and sandbox), `error`;
- `prev_hash` and `hash`.

Event types are a fixed vocabulary, and outcomes are validated. A **correction** is a new event that
references the corrected one. Nothing is ever rewritten.

## Storage, integrity and retention

| What | Where and how |
|---|---|
| Ledger | `backend/data/time_machine/ledger/<project>.jsonl` (git-ignored): one JSON line per event, `hash = sha256(prev_hash + canonical event)`, `fsync` on every append. `verify` recomputes the chain; the timeline shows its integrity, and editing any line breaks it from that line on. |
| File versions | `backend/data/time_machine/blobs/<sha256>`, content-addressed and stored once. Every read re-checks the hash, so damaged content is never served. |
| Jobs | Investigations and reruns: `backend/data/time_machine/jobs`, the latest 50 per project |
| Location | `AIFORGE_TIME_MACHINE_DIR`. The test suite points it at a temporary folder. |
| Retention | The ledger and file versions are kept until deleted. There is no automatic pruning yet. |

## Secret redaction

- Every string in `summary`, `error`, `data`, `config` and `refs` is redacted before it is written.
- A file whose content holds secret-like values is **hashed but not stored**.
  - Its change is recorded with `content_stored: false`.
  - Replay shows the diff as unavailable.
  - Restoring it is `unavailable`; it is never restored with placeholder text.
- Files larger than 512 KB or that aren't UTF-8 are also not stored.

## Revisions

`revision` is the SHA-256 over the sorted `path + sha256(content)` of the project's source files (the
files a working copy holds). It is the same function that `evolution_engine.service.source_revision`
uses.

Sorting is by the path string, so the fingerprint is the same on every platform. Sorting `Path` objects
was case-insensitive on Windows and gave a different order.

Exact bytes are recorded, so CRLF files keep their line endings.

## Timeline and causal graph

- The **timeline** is filterable by type, source, outcome, task, file and text. Pages hold up to 200
  events, and each row can be expanded to its recorded fields.
- The **graph** shows events in lanes by source, with three kinds of edge:

  | Edge | Meaning |
  |---|---|
  | `recorded` | A causal link the emitting subsystem recorded, for example approval → execution → tests → patch → completion |
  | `temporal` | Ordered within the same task with no recorded link: shown as an association, not causation |
  | `file` | A later event changed the same file |

  When the graph is filtered by task, it includes that task's recorded ancestors (for example, the
  approval that started it).

## Replay and reruns

**Historical replay** (`GET /replay/{task}`) returns a task's recorded steps in order, with diffs
reconstructed from the stored file versions. **Nothing is executed.** If a completion was never
recorded, the replay is marked incomplete.

An **experimental rerun** (`POST /reruns`) works like this:
1. The starting revision of a recorded Autopilot execution, or an Evolution experiment's source revision,
   is reconstructed from recorded changes.
2. It is written into an isolated folder.
3. The task runs again there, with today's configuration, under a **separate history id** so its events
   can never look like changes to the project.
4. The result reports the recorded and current configuration, which keys differ, per-file whether the
   output is identical to the recorded one, and recorded versus rerun test results and environments.

A rerun is **never** called a reproduction: model output, dependencies and environments can differ.

## Regression Detective

`POST /investigations` starts an investigation. It never changes the project.

1. The project's tests run on an isolated copy of the current state. If they don't fail, the result is
   `not_reproduced`. A failure is re-run once; if it then passes, it is flaky and not investigated.
2. Earlier states are reconstructed by reverting recorded changes (`patch_applied`, rollbacks, restores)
   from the newest back. A change is reverted only if the files still hold exactly what it wrote. An
   unrecorded edit stops the walk; this is reported as a limitation, and nothing is overwritten.
3. **Known-good** is the newest reconstructed state whose revision matches a recorded passing test run.
   If none matches (for example, a person added a test, which changes every revision), it is the oldest
   reconstructable state. Either way it is tested now, and if it doesn't pass the result is
   `inconclusive`, because the environment may be the cause.
4. The changes between known-good and now are bisected. Each state is materialized in its own folder and
   tested, with at most 12 test runs.
5. Isolation checks:
   - The suspected change is reverted from the current state alone (and only if no later change touched
     its files), and the tests run.
   - Where possible, the change is also applied alone on the known-good state.
6. The verdict:

   | Verdict | When |
   |---|---|
   | `confirmed` | An exact pass→fail transition at this change, **and** reverting only this change makes the tests pass. If the change could be applied alone, it also made them fail. |
   | `probable` | One isolation check supports the change, the other doesn't |
   | `hypothesis` | The search didn't narrow down to one change, or isolation didn't support it |
   | `inconclusive` / `not_reproduced` | As described above |

   A change is never blamed just because it happened shortly before the failure.

7. The proposal is a revert of the suspected change. Restoring it goes through the safe restore below.

Every test run is listed with the state it tested, the result, the environment and the failing tests.

## Checkpoints and safe restoration

**A checkpoint** records:
- the source-tree fingerprint;
- every source file (by content hash, stored unless secret-bearing or binary);
- the latest recorded test outcome.

**Preview** (`POST /restore/preview` with a `checkpoint_id` or a `revert_change_id`) classifies every
file that would change:

| Action | Meaning |
|---|---|
| `restore` | The current content was written by a recorded AIForge change, so it is safe to replace |
| `conflict` | The current content wasn't produced by any recorded change: a person or another session edited it. **It is never touched.** |
| `unavailable` | The target content wasn't stored |

The preview returns a token: the hash of the current revision, the target and the planned rows.

**Isolated restore** (`POST /restore/isolated`) rebuilds the target in a separate folder and runs its
tests there. The project is not touched.

**Restore into the project** (`POST /restore`) needs `approved: true` and the preview's token, which
must still match: if the project changed since the preview, the restore is refused. Then:
1. A recovery checkpoint is created.
2. Only the `restore` rows are written, through the patch engine.
3. The project's tests run.
4. The restore is recorded with the files' before and after versions, so it can itself be undone.

## Limitations

- History starts when this ledger was added. Work done earlier only appears through the legacy Flight
  Recorder view.
- Reconstruction needs every file change between the states to have been recorded. Edits made outside
  AIForge, or files that weren't stored, limit how far back the Detective and reruns can go, and they say
  so.
- Bisecting assumes the project's tests detect the regression. A regression the tests don't catch can't
  be investigated.
- Reruns cover Autopilot executions and Evolution experiments. Full multi-agent generation reruns aren't
  implemented.
- The graph is a simple lane layout. Very large histories are limited to the latest 300 events per view.
- Revision comparison covers checkpoints, tests and performance runs. Agent-decision diffs between two
  generations aren't implemented.

## Tests

`tests/time_machine/test_time_machine.py` covers:
- ledger order, the hash chain and tamper detection;
- validation, corrections and redaction;
- content integrity and pagination;
- recording that never breaks the caller, and fingerprints;
- real Autopilot executions producing linked events with exact file versions;
- timeline, graph and replay, including missing content;
- previews that never overwrite unrecorded work;
- approval and stale-token enforcement, recovery points and isolated restore;
- the Detective: confirmed, not reproduced, and limited by unrecorded edits;
- isolated reruns that don't touch the project's history;
- API access and flows, and the page.

The genuine test runs the whole scenario with the project's tests in **Docker**: recorded changes, a
person's new test failing, the Detective confirming the change after 5 test runs, an isolated checkpoint
restore, and an approved restore that keeps the person's test.
