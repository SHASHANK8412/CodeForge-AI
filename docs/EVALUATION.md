# Evaluating AIForge

This page explains how AIForge is measured, what each number means, and what the numbers do **not** tell you. The code is in `benchmarks/`.

## TL;DR

```bash
# one-time: build the sandbox image (Python 3.11 + common FastAPI deps, no network at run time)
docker build -t aiforge-sandbox:py311 sandbox/

# run all 20 tasks with the default model routing, executing generated code in Docker
AIFORGE_SANDBOX=docker python -m benchmarks.harness run --label baseline

# ablations
AIFORGE_SANDBOX=docker python -m benchmarks.harness run --model qwen2.5-coder:7b   --label qwen-coder-7b
AIFORGE_SANDBOX=docker python -m benchmarks.harness run --model llama3.1:8b        --label llama3.1-8b
AIFORGE_SANDBOX=docker python -m benchmarks.harness run --model deepseek-coder:6.7b --label deepseek-6.7b
AIFORGE_SANDBOX=docker python -m benchmarks.harness run --rag off        --label baseline-norag
AIFORGE_SANDBOX=docker python -m benchmarks.harness run --llm-repair off --label baseline-rules-only

# side-by-side table for the README
python -m benchmarks.compare benchmarks/runs/*/results.json > benchmarks/COMPARISON.md

# does the reviewer catch planted bugs?
python -m benchmarks.reviewer_eval --model qwen2.5-coder:7b
```

Each run writes `benchmarks/runs/<timestamp>_<label>/` containing:

| File | What it holds |
| --- | --- |
| `results.json` | config, summary, and the full per-task record (grades before and after repair, telemetry) |
| `REPORT.md` | human-readable tables, plus a "why builds failed" list |
| `traces/<task>.jsonl` | one JSON event per LLM call and per graph node (latency, tokens, fallback, errors) |
| `projects/<task>/{initial,final}/` | the exact files that were graded (git-ignored) |

## The task set

`benchmarks/tasks.py` has 20 fixed prompts: 5 easy, 11 medium and 4 hard. They cover CRUD, auth/JWT, RBAC, domain logic (ledger, bookings, library loans), and services (rate limiting, background jobs, WebSockets). Every prompt states the exact HTTP endpoints it requires, which makes requirement coverage measurable.

The task set is versioned (`TASKSET_VERSION`). Once you publish numbers, don't change a prompt. Add a v2 and re-run every configuration instead.

## What is measured, and how

The pipeline reports its own success, but the harness does **not** trust that report. `benchmarks/grader.py` re-grades the final files from scratch and records any disagreement (`pipeline_claim_mismatches`).

| Metric | Definition | How it is computed |
| --- | --- | --- |
| **Build success** | every `.py` file parses **and** a FastAPI app imports and serves `GET /openapi.json` with HTTP 200 | `ast.parse` on the host; a probe script runs in the sandbox, locates the `FastAPI()` instance, and calls it through `TestClient` |
| **Build success before repair** | the same check, run on the files as they were *before* the first debug/patch iteration | `pre_repair_files` snapshot in `ProjectState` |
| **Route coverage** | share of the task's required `METHOD /path` pairs that exist in the app's real route table | path-parameter names and trailing slashes are ignored; everything else must match |
| **Generated-test pass rate** | passed / (collected − skipped) across all tasks that produced tests | `pytest --junitxml` in the sandbox; counts are read from the XML, not scraped from output |
| **Repair improvement** | tasks where the repair loop fixed the build or increased passing tests / tasks where repair ran | initial grade vs final grade |
| **Tokens per task** | prompt + completion tokens over all LLM calls | taken from Ollama's `prompt_eval_count` / `eval_count`; if a provider doesn't report counts, a chars/4 estimate is used and the report says "(estimated)" |
| **Wall time per task** | end-to-end pipeline time | median across valid tasks |
| **Reviewer recall** | planted bugs the reviewer mentions / planted bugs | 12 snippets with one known bug each, plus 3 clean controls (`benchmarks/reviewer_eval.py`) |
| **Reviewer false-alarm rate** | clean controls where the reviewer raised a critical or major issue | same |

### Validity rules

- **LLM caching is off** (`AIFORGE_DISABLE_LLM_CACHE=1`), and the per-node caches are cleared between tasks, so every task calls the model for real.
- **Fallback = invalid.** When an LLM call fails, `backend/services/llm.py` returns canned placeholder code, and that code can pass the build check. Any task with a fallback is marked `valid: false`, excluded from every rate, and counted in `tasks_invalid`. A run where Ollama was down therefore shows "0 valid tasks", not a fake success rate.
- **Fallback output is never cached**, so one outage can't poison later runs.
- **Isolation.** Each run gets its own output directory, and the grader always works on a throwaway copy of the project.

### What the numbers do not tell you

