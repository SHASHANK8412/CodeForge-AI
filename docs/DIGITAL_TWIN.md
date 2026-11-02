# AIForge Digital Twin

The Digital Twin builds a dependency graph of a generated project. Before any file is changed, it predicts
the impact of a proposed change:
- which files, APIs, models and components are affected;
- which interfaces have callers;
- the risk, and which tests to run.

The prediction can become an Autopilot plan, which goes through the usual approval, isolated execution and
checks. After the run, the prediction is compared with what the change actually did.

- UI: **Engineering Suite → Digital Twin**.
- API: `/api/projects/{id}/twin`.
- Code: `backend/twin/`.

It is built on static analysis and explicit rules. It does not claim to predict runtime failures, and an
empty impact does not mean a change is safe.

## Dependency graph (`backend/twin/graph.py`)

Graph extraction reads the source only and never runs it. It uses Autopilot's bounded scan: dependency,
build and VCS folders, secrets, local data and symlinks are skipped, and there are limits on file size,
file count and time.

| Node | Source |
|---|---|
| `file`, `test`, `config` | Every Python/JS/TS file. Test files by name pattern. Manifests and config files. |
| `function`, `class` | Top-level Python definitions |
| `model` | Classes with `__tablename__`, or based on `Model`/`Document` (`orm`) or `BaseModel`/`SQLModel` (`schema`), including subclasses of those in the same file |
| `route` | FastAPI decorators (with the `APIRouter(prefix=…)` of the same file), Express `app/router.METHOD`, Next.js `app/api/**/route.js` handlers |
| `component` | Capitalized functions/arrow functions in JSX/TSX files |
| `package` | Third-party imports |

| Edge | Meaning | Certainty |
|---|---|---|
| `imports` | A module import that resolves to a project file | established. Inferred when it resolves only through another source root or a bundler alias (`@/`). |
| `uses` | An imported symbol: `from m import X`, or `import m` followed by `m.X` | established |
| `defines` | A file defines a symbol or route | established |
| `handled_by` | A route maps to its handler function | established |
| `renders` | A JSX element of an imported component | established |
| `calls_api` | A `fetch`/`axios`/`api.*` URL matched to a route by path pattern and HTTP method | **inferred** |
| `tests` | A test imports the module (established), or is named after it (inferred) | as stated |
| `depends_on` | Third-party package | established |

Every edge carries its evidence (`file:line: code`, with secrets redacted). The graph also records:
- unresolved imports: a module or name that the code imports but no file defines;
- import cycles, found with Tarjan's algorithm;
- what the scan could not cover: files that don't parse, oversized files, dynamic imports, the time limit,
  and router prefixes set in another file.

## Impact analysis (`impact.py`, `index.py`)

The files a change targets (its *seeds*) come from up to three sources. Each seed is labelled with its source.

1. **Files you choose** (established).
2. **The planner model** (optional, "use planner model"). It proposes `modify`/`create` paths. Paths
   that don't exist, or that point outside the project, are dropped and reported.
3. **Keyword matching** of the request against file names, symbols, routes and models (inferred). This is
   used only when the first two give nothing.

From the seeds, fixed rules over the graph produce:
- **direct dependents** (depth 1);
- **transitive dependents** (up to depth 4, with the chain). A chain is inferred if any link in it is.
- **APIs**: routes defined in changed or affected files, with their frontend callers.
- **models**, **components**, and **configuration** relevant to the change kind.
- **interfaces at risk**: symbols in changed files that other files use.

Change kinds come from the request text and from what the seeds contain:
- `auth`
- `database`
- `public_api`
- `frontend_ui`
- `dependency`
- `configuration`
- `tests`

## Risk (`risk.py`)

Risk is a sum of points, and every factor is listed with its reason.

| Factor | Points |
|---|---|
| Affected files: 2+ / 6+ / 15+ | +1 / +2 / +3 |
| Dependency depth: 2 / 3+ | +1 / +2 |
| Critical modules: symbols used by 5+ files; modified entry points | up to +3 |
| Public API: changed files define routes | +2 |
| Database schema: database change kind, or ORM models defined in changed files | +2 |
| Authentication/authorization | +3, and a security review is required |
| Test coverage: share of changed files with no linked test | +1 or +2 |
| Previous validation failures: open Autopilot syntax/test/blocking findings in the area | up to +2 |
| Uncertainty: mostly inferred links; targets inferred rather than chosen | up to +2 |

