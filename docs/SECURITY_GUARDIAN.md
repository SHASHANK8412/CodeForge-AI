# AIForge Security Guardian

The Security Guardian finds security problems in a generated project and backs every claim with
recorded evidence. It verifies findings by sending benign requests to a **disposable copy** in an
isolated sandbox, and it fixes them through Autopilot. A fix is applied only after the project's tests
pass and the same verification no longer reproduces the problem.

- UI: **Engineering Suite → Security Guardian**.
- API: `/api/projects/{id}/guardian`.
- Code: `backend/guardian/`.

It replaces the earlier "Security Center" endpoints, which scanned hardcoded sample files instead of the
project (see [Retired](#retired)).

## Finding states

Each state needs specific evidence. Nothing moves to `verified` because a rule matched, and nothing moves
to `fixed` because a patch was generated.

| State | Meaning |
|---|---|
| `detected` | A rule or scanner reported it, with evidence (file, line, matched code, tool). |
| `requires_review` | A pattern needs human judgement, for example a read route without authentication in an app that uses authentication elsewhere. |
| `verification_in_progress` | An approved verification is running. |
| `verified` | A safe test against the disposable copy **showed** the issue. The requests and (redacted) answers are stored. |
| `not_reproduced` | The safe test ran and did not show it. This lowers the priority but does not prove absence. |
| `verification_unavailable` | No safe test exists for the rule, or the sandbox could not run (for example, no Docker). |
| `fixed` | A remediation was applied and a **static** re-check no longer detects it. Used only for rules without a safe dynamic test. |
| `fix_verified` | A remediation was applied after the same safe test reproduced the issue on the original and **not** on the changed copy. |
| `accepted_risk` | A person accepted it with a written reason. Their name and reason are recorded, and acceptance survives later assessments. |

When a finding no longer shows up, it is marked as resolved in history. When a `fixed` or `fix_verified`
finding comes back, it returns to `detected` with a note.

## Categories and rules

| Category | Rules / tools |
|---|---|
| Injection | `PY-SQLI` (f-strings, `%`, `+` or `.format` into `execute`), `PY-CMDI`, `PY-EVAL`, `PY-DESERIALIZE` (pickle, yaml.load), `PY-PATH-TRAVERSAL`, `PY-SSRF`; `JS-SQLI`, `JS-CMDI`, `JS-EVAL`; Bandit B608/B602/B605/B307/B102/B301/B506/B310 |
| Authentication / authorization | `PY-MISSING-AUTH` (a route without an auth dependency in a project that uses them; high confidence for state-changing methods), `PY-TRUSTED-ROLE` (role or admin flags taken from the request), `PY-JWT-NO-VERIFY`, `JS-JWT-DECODE` |
| Secrets and sensitive data | `PY-HARDCODED-KEY`, `SECRET-HARDCODED` (AIForge secret scanner), `SECRET-PRIVATE-KEY`, `SECRET-ENV-FILE`, `PY-SENSITIVE-RESPONSE` (password hashes, tokens or secrets returned by an endpoint); values are always redacted |
| Web | `PY-CORS` (any origin, especially with credentials), `PY-OPEN-REDIRECT`, `PY-COOKIE-FLAGS`, `PY-ERROR-DETAIL`, `JS-XSS`, `JS-DANGEROUS-HTML`, `JS-OPEN-REDIRECT`, `JS-CORS-ANY`, `JS-NO-SECURITY-HEADERS` |
| Dependencies | `DEP-VULNERABLE` (pip-audit against PyPI/OSV advisories; npm audit against a `package-lock.json`), `DEP-UNPINNED`, `DEP-NO-LOCKFILE` |
| Cryptography | `PY-WEAK-HASH` (MD5/SHA-1 for passwords or tokens), `PY-PREDICTABLE-TOKEN` (`random` for tokens) |
| Configuration | `PY-DEBUG`, `CFG-DOCKER-ROOT`, `CFG-COMPOSE-PRIVILEGE` |

How the analysis works:
- **Python rules** use the AST. They follow request-derived values inside one function: handler arguments,
  and variables assigned from them. A route's authentication comes from its `Depends`/`Security`
  parameters, its decorator's `dependencies=`, its router's dependencies, or authentication middleware.
- **JavaScript rules** are pattern-based and reported with lower confidence.

## Pipeline

1. **Assessment.** This step is read-only and runs no project code.
   - The project's files are read, with limits: no symlinks, and dependency and cache folders are skipped.
   - The Python rules, Bandit, the secret scanner, the JS and config rules, pip-audit and npm audit run.
   - Each tool reports `ran`, `partial`, `unavailable`, `error` or `skipped`. A tool that did not run is
     listed under "not covered" and is **never** treated as a clean result.
2. **Correlation.** Results about the same thing are merged into one finding that lists every source that
   detected it. Examples:
   - Bandit B608 and `PY-SQLI` on the same line are one finding.
   - A hardcoded key reported by three tools is one finding.

   The Digital Twin graph adds context to each finding:
   - the route the line belongs to;
   - whether that route is behind authentication (`exposure: public | authenticated`);
   - which files depend on the file.
3. **Prioritisation** gives a qualitative P1–P4 with the reasons listed: severity, confidence, verified or
   not, public or authenticated, number of sources. **No CVSS score is computed or invented.** A
   dependency advisory's severity is labelled as not taken from CVSS.
4. **Verification** happens only after explicit approval of the selected findings.
   - It reuses the Chaos Engineer's sandbox:
     - a `docker network create --internal` network (no route to the host, the LAN or the internet);
     - the app in the preview's hardened container (non-root, all capabilities dropped, read-only, with
       memory, CPU and process limits);
     - requests sent from a probe container on that network.
   - Every container is labelled and removed in `finally`. The verifiers are:

   | Kind | Requests | Proof |
   |---|---|---|
   | `sql_injection` | GET with a non-matching value, a single quote, and `<marker>' OR '1'='1` | An SQL error in the answer, or the tautology returning more rows than the non-matching value |
   | `missing_auth` | The route's own method without credentials | A 2xx/3xx answer. 401/403 means authentication is enforced; 404, 422 and 5xx are not proof. |
   | `sensitive_exposure` | GET | Sensitive keys present with values (the values are not stored) |
   | `cors` | OPTIONS with `Origin: http://evil.example` (resolves nowhere) | That origin or `*` allowed, noted with or without credentials |
   | `path_traversal` | The file parameter set to `../../…/etc/passwd`, the sandbox container's own file | Its contents in the answer |
   | `open_redirect` | The target `https://example.invalid/`, without following redirects | A 3xx to it |

   No destructive payloads are sent. A state-changing request (such as `DELETE` without credentials) can
   only change the disposable copy's throwaway data. This is stated as a limitation on the result.
5. **Remediation** creates an Autopilot plan (`origin: security`) for rules where an automatic fix is safe:
   - `t1`: a model fix limited to the finding's file. The request carries the redacted evidence and the
     constraint "keep the API contract; never weaken authentication, validation or tests; no new
     dependencies".
   - `t2`: a **templated** security regression test (`tests/test_security_<finding>.py`), not written by
     the model. It fails while the issue exists, as a real run showed.

   Plans that change authentication need the Autopilot "security reviewed" acknowledgement when they are
   approved.

   These go to a person instead (the plan is refused with the reason):
   - dependency upgrades;
   - password-hash changes, which need a migration;
   - trusted-role design;
   - leaked secrets and keys, which must be rotated;
   - low-confidence missing-auth findings, where making a route public or not is a design decision.
6. **Execution** follows Autopilot's existing path. Changes are applied only if every gate passes, and are
   otherwise discarded:
   - an isolated copy is made;
   - the correctness checks run, including the project's tests **plus the regression test** in the Docker
     sandbox (no network, non-root);
   - the change is compared with the original;
   - **the security gate** (`MEASURED_GATES["security"]`) runs:
     - Verifiable rules: the same verification runs on the original and the changed copy. The decision is
       `improved` only when the original reproduces and the changed copy does not. In that case the finding
       becomes `fix_verified`. Otherwise the decision is `inconclusive` or `not_measured`.
     - Other rules: the static analysis runs again on the changed copy. The decision is `improved` if the
       rule no longer fires (the finding becomes `fixed`), `regressed` if the change introduces a new
       high or critical finding, and otherwise `inconclusive`.

### Secrets and model prompts

Autopilot never sends a secret value to the model.
- Lines that hold secret-like values are replaced by marker comments (`# AIFORGE_HIDDEN_LINE_n …`) in the
  prompt, and the original lines are put back in the model's answer.
- If the model drops or changes a marker, the answer is rejected and retried once with that feedback.
  After that the task fails, and nothing is applied.
- A file whose secret cannot be hidden line by line is not sent at all.

Evidence, audit entries, verification bodies, diffs and reports are all redacted.

## API

All routes need authentication and check project ownership the same way Autopilot does.

| Method | Path | |
|---|---|---|
| POST | `/assessments` | Start an assessment (202). 409 if a security job is already running for the project. |
| GET | `/assessments` | History of assessments and verification jobs, and `active_job` |
| GET | `/assessments/{id}` | Status, tools (versions, advisory retrieval time), coverage, audit |
| POST | `/assessments/{id}/abort` | Abort an assessment or verification |
| GET | `/findings` | Filters: `severity`, `category`, `state`, `priority` (comma lists), `file` (prefix), `route`, `q`, `include_resolved` |
| GET | `/findings/{id}` | Evidence, verification requests and answers, context |
| POST | `/verifications` | `{"finding_ids": [...], "approved": true}`. Returns 400 without approval. |
| POST | `/findings/{id}/accept-risk` | `{"note": "..."}` (required) |
| POST | `/findings/{id}/plan` | Create the Autopilot remediation plan. Approve and execute it with the Autopilot endpoints. |
| GET | `/gates/{execution_id}` | The security re-check of a remediation (original and changed verification) |
| GET | `/compare?first=&second=` | New, resolved and recurring findings between two assessments |
| GET | `/report?format=markdown\|json` | Redacted report of the latest completed assessment |

Data is stored in `backend/data/guardian/` (git-ignored). Override the location with
`AIFORGE_GUARDIAN_DIR`.

## Used by other modules

`backend.guardian.service.security_status(project_id)` returns:
- `NOT_ASSESSED` when there is no completed assessment;
- `BLOCK` when there are open critical or high findings that are detected or verified;
- `REVIEW_NEEDED` when the only open critical or high findings need a person's judgement
  (`requires_review`);
- `NO_KNOWN_BLOCKERS` otherwise. This is deliberately not called "secure".

It is used by:
- the **readiness** security check. Without an assessment the check is `NOT_AVAILABLE`; `BLOCK` fails it.
  `REVIEW_NEEDED`, or a scanner that did not run fully, gives `WARN`.
- the **copilot** executor's validation evidence;
- the **incident** remediation validation.

## Retired

These all scanned hardcoded sample files or "projects" instead of the real project, so they produced
fabricated results:
- `POST /api/security/scan` and `GET /api/security/{id}/report` (`backend/security/routes.py`);
- the unmounted `SecurityCenter` page and `services/security.js`;
- `GET /api/projects/{id}/security`, `/security-report` and `/sbom`, which audited dummy manifests;
- the `run_full_security_scan(project_id, {"main.py": "pass"})` calls in readiness, copilot, incidents
  and the architecture evaluator.

`POST /api/projects/{id}/security/fix` remains, because it works on the files sent in the request.

## Limitations

- **An empty result does not mean the project is secure.** The report says so and lists what was not
  covered.
- Data flow is followed only inside one function. There is no cross-function or cross-file taint
  tracking.
- JavaScript/TypeScript rules are patterns with no data-flow proof.
- Business logic, authorization between users (IDOR), rate limiting and CSRF are not analysed.
- Dependency lookups are **lookup-only**: `pip-audit --disable-pip --no-deps`.
  - Only exact `name==version` pins are sent. Nothing is installed or built, and index URLs, paths and
    VCS links never leave the machine.
  - Unpinned requirements are reported as NOT checked, and the tool status is `partial`.
  - npm audit needs a `package-lock.json` and runs with `--package-lock-only` on a copy of the manifests.
  - When the advisory service is unreachable, the tool is `error` or `unavailable`. It is never reported
    as clean.
- Verification needs Docker and a FastAPI app that starts in the sandbox (a health check on `/health` or
  `/docs`). Only the six kinds above have safe tests. Everything else stays static until a person reviews
  it.
- Automatic remediation is limited to single-file Python fixes. The model may still fail, and in that
  case nothing is applied.
- Verification probes the sandbox copy with its own throwaway data. Behaviour that depends on production
  data or configuration is not observed.
