"""
Side-by-side comparison of benchmark runs (models, RAG on/off, repair on/off).

    python -m benchmarks.compare benchmarks/runs/*/results.json > benchmarks/COMPARISON.md

Only compare runs that used the same ``taskset_version`` and task ids; the
script warns when they differ because the numbers are then not comparable.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

ROWS = [
    ("Build success", "build_success_rate", "pct"),
    ("Build success, no repair", "first_attempt_build_success_rate", "pct"),
    ("Route coverage", "mean_route_coverage", "pct"),
    ("Generated-test pass rate", "generated_test_pass_rate", "pct"),
    ("Tasks improved by repair", ("repair", "improved_by_repair"), "int"),
    ("Builds fixed by repair", ("repair", "build_fixed_by_repair"), "int"),
    ("Mean iterations", ("repair", "mean_iterations"), "num"),
    ("Median tokens / task", "tokens_per_task_median", "num"),
    ("Median time / task (s)", "wall_time_per_task_median_s", "num"),
    ("Valid tasks", "tasks_valid", "int"),
]


def _get(summary: Dict[str, Any], key: Any) -> Any:
    if isinstance(key, tuple):
        for k in key:
            summary = (summary or {}).get(k)
        return summary
    return summary.get(key)


def _fmt(v: Optional[float], kind: str) -> str:
    if v is None:
        return "n/a"
    if kind == "pct":
        return f"{v * 100:.1f}%"
    if kind == "int":
        return str(int(v))
    return f"{v:g}"


def compare(paths: List[str]) -> str:
    runs = []
    for p in paths:
        data = json.loads(Path(p).read_text(encoding="utf-8"))
        runs.append(data)
    if not runs:
        return "No runs given.\n"

    head = [r["config"]["label"] for r in runs]
    out = ["| Metric | " + " | ".join(head) + " |", "| --- |" + " --- |" * len(runs)]
    for title, key, kind in ROWS:
        out.append(f"| {title} | " + " | ".join(_fmt(_get(r["summary"], key), kind) for r in runs) + " |")
    out.append("")
    out.append("| Config | " + " | ".join(head) + " |")
    out.append("| --- |" + " --- |" * len(runs))
    for k in ("model", "rag", "llm_repair", "max_iterations", "sandbox", "git_commit", "taskset_version"):
        out.append(f"| {k} | " + " | ".join(str(r["config"].get(k) or "default") for r in runs) + " |")

    task_sets = {(r["config"]["taskset_version"], tuple(r["config"]["task_ids"])) for r in runs}
    if len(task_sets) > 1:
        out.insert(0, "> ⚠️ These runs used different task sets; the numbers are not directly comparable.\n")
    if any(r.get("partial") for r in runs):
        out.insert(0, "> ⚠️ At least one run is partial (interrupted).\n")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    sys.stdout.write(compare(sys.argv[1:]))
