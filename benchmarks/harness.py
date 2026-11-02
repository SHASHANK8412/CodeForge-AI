"""
AIForge evaluation harness.

Runs the fixed task set (``benchmarks/tasks.py``) through the real pipeline,
grades every generated project independently (``benchmarks/grader.py``) and
writes ``results.json`` + ``REPORT.md`` for the run.

    # one configuration, all 20 tasks, Docker-isolated execution
    AIFORGE_SANDBOX=docker python -m benchmarks.harness run --label qwen7b

    # ablations
    python -m benchmarks.harness run --model llama3.1:8b --label llama8b
    python -m benchmarks.harness run --rag off --label qwen7b-norag
    python -m benchmarks.harness run --llm-repair off --label qwen7b-rules-only

    # grade a project you already have
    python -m benchmarks.harness grade path/to/project --task todo-basic

    # compare runs side by side
    python -m benchmarks.compare benchmarks/runs/*/results.json

Validity rules (a run that breaks one is reported, not hidden):
* LLM caches are disabled, so every task really calls the model.
* A task with any LLM *fallback* (model unreachable -> canned output) is marked
  ``valid=False`` and excluded from headline rates; the summary counts them.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import platform
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from benchmarks.grader import grade_project, is_test_file, materialize_files  # noqa: E402
from benchmarks.tasks import TASKSET_VERSION, BenchmarkTask, get_tasks  # noqa: E402

DEFAULT_RUNS_DIR = REPO_ROOT / "benchmarks" / "runs"
PipelineFn = Callable[..., Any]


# --------------------------------------------------------------------------- #
# Environment / configuration
# --------------------------------------------------------------------------- #

@contextmanager
def configured_env(model: Optional[str], rag: str, llm_repair: str, trace_file: Optional[Path]) -> Iterator[None]:
    """Applies one benchmark configuration through env vars, then restores them."""
    updates = {
        "AIFORGE_DISABLE_LLM_CACHE": "1",
        "AIFORGE_RAG": rag,
        "AIFORGE_LLM_REPAIR": llm_repair,
        "AIFORGE_TRACE_FILE": str(trace_file) if trace_file else None,
    }
    if model:
        updates.update({"AIFORGE_CODING_MODEL": model, "AIFORGE_GENERAL_MODEL": model,
                        "AIFORGE_DEBUG_MODEL": model, "OLLAMA_MODEL": model})
    saved = {k: os.environ.get(k) for k in updates}
    try:
        for k, v in updates.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def _reset_pipeline_caches() -> None:
    """Clears in-process caches so tasks cannot reuse each other's outputs."""
    for clear in (
        lambda: __import__("backend.services.cache_service", fromlist=["x"]).global_cache_service.clear(),
        lambda: __import__("backend.utils.cache", fromlist=["x"]).clear_cache(),
    ):
        try:
            clear()
        except Exception:
            pass


def _git_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT,
                              capture_output=True, text=True, timeout=10).stdout.strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


# --------------------------------------------------------------------------- #
# Per-task execution
# --------------------------------------------------------------------------- #

def _files_with_tests(final_state: Dict[str, Any], key: str = "files") -> Dict[str, str]:
    files = dict(final_state.get(key) or {})
    return {k: v for k, v in files.items() if isinstance(v, str)}


def _review_summary(final_state: Dict[str, Any]) -> Dict[str, Any]:
    review = final_state.get("review") or {}
    counts = review.get("severity_counts") or {}
    return {
        "score": review.get("score"),
        "issues": len(review.get("issues") or []),
        "critical": counts.get("critical", 0),
        "major": counts.get("major", 0),
        "minor": counts.get("minor", 0),
    }