- **Frontend code is not built.** The React output is never compiled, because that needs `npm install`, which needs network access. Build success is a backend measure.
- **Route coverage checks existence, not behavior.** An endpoint that exists but returns the wrong thing still counts. Generated tests partly cover behavior, but the model wrote those tests too, so a weak suite can pass a weak app.
- **Reviewer detection uses keyword matching.** It is deterministic and cheap, but it can miss a correct finding phrased differently, or credit a vague one. Every review is saved in `reviewer_eval.json`, so misses can be audited by hand.
- **Small n.** With 20 tasks, one task is 5 percentage points. Do at least 3 runs per configuration (`--label x-r1`, `x-r2`, …) and report the spread before claiming one setup beats another.
- **Sandbox dependencies define "builds."** A project that imports a library missing from `sandbox/requirements.txt` fails with `ImportError`. That's intended (the generator should use common libraries), but keep it in mind when reading results.

## The execution sandbox

Set `AIFORGE_SANDBOX=docker` to run all generated code (the pipeline's own run/test step as well as the grader) in `backend/execution/docker_sandbox.py`:

| Control | Threat it addresses |
| --- | --- |
| `--network none` | exfiltration, downloading payloads, calling external APIs |
| `--read-only` + `--tmpfs /tmp` | writes outside the project copy |
| `--memory 512m --memory-swap 512m`, `--cpus 1` | memory bombs, CPU starvation |
| `--pids-limit 256` | fork bombs |
| `--user 10001`, `--cap-drop ALL`, `no-new-privileges` | root inside the container, kernel capabilities, setuid escalation |
| host-side timeout → `docker kill` | infinite loops and servers that never exit |
| throwaway copy of the project | a run can't modify the generator's output |
| explicit env only | host secrets never reach the container |

If `AIFORGE_SANDBOX=docker` is set but the image is missing, the runner **refuses to run** instead of quietly executing untrusted code on the host. Without the variable, code runs as a local subprocess with secret-looking environment variables stripped. That is fine for trusted fixtures, but it is not isolation, and `results.json` records which backend was used.

## The generate → run → fix loop

```
assembly ─► execution_validation ─► testing ─┬─► packaging   (build + tests green)
                 ▲                            ├─► END          (max_iterations reached)
                 └──── patch ◄──── debug ◄────┘
```

1. **testing** generates a pytest suite *once*, writes it into the project, and re-runs the build. The suite is never regenerated during repair, so the debugger has to make the same tests pass.
2. **execution_validation** runs `compileall` (every module must parse, not just the imported ones) and then `pytest`, in the sandbox.
3. **debug** first applies deterministic rules. If they produce no concrete patch, it sends the real failure output plus the suspect source files to the LLM and asks for complete corrected files. Guard rails:
   - only existing, non-test `.py` files can be changed (the model can't "fix" a failure by weakening the tests);
   - every patched file must parse;
   - a patch identical to the current file is dropped.
4. **patch** writes the change to disk with path-traversal checks, and the loop repeats until green or `max_iterations` (default 3).

`--llm-repair off` disables step 3's LLM path, so the benchmark can show how much the LLM repair adds over the rules alone.

## Observability

Every LLM call and every graph node emits a structured event through `backend/observability/tracing.py`:

```json
{"kind": "llm_call", "agent": "backend", "model": "qwen2.5-coder:latest", "latency_ms": 41873.2,
 "prompt_tokens": 1312, "completion_tokens": 1650, "tokens_estimated": false,
 "cache_hit": false, "fallback": false, "error": null, "prompt": "…", "output": "…"}
{"kind": "node", "node": "execution_validation", "status": "ok", "latency_ms": 2210.4, "state_status": "FAIL"}
```

- Set `AIFORGE_TRACE_FILE=logs/trace.jsonl` to log events outside the benchmark.
- `AIFORGE_TRACE_MAX_CHARS` (default 2000; 0 drops text) caps how much prompt and output text is stored.
- `global_trace.summary()` aggregates tokens, latency, fallbacks and per-agent cost. That's what the harness reports.

## Bugs the harness surfaced while it was being built

Building the harness and running the pipeline end to end against a scripted LLM (`tests/test_eval_harness.py::test_pipeline_end_to_end_repairs_planted_bug`) exposed these bugs, now fixed:

1. **Markdown written as source.** Agents return fenced blocks annotated with `# filepath:`, but assembly wrote the whole markdown answer into `backend/main.py`. Every real generation was a `SyntaxError`. `split_llm_files` now extracts each block to its own path.
2. **Generated tests never ran.** The suite was generated after the execution step and never written to disk. The only test file was a placeholder, so pytest exited 5 ("no tests collected").
3. **The planner received an empty prompt** from the CLI/benchmark entry point (`user_request` was set, but the planner read `user_prompt`). Every project was planned without seeing the request.
4. **The debugger couldn't repair real bugs.** Its only rewrite replaced the string `'WRONG'` with `'OK'`.
5. **Reviewer scores were always 100.** The score counted `[Critical]` tags, but the reviewer is prompted to return JSON with a `severity` field.
6. **Canned fallback output was cached**, and token counts were always estimated as chars/4.
7. **Runs shared `./generated_projects/<name>`**, so files left by one run changed the next run's result.
8. **Old benchmark numbers came from mocks.** The previous `benchmarks/results.json` ("100% E2E", 0.0 s per task) was written by a unit test with a mocked pipeline. It has been removed, and the legacy runner now writes to `benchmarks/legacy_results/`.
