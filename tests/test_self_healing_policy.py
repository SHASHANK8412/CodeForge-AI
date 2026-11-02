"""
Self-healing loop: per-test evidence, verdicts, rollback, no-repeat, early stop,
and the evidence-backed verification report.

The end-to-end tests run the real LangGraph pipeline with a scripted LLM
(tests/fixtures/fake_llm.py) and the local sandbox, so no Ollama is needed.
"""

import asyncio
import importlib.util
from pathlib import Path

import pytest

from backend.execution import repair_policy as rp
from backend.execution.verification_report import build_verification_report, render_markdown
from benchmarks import harness

FIXTURES = Path(__file__).parent / "fixtures"

PYTEST_OUT = """
PASSED tests/test_todos.py::test_health
FAILED tests/test_todos.py::test_missing_todo_is_404 - assert 200 == 404
ERROR tests/test_db.py::test_conn - fixture 'db' not found
SKIPPED [1] tests/test_x.py:3: later
=== 1 failed, 1 passed, 1 error in 0.12s ===
"""


def _fake():
    spec = importlib.util.spec_from_file_location("fake_llm", FIXTURES / "fake_llm.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _snap(exit_code, passing=(), failing=()):
    return {"exit_code": exit_code, "passing": list(passing), "failing": list(failing),
            "outcomes": {**{p: "passed" for p in passing}, **{f: "failed" for f in failing}}}


# --------------------------------------------------------------------------- #
# Policy units
# --------------------------------------------------------------------------- #

def test_parse_pytest_outcomes():
    out = rp.parse_pytest_outcomes(PYTEST_OUT)
    assert out == {"tests/test_todos.py::test_health": "passed",
                   "tests/test_todos.py::test_missing_todo_is_404": "failed",
                   "tests/test_db.py::test_conn": "error"}
    assert rp.failing(out) == ["tests/test_db.py::test_conn", "tests/test_todos.py::test_missing_todo_is_404"]


@pytest.mark.parametrize("before,after,verdict", [
    (_snap(1, ["a"], ["b"]), _snap(0, ["a", "b"]), "fixed"),
    (_snap(1, ["a"], ["b", "c"]), _snap(1, ["a", "b"], ["c"]), "improved"),
    (_snap(1, ["a"], ["b"]), _snap(1, [], ["a", "b"]), "regressed"),
    (_snap(1, ["a"], ["b"]), _snap(1, ["a"], ["b"]), "no_effect"),
    (_snap(0, ["a"]), _snap(1, ["a"], []), "regressed"),       # build broke
    (_snap(1), _snap(1, ["a"], ["b"]), "improved"),            # SyntaxError -> tests now run
])
def test_judge_attempt(before, after, verdict):
    assert rp.judge_attempt(before, after)["verdict"] == verdict


def test_judge_reports_test_level_diff():
    j = rp.judge_attempt(_snap(1, ["a", "x"], ["b"]), _snap(1, ["b"], ["a", "x"]))
    assert j["newly_failing"] == ["a", "x"] and j["newly_passing"] == ["b"]


def test_fingerprint_is_stable_across_paths_and_timings():
    a = {"exit_code": 1, "stdout": PYTEST_OUT, "stderr": 'File "/tmp/run1/backend/main.py", line 3\nE   KeyError: 5'}
    b = {"exit_code": 1, "stdout": PYTEST_OUT.replace("0.12s", "9.99s"),
         "stderr": 'File "/home/x/backend/main.py", line 9\nE   KeyError: 5'}
    assert rp.failure_fingerprint(a) == rp.failure_fingerprint(b)
    assert rp.failure_fingerprint(a) != rp.failure_fingerprint({**a, "exit_code": 2})


def test_patch_hash_ignores_trailing_whitespace_and_order():
    assert rp.patch_hash({"a.py": "x\n", "b.py": "y"}) == rp.patch_hash({"b.py": "y\n\n", "a.py": "x"})


def test_stalled():
    assert rp.stalled([{"verdict": "fixed"}, {"verdict": "no_effect"}, {"verdict": "regressed"}])
    assert not rp.stalled([{"verdict": "no_effect"}, {"verdict": "improved"}])
    assert not rp.stalled([{"verdict": "no_effect"}])


def test_history_for_prompt_mentions_rollbacks():
    text = rp.history_for_prompt([{"attempt": 1, "source": "llm", "files": ["backend/main.py"],
                                   "verdict": "regressed", "newly_failing": ["t::test_health"]}])
    assert "ROLLED BACK" in text and "test_health" in text


@pytest.mark.parametrize("exec_res,status", [
    ({}, "NOT_RUN"),
    ({"exit_code": 0, "stdout": "PASSED t.py::test_a\n"}, "VERIFIED"),
    ({"exit_code": 0, "stdout": "Listing '.'...\n"}, "BUILD_ONLY"),   # compileall only
    ({"exit_code": 1, "stdout": PYTEST_OUT}, "FAILED"),
])
def test_classify_verification(exec_res, status):
    assert rp.classify_verification(exec_res, "docker")["status"] == status


def test_verification_report_is_built_from_evidence_only():
    state = {
        "status": "PASS",                       # the pipeline's claim...
        "test_results": {"success": True, "passed": 1, "total": 1},
        "execution_results": {"exit_code": 0, "stdout": "Compiling...", "sandbox": "local",
                              "command": "python -m compileall -q ."},
    }
    report = build_verification_report(state)
    assert report["status"] == "BUILD_ONLY"   # ...does not make it VERIFIED
    assert report["isolated"] is False
    md = render_markdown(report)
    assert "BUILD ONLY" in md and "not isolated" in md


# --------------------------------------------------------------------------- #
# End-to-end on the real graph
# --------------------------------------------------------------------------- #

def _run(tmp_path, monkeypatch, repair_sequence, max_iterations=3):
    import backend.services.llm as llm
    fake = _fake()
    calls = fake.install_on(monkeypatch, llm, repair_sequence=[getattr(fake, n) for n in repair_sequence])
    monkeypatch.setenv("AIFORGE_SANDBOX", "local")
    monkeypatch.chdir(tmp_path)
    res = asyncio.run(harness.run_benchmark(task_ids=["todo-basic"], label="heal", runs_dir=tmp_path / "runs",
                                            max_iterations=max_iterations))
    run_dir = next((tmp_path / "runs").iterdir())
    return res["tasks"][0], calls, run_dir


def test_regressing_patch_is_rolled_back_then_fixed(tmp_path, monkeypatch):
    task, calls, run_dir = _run(tmp_path, monkeypatch, ["REGRESSING_MAIN", "FIXED_MAIN"])
    history = task["pipeline"]["repair_history"]

    assert [h["verdict"] for h in history] == ["regressed", "fixed"], (task["valid"], task.get("invalid_reason"), task["telemetry"]["llm_calls"], task["pipeline"], task["initial"] and task["initial"]["tests_passed"])
    assert history[0]["rolled_back"] is True
    assert history[0]["newly_failing"] == ["tests/test_todos.py::test_health"]
    assert history[1]["newly_passing"] == ["tests/test_todos.py::test_missing_todo_is_404"]

    # The second repair prompt told the model what went wrong the first time.
    repair_prompts = [u for s, u in calls if "fixing a FastAPI project" in s]
    assert len(repair_prompts) == 2
    assert "ROLLED BACK" in repair_prompts[1] and "test_health" in repair_prompts[1]

    assert task["pipeline"]["verification_status"] == "VERIFIED"
    assert task["final"]["tests_passed"] == 3 and task["final"]["routes_matched"] == 6  # /health is back

    report = (run_dir / "projects" / "_pipeline" / "todo-basic" / "VERIFICATION.md").read_text()
    assert "VERIFIED" in report and "rolled back" in report


def test_loop_stops_early_when_no_progress(tmp_path, monkeypatch):
    task, calls, _ = _run(tmp_path, monkeypatch, ["NO_EFFECT_MAIN", "REGRESSING_MAIN", "FIXED_MAIN"],
                          max_iterations=5)
    history = task["pipeline"]["repair_history"]
    assert [h["verdict"] for h in history] == ["no_effect", "regressed"]
    assert all(h["rolled_back"] for h in history)
    # Stopped after two non-improving attempts instead of using all 5 iterations,
    # and the project on disk is the original (rolled back), not the broken patch.
    assert sum(1 for s, _ in calls if "fixing a FastAPI project" in s) == 2
    assert task["pipeline"]["verification_status"] == "FAILED"
    assert task["final"]["tests_passed"] == 2 and task["final"]["routes_matched"] == 6


def test_rejected_patch_is_never_reapplied(tmp_path, monkeypatch):
    task, calls, _ = _run(tmp_path, monkeypatch, ["REGRESSING_MAIN", "REGRESSING_MAIN", "FIXED_MAIN"],
                          max_iterations=4)
    verdicts = [h["verdict"] for h in task["pipeline"]["repair_history"]]
    # Attempt 2 proposed the same rejected patch: skipped (no_patch), not applied
    # again; two non-improving attempts in a row then trigger the early stop.
    assert verdicts == ["regressed", "no_patch"]
    assert task["pipeline"]["verification_status"] == "FAILED"
    assert task["final"]["routes_matched"] == 6  # the regressing patch is not on disk
