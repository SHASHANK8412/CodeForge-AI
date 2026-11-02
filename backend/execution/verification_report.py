"""
Evidence-backed verification report for a generated project.

The report is computed only from what was executed: the last command, its exit
code, per-test outcomes from pytest's ``-rA`` summary, the sandbox it ran in,
and the judged history of repair attempts. Nothing an agent *said* about the
code affects the status.

Statuses (see ``repair_policy.classify_verification``):

* ``VERIFIED``   tests were collected and every one passed
* ``BUILD_ONLY`` the build passed but no tests ran, so behavior is unverified
* ``FAILED``     build or tests failed
* ``NOT_RUN``    nothing was executed
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from backend.execution.repair_policy import classify_verification, snapshot

_BADGE = {"VERIFIED": "✅ VERIFIED", "BUILD_ONLY": "⚠️ BUILD ONLY (no tests ran)",
          "FAILED": "❌ FAILED", "NOT_RUN": "⛔ NOT RUN"}


def build_verification_report(state: Dict[str, Any]) -> Dict[str, Any]:
    exec_res = dict(state.get("execution_results") or {})
    snap = snapshot(exec_res) if exec_res else {"outcomes": {}, "failing": [], "passing": []}
    outcomes = snap["outcomes"]
    cls = classify_verification(exec_res, exec_res.get("sandbox"))
    history: List[Dict[str, Any]] = [
        {k: h.get(k) for k in ("attempt", "source", "files", "verdict", "rolled_back", "newly_passing",
                                "newly_failing", "still_failing", "diagnosis", "patch_hash")}
        for h in (state.get("repair_history") or [])
    ]
    output = f"{exec_res.get('stdout', '')}\n{exec_res.get('stderr', '')}".strip()
    return {
        "status": cls["status"],
        "sandbox": cls["sandbox"],
        "isolated": cls["isolated"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence": {
            "command": exec_res.get("command"),
            "exit_code": exec_res.get("exit_code"),
            "duration_ms": exec_res.get("duration_ms"),
            "timed_out": exec_res.get("timed_out"),
            "tests": {
                "collected": len(outcomes),
                "passed": sum(1 for v in outcomes.values() if v == "passed"),
                "failed": sum(1 for v in outcomes.values() if v == "failed"),
                "errors": sum(1 for v in outcomes.values() if v == "error"),
                "skipped": sum(1 for v in outcomes.values() if v == "skipped"),
            },
            "test_outcomes": outcomes,
            "output_tail": output[-3000:],
        },
        "repair": {
            "iterations": state.get("iteration", 0),
            "attempts": history,
            "kept": sum(1 for h in history if h.get("verdict") in ("fixed", "improved")),
            "rolled_back": sum(1 for h in history if h.get("rolled_back")),
        },
    }


def render_markdown(report: Dict[str, Any]) -> str:
    ev, rep = report["evidence"], report["repair"]
    t = ev["tests"]
    lines = [
        "# Verification report",
        "",
        f"**Status:** {_BADGE.get(report['status'], report['status'])}  ",
        f"**Executed in:** `{report['sandbox']}` sandbox"
        + ("" if report["isolated"] else " (not isolated: local subprocess)") + "  ",
        f"**Generated:** {report['generated_at']}",
        "",
        "This status comes only from running the project. No agent's description of the code counts as evidence.",
        "",
        "## Evidence",
        "",
        f"- Command: `{ev['command'] or 'n/a'}`",
        f"- Exit code: `{ev['exit_code']}`" + (" (timed out)" if ev.get("timed_out") else ""),
        f"- Tests: {t['passed']} passed, {t['failed']} failed, {t['errors']} errors, {t['skipped']} skipped "
        f"({t['collected']} collected)",
        "",
    ]
    if ev["test_outcomes"]:
        lines += ["| Test | Outcome |", "| --- | --- |"]
        lines += [f"| `{k}` | {v} |" for k, v in sorted(ev["test_outcomes"].items())]
        lines.append("")
    if rep["attempts"]:
        lines += [
            "## Self-healing attempts",
            "",
            f"{len(rep['attempts'])} attempt(s): {rep['kept']} kept, {rep['rolled_back']} rolled back.",
            "",
            "| # | Source | Files | Verdict | Effect |",
            "| --- | --- | --- | --- | --- |",
        ]
        for a in rep["attempts"]:
            effect = []
            if a.get("newly_passing"):
                effect.append(f"now passing: {', '.join(a['newly_passing'])}")
            if a.get("newly_failing"):
                effect.append(f"broke: {', '.join(a['newly_failing'])}")
            if a.get("rolled_back"):
                effect.append("rolled back")
            lines.append(f"| {a['attempt']} | {a.get('source')} | {', '.join(a.get('files') or []) or '—'} | "
                         f"{a.get('verdict') or 'pending'} | {'; '.join(effect) or '—'} |")
        lines.append("")
    if ev["output_tail"]:
        lines += ["## Output (tail)", "", "```", ev["output_tail"], "```", ""]
    return "\n".join(lines)


def write_report(report: Dict[str, Any], project_dir: str) -> Dict[str, str]:
    """Writes VERIFICATION.md and verification.json into the project; returns them as files."""
    root = Path(project_dir)
    md, js = render_markdown(report), json.dumps(report, indent=2, default=str)
    if root.is_dir():
        (root / "VERIFICATION.md").write_text(md, encoding="utf-8")
        (root / "verification.json").write_text(js, encoding="utf-8")
    return {"VERIFICATION.md": md, "verification.json": js}