The total maps to a category: 0–3 is **low**, 4–7 **medium**, 8–11 **high**, 12 and above **critical**.
Authentication changes are at least **high**. This is a ranking for review effort, not a measured failure
probability.

## Test selection

Tests are selected in this order, and each one lists why:

1. Tests that import a changed file, or are named after it.
2. Tests for the dependent files.
3. Integration tests (`TestClient`, `supertest`) that mention an affected route.
4. The whole suite, when 10 or more files are affected or the risk is high or critical.

Changed files with no linked test are listed. When Docker is unavailable, the report says the tests
cannot run there.

## What-if simulation (read-only)

`POST /twin/simulations` takes:
- a request;
- optional target files;
- up to 3 alternatives;
- `use_model`.

It runs as a background job. If the project changed since the last analysis, the graph is rebuilt first.
The project's file fingerprint is compared before and after, and the report records `files_written`, which
is always 0 unless another process edited the project. Alternatives are simulated separately and compared
side by side: scope, affected files, APIs, tests, uncertainties and risk.

## Approval, execution, prediction versus actual

`POST /twin/reports/{id}/plan` creates an Autopilot plan with `origin: "digital_twin"`:
- one coding-model task scoped to the predicted files (plus folders for new files);
- the dependent files given to the model as read-only context.

Approving and executing use the Autopilot API and its safeguards:
- an isolated copy;
- baseline and after checks;
- rejection of regressions;
- a stop for approval when a change touches a file outside the scope.

Approving an authentication change also requires `security_reviewed: true`.

When the execution ends, `GET /twin/reports/{id}/outcome` compares the prediction with the actual run. It reports:

| Item | Meaning |
|---|---|
| Predicted files vs. actually modified files | including out-of-scope attempts |
| Unexpected modifications | changed files that were not predicted |
| Predicted but not changed | predicted files the change left alone |
| Validation failures | each marked new or already failing before the change |
| Precision | changed files that were predicted ÷ all changed files |
| Recall | predicted files that were changed ÷ all predicted files |

`GET /twin/accuracy` summarizes these across a project's reports. The summary is descriptive only:
nothing is trained or tuned from it.

## API

| Method | Path |
|---|---|
| POST | `/api/projects/{id}/twin/analyses` |
| GET | `/api/projects/{id}/twin/analyses/latest` (status, stats, `stale`) |
| GET | `/api/projects/{id}/twin/graph?type=&language=&q=&offset=&limit=` |
| GET | `/api/projects/{id}/twin/dependencies?node=&depth=&direction=both\|in\|out&limit=` |
| POST | `/api/projects/{id}/twin/simulations` `{"request", "target_files", "alternatives", "use_model"}` |
| GET | `/api/projects/{id}/twin/reports`, `/reports/{report_id}`, `/reports/{report_id}/tests?option=` |
| POST | `/api/projects/{id}/twin/reports/{report_id}/plan` `{"option": 0}` |
| GET | `/api/projects/{id}/twin/reports/{report_id}/outcome`, `/api/projects/{id}/twin/accuracy` |

Ownership and project resolution are the same as for Autopilot: `{id}` is a generation the user owns, and
its folder must be inside `generated_projects/`. Target paths that are absolute or climb out of the project
are rejected with HTTP 400.

Data is stored as one JSON file per project in `backend/data/twin/` (directory set by `AIFORGE_TWIN_DIR`).
The last 3 graphs and 100 reports are kept. A graph stores structure and one-line evidence, never whole
source files. Jobs interrupted by a server restart are closed as failed.

## Known limitations

- Python and JS/TS only. No type inference, so `obj.method()` calls through variables are not linked.
- Routers mounted with a prefix in another file (`include_router`, `app.use`) are matched to frontend calls
  by URL suffix, so those links are inferred.
- Dynamic imports, reflection, dependency injection containers and configuration-driven wiring are not
  followed. They are listed when detected.
- Keyword targeting is coarse. Choosing the target files, or enabling the planner model, gives a sharper scope.
- The prediction-versus-actual comparison covers modified files. Whether a predicted dependent actually
  broke is shown only by the checks.

Tests: `tests/twin/test_digital_twin.py` (21 tests covering the 20 scenarios).
