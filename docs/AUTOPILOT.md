# AIForge Autopilot

Autopilot analyzes a generated project, reports evidence-backed findings, and, once you approve
a plan, makes changes in an isolated copy. Changes are kept only when the checks do not regress.
The UI is under **Engineering Suite → AIForge Autopilot**. The REST API is under
`/api/projects/{project_id}/evolution` (code: `backend/evolution/autopilot/`, `backend/evolution/routes.py`).

It replaces the old "software evolution" module, which reported made-up debt for a hard-coded
service. The `/api/autopilot` autonomy controller ("Autopilot Engine") is a separate feature.

## The record types

| Term | Meaning |
|---|---|
| **Detected** | An analyzer reported a finding: rule, file and line, evidence, severity, confidence. |
| **Proposed** | The finding is in a plan that is waiting for your approval. Nothing has run yet. |
| **Implemented** | A task changed files in the isolated working copy. |
| **Checked** | The checks ran before and after the change, and the result is recorded per check. |
| **Verified** | The change was applied and a fresh analysis no longer detects the finding (`fixed_verified`). |

Confidence: `confirmed` means a tool reported the finding (parser, ruff, Bandit, a test run). `likely` means a
deterministic pattern. `suspected` means a heuristic, such as the performance patterns. No profiling is done.

## Analysis

These analyzers run on the project folder. None of them runs the project's code.

| Area | Source |
|---|---|
| Syntax | Python `ast` |
| Quality | The quality gate (ruff E9/F63/F7/F82, cross-file import check, oxlint) and ruff F401/F841. Unused imports in `__init__.py` are reported as possible re-exports, not auto-fixed. |
| Tests | Test discovery. When requested, a test run in the Docker sandbox. |
| Dependencies | Imports that `requirements.txt` or `package.json` does not declare. |
| Security | Bandit and the secret scanner. Evidence is redacted. |
| Maintainability | Long functions, bare `except:`, duplicated function bodies. |
| Performance | `time.sleep` in `async def`; queries or HTTP calls inside loops (suspected). |

Every analysis lists the tools that ran and how each one ended:
- `ran`
- `partial`
- `unavailable`
- `skipped`
- `error`

A finding's id comes from its rule, its file and the text of the flagged line. The id stays the same
across runs and across edits elsewhere in the file. Findings that disappear become `resolved`. Dismissed
findings stay dismissed. A fixed finding that reappears is reopened.

### Priority

| Priority | Rule |
|---|---|
| **P1** | Critical, or high and confirmed. |
| **P2** | High, or a confirmed medium security, tests or syntax finding. |
| **P3** | Any other medium finding, or a confirmed low one. |
| **P4** | Everything else. |

A medium-or-higher finding in an entry point or route handler moves up one level. The reasons appear
on each finding.

## Plans and approval

Select open findings and choose **Propose plan**. The plan lists:
- tasks, in order: security first, then syntax, quality, dependencies, tests, maintainability, performance;
- the fix strategy and the existing AIForge component that performs it;
- the files that may change;
- the checks;
- risks, assumptions, what your approval covers, and the completion criteria.

A plan must be **approved** before it can run. It can also be **rejected** or **cancelled**.

| Strategy | Performed by |
|---|---|
| `ruff_fix` | `ruff check --fix` (safe fixes only) |
| `add_requirements` | Declares imported packages in `requirements.txt` |
| `import_repair` | The Debug Agent's repair strategies (missing, misplaced and shadowed imports) |
| `model` | The coding model through `project_editor.propose_changes`. Paths are validated. |
| `manual` | Not automated, for example committed secrets. The task is skipped and the finding stays open. |

## Execution

1. Copy the project to a temporary workspace. `.venv`, `node_modules`, caches and `.git` are left out.
2. Baseline checks: Python syntax, the quality gate, Bandit, and the tests.
3. Run each task in the copy:
   - A change to a file outside the plan stops the run with status `needs_approval`.
   - You can approve the plan again with those files (`extra_files`).
   - A model edit that adds a syntax error is reverted and retried once.
   - A file containing secret-like values is never sent to the model.
4. Run the same checks again and compare them with the baseline:
   - **Rejected:** more syntax errors, more quality-gate errors, more high-severity Bandit findings, or
     tests that passed before and fail after. For a suite that was already failing, the change is
     also rejected if the passed count drops or the failed count rises.
   - **Unverified, so not accepted:** a check that ran before the change could not run after it.
5. If the change is accepted, write the changed files to the project.
   - Before writing, the content hash of each file is compared with the copy taken at the start.
   - If a file changed in the meantime, nothing is written.
6. Analyze the project again and mark each addressed finding `fixed_verified` or `fix_failed`.

Cancelling at any point leaves the project untouched. Every run records:
- its stages;
- each task's result;
- the checks before and after, with exit codes and where they ran;
- the verdict, the unified diff and a report.

### Tests and the sandbox

Tests run only in the Docker sandbox: no network, non-root, resource limits. When Docker is unavailable,
the test check is reported as **blocked**, never as passed. The report then states that acceptance rests
on static checks only. Test counts appear only when the test runner's own summary prints them.

## API

| Method | Path |
|---|---|
| GET | `/api/evolution/projects` |
| POST | `/api/projects/{id}/evolution/analyses` (`{"run_tests": false}`) |
| GET | `/api/projects/{id}/evolution/analyses/latest`, `/analyses/{analysis_id}` |
| GET | `/api/projects/{id}/evolution/findings?priority=&severity=&category=&status=&confidence=&file=&q=&offset=&limit=` |
| GET, PATCH | `/api/projects/{id}/evolution/findings/{finding_id}` (`{"dismissed": true}`) |
| POST, GET | `/api/projects/{id}/evolution/plans` (`{"finding_ids": [...], "objective": ""}`) |
| POST | `/api/projects/{id}/evolution/plans/{plan_id}/approve` (`{"note": "", "extra_files": []}`), `/reject`, `/cancel` |
| POST | `/api/projects/{id}/evolution/plans/{plan_id}/execute` (`{"run_tests": true}`) |
| GET | `/api/projects/{id}/evolution/executions`, `/executions/{execution_id}`, `/executions/{execution_id}/report` |
| POST | `/api/projects/{id}/evolution/executions/{execution_id}/cancel` |

`{id}` is a generation id. Every request checks that the current user owns that generation, and that the
project folder is inside `generated_projects/`. Records are stored as one JSON file per project in
`backend/data/evolution/`. Writes are atomic and locked. Only one analysis or execution runs per project
at a time.

Tests: `tests/evolution/test_autopilot.py` (20 scenarios).