async def run_task(task: BenchmarkTask, run_dir: Path, pipeline: PipelineFn, max_iterations: int,
                   task_timeout: float) -> Dict[str, Any]:
    from backend.observability.tracing import global_trace

    _reset_pipeline_caches()
    global_trace.reset()
    projects_dir = run_dir / "projects"
    started = time.perf_counter()
    record: Dict[str, Any] = {
        "task_id": task.id, "title": task.title, "category": task.category, "difficulty": task.difficulty,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }

    error: Optional[str] = None
    final_state: Dict[str, Any] = {}
    pipeline_res: Dict[str, Any] = {}
    try:
        pipeline_res = await asyncio.wait_for(
            pipeline(prompt=task.prompt, project_name=task.id, max_iterations=max_iterations,
                     export_zip=False, output_dir=str(projects_dir / "_pipeline")),
            timeout=task_timeout,
        )
        final_state = pipeline_res.get("final_state") or {}
    except asyncio.TimeoutError:
        error = f"pipeline timed out after {task_timeout}s"
    except Exception as exc:  # recorded, never raised: one task must not kill the run
        error = f"{type(exc).__name__}: {exc}"

    record["wall_time_s"] = round(time.perf_counter() - started, 2)
    trace = global_trace.summary()
    record["telemetry"] = trace
    record["pipeline"] = {
        "error": error,
        "status": pipeline_res.get("status") or final_state.get("status"),
        "errors": [str(e)[:500] for e in (final_state.get("errors") or [])][:3],
        "self_reported_success": bool(pipeline_res.get("success")),
        "iterations_used": int(final_state.get("iteration") or 0),
        "repair_attempts": len(final_state.get("fixes") or []),
        "verification_status": (pipeline_res.get("verification") or {}).get("status"),
        "repair_history": [
            {k: h.get(k) for k in ("attempt", "source", "verdict", "rolled_back", "newly_passing", "newly_failing")}
            for h in (final_state.get("repair_history") or [])
        ],
        "review": _review_summary(final_state),
    }
    record["valid"] = error is None and trace["llm_fallbacks"] == 0 and trace["llm_calls"] > 0
    if not record["valid"]:
        reasons = []
        if error:
            reasons.append(error)
        if trace["llm_fallbacks"]:
            reasons.append(f"{trace['llm_fallbacks']} LLM call(s) fell back to canned output")
        if trace["llm_calls"] == 0:
            reasons.append("no LLM calls recorded")
        if record["pipeline"]["errors"] and record["pipeline"]["status"] == "SECURITY_ERROR":
            reasons.append(f"pipeline crashed: {record['pipeline']['errors'][0][:200]}")
        record["invalid_reason"] = "; ".join(reasons)

    final_files = _files_with_tests(final_state)
    initial_files = _files_with_tests(final_state, "pre_repair_files") or final_files
    if final_files:
        final_dir = materialize_files(final_files, str(projects_dir / task.id / "final"))
        record["final"] = grade_project(str(final_dir), task.expected_routes).to_dict()
        if initial_files != final_files:
            init_dir = materialize_files(initial_files, str(projects_dir / task.id / "initial"))
            record["initial"] = grade_project(str(init_dir), task.expected_routes).to_dict()
        else:
            record["initial"] = record["final"]
    else:
        record["final"] = record["initial"] = None
    record["has_generated_tests"] = any(is_test_file(k, v) for k, v in final_files.items())
    return record


# --------------------------------------------------------------------------- #
# Aggregation
# --------------------------------------------------------------------------- #

def _rate(num: int, den: int) -> Optional[float]:
    return round(num / den, 4) if den else None


def _mean(values: List[float]) -> Optional[float]:
    return round(sum(values) / len(values), 4) if values else None


def _median(values: List[float]) -> Optional[float]:
    if not values:
        return None
    v = sorted(values)
    mid = len(v) // 2
    return round(v[mid] if len(v) % 2 else (v[mid - 1] + v[mid]) / 2, 2)


