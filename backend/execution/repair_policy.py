"""
Repair policy for the self-healing loop.

The debug -> patch -> re-run loop is only useful if it can tell whether a patch
helped. This module gives it the evidence to decide:

* ``parse_pytest_outcomes`` reads per-test results from pytest's ``-rA``
  summary (``PASSED tests/test_x.py::test_a``) so we know *which* tests
  pass before and after a patch, not just how many.
* ``failure_fingerprint`` is a stable hash of "what is failing and why"; the
  same fingerprint twice means the loop is stuck.
* ``judge_attempt`` compares before/after and returns a verdict:

  ============  ======================================================
  ``fixed``     build exits 0 (and every collected test passes)
  ``improved``  fewer failing tests, and nothing that passed now fails
  ``regressed`` something that passed now fails, or the build broke
  ``no_effect`` same failures as before
  ============  ======================================================

  The graph rolls back ``regressed`` and ``no_effect`` patches so the loop
  never builds on top of a change that made things worse.
* ``patch_hash`` identifies a patch so an already-rejected one is never
  re-applied.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, Iterable, List, Optional

# "PASSED tests/test_a.py::test_x", "FAILED tests/test_a.py::test_y - assert 1 == 2",
# "ERROR tests/test_a.py::test_z - fixture 'db' not found", "ERROR tests/test_b.py" (collection)
_OUTCOME_RE = re.compile(r"^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)\s+(\S+?)(?:\s+-\s+.*)?$", re.MULTILINE)
_NORMALIZE_RE = [
    (re.compile(r"0x[0-9a-fA-F]+"), "0x?"),
    (re.compile(r"line \d+"), "line ?"),
    (re.compile(r"\d+\.\d+s"), "?s"),
    (re.compile(r"/[^\s\"']*/(?=[\w.-]+\.py)"), ""),  # strip absolute dirs, keep file name
]

VERDICT_FIXED = "fixed"
VERDICT_IMPROVED = "improved"
VERDICT_REGRESSED = "regressed"
VERDICT_NO_EFFECT = "no_effect"
KEEP_VERDICTS = {VERDICT_FIXED, VERDICT_IMPROVED}


def parse_pytest_outcomes(output: str) -> Dict[str, str]:
    """Maps pytest node id -> passed | failed | error | skipped (needs ``-rA``)."""
    outcomes: Dict[str, str] = {}
    for status, node in _OUTCOME_RE.findall(output or ""):
        status = status.lower()
        if status in ("xfail",):
            status = "skipped"
        elif status == "xpass":
            status = "passed"
        outcomes[node] = status
    return outcomes


def failing(outcomes: Dict[str, str]) -> List[str]:
    return sorted(n for n, s in outcomes.items() if s in ("failed", "error"))


def passing(outcomes: Dict[str, str]) -> List[str]:
    return sorted(n for n, s in outcomes.items() if s == "passed")


def _last_error_line(text: str) -> str:
    for line in reversed((text or "").strip().splitlines()):
        line = line.strip()
        if re.match(r"^(E\s+)?\w*(Error|Exception)\b", line) or line.startswith("E "):
            for pattern, repl in _NORMALIZE_RE:
                line = pattern.sub(repl, line)
            return line[:200]
    return ""


def failure_fingerprint(exec_results: Dict[str, Any]) -> str:
    """Stable id of the current failure: failing tests + last error line + exit code."""
    out = f"{exec_results.get('stdout', '')}\n{exec_results.get('stderr', '')}"
    payload = {
        "exit": exec_results.get("exit_code"),
        "failing": failing(parse_pytest_outcomes(out)),
        "error": _last_error_line(out),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


def snapshot(exec_results: Dict[str, Any]) -> Dict[str, Any]:
    """The evidence about one run that a repair attempt is judged against."""
    out = f"{exec_results.get('stdout', '')}\n{exec_results.get('stderr', '')}"
    outcomes = parse_pytest_outcomes(out)
    return {
        "exit_code": exec_results.get("exit_code"),
        "status": str(exec_results.get("status", "")),
        "outcomes": outcomes,
        "failing": failing(outcomes),
        "passing": passing(outcomes),
        "fingerprint": failure_fingerprint(exec_results),
        "error_line": _last_error_line(out),
    }


def judge_attempt(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
    """Compares two snapshots; returns the verdict and the test-level diff."""
    before_pass, after_pass = set(before.get("passing", [])), set(after.get("passing", []))
    before_fail, after_fail = set(before.get("failing", [])), set(after.get("failing", []))
    newly_failing = sorted(before_pass - after_pass)
    newly_passing = sorted(after_pass - before_pass)
    build_broke = before.get("exit_code") == 0 and after.get("exit_code") != 0

    if after.get("exit_code") == 0 and not after_fail:
        verdict = VERDICT_FIXED
    elif newly_failing or build_broke:
        verdict = VERDICT_REGRESSED
    elif newly_passing or len(after_fail) < len(before_fail) or (
            # e.g. a SyntaxError (no tests collected) became runnable tests
            not before.get("outcomes") and after.get("outcomes")):
        verdict = VERDICT_IMPROVED
    else:
        verdict = VERDICT_NO_EFFECT
    return {
        "verdict": verdict,
        "newly_passing": newly_passing,
        "newly_failing": newly_failing,
        "still_failing": sorted(after_fail & before_fail),
    }


def patch_hash(changes: Dict[str, str]) -> str:
    canonical = json.dumps({k: (v or "").strip() for k, v in sorted((changes or {}).items())}, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def stalled(history: Iterable[Dict[str, Any]], limit: int = 2) -> bool:
    """True if the last ``limit`` judged attempts all failed to make progress."""
    judged = [h for h in history if h.get("verdict")]
    tail = judged[-limit:]
    return len(tail) == limit and all(h["verdict"] not in KEEP_VERDICTS for h in tail)


def history_for_prompt(history: Iterable[Dict[str, Any]], max_items: int = 4) -> str:
    """Short description of earlier attempts so the LLM doesn't repeat them."""
    lines: List[str] = []
    for h in list(history)[-max_items:]:
        if not h.get("verdict"):
            continue
        action = "kept" if h["verdict"] in KEEP_VERDICTS else "ROLLED BACK"
        detail = ""
        if h.get("newly_failing"):
            detail = f"; broke {', '.join(h['newly_failing'][:3])}"
        elif h.get("still_failing"):
            detail = f"; still failing {', '.join(h['still_failing'][:3])}"
        lines.append(f"- attempt {h.get('attempt')} ({h.get('source', 'llm')}) changed "
                     f"{', '.join(h.get('files', []))}: {h['verdict']}, {action}{detail}")
    return "\n".join(lines)


def classify_verification(exec_results: Dict[str, Any], sandbox: Optional[str]) -> Dict[str, Any]:
    """Evidence-based status of the final project.

    * ``VERIFIED``      tests were collected and every one passed
    * ``BUILD_ONLY``    the build/compile step passed but no tests ran
    * ``FAILED``        build or tests failed
    * ``NOT_RUN``       nothing was executed
    """
    if not exec_results or "exit_code" not in exec_results:
        status = "NOT_RUN"
    else:
        snap = snapshot(exec_results)
        ran = [n for n, s in snap["outcomes"].items() if s != "skipped"]
        if exec_results.get("exit_code") != 0 or snap["failing"]:
            status = "FAILED"
        elif ran:
            status = "VERIFIED"
        else:
            status = "BUILD_ONLY"
    return {"status": status, "sandbox": sandbox or "unknown", "isolated": sandbox == "docker"}
