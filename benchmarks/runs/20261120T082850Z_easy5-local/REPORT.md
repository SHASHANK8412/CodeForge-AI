# AIForge benchmark: easy5-local

- Task set: `v1` (5 tasks, 2 valid)
- Model override: `router default` | RAG: `on` | LLM repair: `on` | max iterations: `3`
- Sandbox: `docker` | commit `5a01bbd` | 2026-11-20T13:34:35.891440+00:00
- Coding agents on Groq: no (all agents local)

> **3 task(s) invalid** (excluded from rates). See the table below.

## Headline numbers

| Metric | Value |
| --- | --- |
| Build success (syntax OK + app boots) | 0.0% |
| Build success before any repair | 0.0% |
| Mean requirement (route) coverage | 0.0% |
| Generated-test pass rate | 0.0% (0/6 tests, 2 tasks with tests) |
| Tasks with all generated tests green | 0 |
| Repair loop: tasks improved / tasks repaired | 0 / 2 (builds fixed: 0) |
| Repair attempts kept / rolled back | 0 / 2 of 2 |
| Pipeline said PASS but grader disagreed | 0 |
| Median tokens per task | 21494.0 |
| Median wall time per task | 2649.57 s |

## Per task

| Task | Diff | Valid | Build (1st → final) | Routes | Tests | Iter | Tokens | Time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `todo-basic` | easy | yes | ❌ → ❌ | 0/6 | 0/3 | 1 | 22670 | 2717.47s |
| `notes-sqlite` | easy | yes | ❌ → ❌ | 0/4 | 0/3 | 1 | 20318 | 2581.67s |
| `url-shortener` | easy | no: pipeline timed out after 3600.0s | — | — | none | 0 | 20304 | 5991.83s |
| `calculator-api` | easy | no: 1 model call(s) failed | — | — | none | 0 | 0 | 3430.31s |
| `contact-book` | easy | no: pipeline timed out after 3600.0s | — | — | none | 0 | 21332 | 3602.72s |

## Why builds failed

- `todo-basic`: backend/main.py: NameError: name 'Depends' is not defined
- `notes-sqlite`: backend/main.py: ImportError: cannot import name 'get_db' from 'backend.database' (/work/backend/database.py)

Definitions: see `docs/EVALUATION.md`.