def summarize(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    valid = [r for r in records if r.get("valid")]
    graded = [r for r in valid if r.get("final")]
    n = len(valid)

    def g(r: Dict[str, Any], stage: str, key: str) -> Any:
        return (r.get(stage) or {}).get(key)

    builds = sum(1 for r in graded if g(r, "final", "build_success"))
    first_try = sum(1 for r in graded if g(r, "initial", "build_success"))
    syntax = sum(1 for r in graded if g(r, "final", "syntax_ok"))
    with_tests = [r for r in graded if (g(r, "final", "tests_collected") or 0) > 0 or (g(r, "final", "test_files") or 0) > 0]
    passed = sum(g(r, "final", "tests_passed") or 0 for r in with_tests)
    ran = sum((g(r, "final", "tests_collected") or 0) - (g(r, "final", "tests_skipped") or 0) for r in with_tests)
    all_green = sum(1 for r in with_tests if g(r, "final", "test_pass_rate") == 1.0)
    coverage = [g(r, "final", "route_coverage") for r in graded if g(r, "final", "route_coverage") is not None]
    repaired = [r for r in graded if r["pipeline"]["repair_attempts"] > 0]
    fixed_by_repair = sum(1 for r in repaired if g(r, "final", "build_success") and not g(r, "initial", "build_success"))
    improved_by_repair = sum(
        1 for r in repaired
        if (g(r, "final", "build_success") and not g(r, "initial", "build_success"))
        or (g(r, "final", "tests_passed") or 0) > (g(r, "initial", "tests_passed") or 0)
    )
    attempts = [h for r in valid for h in (r["pipeline"].get("repair_history") or [])]
    self_claims = sum(1 for r in graded if r["pipeline"]["self_reported_success"])
    claim_mismatch = sum(1 for r in graded
                         if r["pipeline"]["self_reported_success"] and not g(r, "final", "build_success"))

    tokens = [r["telemetry"]["prompt_tokens"] + r["telemetry"]["completion_tokens"] for r in valid]
    times = [r["wall_time_s"] for r in valid]

    by_difficulty: Dict[str, Dict[str, Any]] = {}
    for diff in ("easy", "medium", "hard"):
        sub = [r for r in graded if r["difficulty"] == diff]
        if sub:
            by_difficulty[diff] = {
                "tasks": len(sub),
                "build_success_rate": _rate(sum(1 for r in sub if g(r, "final", "build_success")), len(sub)),
                "mean_route_coverage": _mean([g(r, "final", "route_coverage") or 0.0 for r in sub]),
            }

    return {
        "tasks_total": len(records),
        "tasks_valid": n,
        "tasks_invalid": len(records) - n,
        "build_success_rate": _rate(builds, n),
        "first_attempt_build_success_rate": _rate(first_try, n),
        "syntax_ok_rate": _rate(syntax, n),
        "mean_route_coverage": _mean(coverage),
        "tasks_with_generated_tests": len(with_tests),
        "generated_test_pass_rate": _rate(passed, ran),
        "tasks_all_tests_green": all_green,
        "tests_passed": passed,
        "tests_ran": ran,
        "repair": {
            "tasks_with_repair_attempts": len(repaired),
            "build_fixed_by_repair": fixed_by_repair,
            "repair_fix_rate": _rate(fixed_by_repair, len(repaired)),
            "improved_by_repair": improved_by_repair,
            "repair_improvement_rate": _rate(improved_by_repair, len(repaired)),
            "mean_iterations": _mean([float(r["pipeline"]["iterations_used"]) for r in valid]),
            "attempts": len(attempts),
            "attempts_kept": sum(1 for h in attempts if h.get("verdict") in ("fixed", "improved")),
            "attempts_rolled_back": sum(1 for h in attempts if h.get("rolled_back")),
            "attempt_verdicts": {v: sum(1 for h in attempts if h.get("verdict") == v)
                                 for v in sorted({h.get("verdict") for h in attempts if h.get("verdict")})},
        },
        "pipeline_self_reported_success": self_claims,
        "pipeline_claim_mismatches": claim_mismatch,
        "tokens_per_task_median": _median([float(t) for t in tokens]),
        "tokens_total": sum(tokens),
        "tokens_estimated": any(r["telemetry"].get("tokens_estimated") for r in valid),
        "wall_time_per_task_median_s": _median(times),
        "wall_time_total_s": round(sum(r["wall_time_s"] for r in records), 1),
        "by_difficulty": by_difficulty,
    }


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #

def _pct(v: Optional[float]) -> str:
    return "n/a" if v is None else f"{v * 100:.1f}%"


def render_report(results: Dict[str, Any]) -> str:
    cfg, s = results["config"], results["summary"]
    lines = [
        f"# AIForge benchmark: {cfg['label']}",
        "",
        f"- Task set: `{cfg['taskset_version']}` ({s['tasks_total']} tasks, {s['tasks_valid']} valid)",
        f"- Model override: `{cfg['model'] or 'router default'}` | RAG: `{cfg['rag']}` | "
        f"LLM repair: `{cfg['llm_repair']}` | max iterations: `{cfg['max_iterations']}`",
        f"- Sandbox: `{cfg['sandbox']}` | commit `{cfg['git_commit']}` | {results['finished_at']}",
        "",
    ]
    if s["tasks_invalid"]:
        lines += [f"> **{s['tasks_invalid']} task(s) invalid** (excluded from rates). See the table below.", ""]
    lines += [
        "## Headline numbers",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| Build success (syntax OK + app boots) | {_pct(s['build_success_rate'])} |",
        f"| Build success before any repair | {_pct(s['first_attempt_build_success_rate'])} |",
        f"| Mean requirement (route) coverage | {_pct(s['mean_route_coverage'])} |",
        f"| Generated-test pass rate | {_pct(s['generated_test_pass_rate'])} ({s['tests_passed']}/{s['tests_ran']} tests, "
        f"{s['tasks_with_generated_tests']} tasks with tests) |",
        f"| Tasks with all generated tests green | {s['tasks_all_tests_green']} |",
        f"| Repair loop: tasks improved / tasks repaired | {s['repair']['improved_by_repair']} / "
        f"{s['repair']['tasks_with_repair_attempts']} (builds fixed: {s['repair']['build_fixed_by_repair']}) |",
        f"| Repair attempts kept / rolled back | {s['repair'].get('attempts_kept', 0)} / "
        f"{s['repair'].get('attempts_rolled_back', 0)} of {s['repair'].get('attempts', 0)} |",
        f"| Pipeline said PASS but grader disagreed | {s['pipeline_claim_mismatches']} |",
        f"| Median tokens per task{' (estimated)' if s['tokens_estimated'] else ''} | {s['tokens_per_task_median']} |",
        f"| Median wall time per task | {s['wall_time_per_task_median_s']} s |",
        "",
        "## Per task",
        "",
        "| Task | Diff | Valid | Build (1st → final) | Routes | Tests | Iter | Tokens | Time |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in results["tasks"]:
        fin, ini = r.get("final") or {}, r.get("initial") or {}
        tok = r["telemetry"]["prompt_tokens"] + r["telemetry"]["completion_tokens"]
        tests = (f"{fin.get('tests_passed', 0)}/{fin.get('tests_collected', 0) - fin.get('tests_skipped', 0)}"
                 if fin.get("test_files") else "none")
        build = f"{'✅' if ini.get('build_success') else '❌'} → {'✅' if fin.get('build_success') else '❌'}" if fin else "—"
        routes = (f"{fin.get('routes_matched', 0)}/{fin.get('routes_expected', 0)}" if fin else "—")
        valid = "yes" if r.get("valid") else f"no: {r.get('invalid_reason', '')[:60]}"
        lines.append(f"| `{r['task_id']}` | {r['difficulty']} | {valid} | {build} | {routes} | {tests} | "
                     f"{r['pipeline']['iterations_used']} | {tok} | {r['wall_time_s']}s |")

    failures = [r for r in results["tasks"] if r.get("final") and not r["final"].get("build_success")]
    if failures:
        lines += ["", "## Why builds failed", ""]
        for r in failures:
            fin = r["final"]
            why = "; ".join(fin.get("syntax_errors", [])[:3]) or (fin.get("boot_error") or "unknown").splitlines()[0]
            lines.append(f"- `{r['task_id']}`: {why[:200]}")
    lines += ["", "Definitions: see `docs/EVALUATION.md`.", ""]
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Entry points
# --------------------------------------------------------------------------- #

async def run_benchmark(task_ids: Optional[List[str]] = None, model: Optional[str] = None, rag: str = "on",
                        llm_repair: str = "on", max_iterations: int = 3, label: Optional[str] = None,
                        runs_dir: Path = DEFAULT_RUNS_DIR, task_timeout: float = 1800.0,
                        pipeline: Optional[PipelineFn] = None) -> Dict[str, Any]:
    if pipeline is None:
        from run_aiforge import run_aiforge_pipeline as pipeline  # heavy import, only when needed
    from backend.execution.docker_sandbox import sandbox_backend

    tasks = get_tasks(task_ids)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    label = label or f"{(model or 'default').replace(':', '-').replace('/', '-')}-rag{rag}"
    run_dir = Path(runs_dir) / f"{stamp}_{label}"
    (run_dir / "traces").mkdir(parents=True, exist_ok=True)

    config = {
        "label": label, "model": model, "rag": rag, "llm_repair": llm_repair, "max_iterations": max_iterations,
        "taskset_version": TASKSET_VERSION, "task_ids": [t.id for t in tasks], "sandbox": sandbox_backend(),
        "git_commit": _git_commit(), "python": platform.python_version(), "platform": platform.platform(),
    }
    print(f"AIForge benchmark '{label}': {len(tasks)} task(s) -> {run_dir}")

    records: List[Dict[str, Any]] = []
    for i, task in enumerate(tasks, 1):
        with configured_env(model, rag, llm_repair, run_dir / "traces" / f"{task.id}.jsonl"):
            rec = await run_task(task, run_dir, pipeline, max_iterations, task_timeout)
        records.append(rec)
        fin = rec.get("final") or {}
        print(f"[{i}/{len(tasks)}] {task.id:<22} valid={rec['valid']!s:<5} build={fin.get('build_success')!s:<5} "
              f"routes={fin.get('routes_matched')}/{fin.get('routes_expected')} "
              f"tests={fin.get('tests_passed')}/{fin.get('tests_collected')} t={rec['wall_time_s']}s")
        # Write progress after every task so a crash loses nothing.
        _write(run_dir, config, records, partial=True)

    return _write(run_dir, config, records, partial=False)


def _write(run_dir: Path, config: Dict[str, Any], records: List[Dict[str, Any]], partial: bool) -> Dict[str, Any]:
    results = {
        "config": config, "partial": partial, "finished_at": datetime.now(timezone.utc).isoformat(),
        "summary": summarize(records), "tasks": records,
    }
    (run_dir / "results.json").write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    (run_dir / "REPORT.md").write_text(render_report(results), encoding="utf-8")
    return results


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m benchmarks.harness", description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    run_p = sub.add_parser("run", help="run the benchmark")
    run_p.add_argument("--tasks", help="comma-separated task ids (default: all)")
    run_p.add_argument("--model", help="Ollama model for every agent, e.g. qwen2.5-coder:7b")
    run_p.add_argument("--rag", choices=["on", "off"], default="on")
    run_p.add_argument("--llm-repair", choices=["on", "off"], default="on")
    run_p.add_argument("--max-iterations", type=int, default=3)
    run_p.add_argument("--label")
    run_p.add_argument("--runs-dir", default=str(DEFAULT_RUNS_DIR))
    run_p.add_argument("--task-timeout", type=float, default=1800.0)

    grade_p = sub.add_parser("grade", help="grade an existing project directory")
    grade_p.add_argument("project_dir")
    grade_p.add_argument("--task", help="task id whose expected routes to check")

    rep_p = sub.add_parser("report", help="re-render REPORT.md from results.json")
    rep_p.add_argument("results_json")

    sub.add_parser("list", help="list benchmark tasks")

    args = parser.parse_args(argv)
    if args.cmd == "run":
        res = asyncio.run(run_benchmark(
            task_ids=args.tasks.split(",") if args.tasks else None, model=args.model, rag=args.rag,
            llm_repair=args.llm_repair, max_iterations=args.max_iterations, label=args.label,
            runs_dir=Path(args.runs_dir), task_timeout=args.task_timeout,
        ))
        s = res["summary"]
        print(f"\nbuild success {_pct(s['build_success_rate'])} | route coverage {_pct(s['mean_route_coverage'])} | "
              f"test pass {_pct(s['generated_test_pass_rate'])} | invalid tasks {s['tasks_invalid']}")
        return 0
    if args.cmd == "grade":
        routes = get_tasks([args.task])[0].expected_routes if args.task else None
        print(json.dumps(grade_project(args.project_dir, routes).to_dict(), indent=2))
        return 0
    if args.cmd == "report":
        path = Path(args.results_json)
        results = json.loads(path.read_text(encoding="utf-8"))
        results["summary"] = summarize(results["tasks"])  # pick up metric changes
        (path.parent / "REPORT.md").write_text(render_report(results), encoding="utf-8")
        print(path.parent / "REPORT.md")
        return 0
    if args.cmd == "list":
        for t in get_tasks():
            print(f"{t.id:<22} {t.difficulty:<7} {t.category:<8} {len(t.expected_routes)} routes  {t.title}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
