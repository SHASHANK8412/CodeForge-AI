"""
Self-healing loop: per-test evidence, verdicts, rollback, no-repeat, early stop.

The loop tests run the real testing and patch nodes on a small FastAPI project on disk, with its real tests (local
sandbox opt-in from tests/conftest.py); the patches are scripted, so no model is needed.
"""

import asyncio
import importlib.util
from pathlib import Path

import pytest

from backend.execution import repair_policy as rp

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


# --------------------------------------------------------------------------- #
# The loop on the real testing and patch nodes
# --------------------------------------------------------------------------- #

def _loop(tmp_path, monkeypatch):
    """A todo API whose GET /todos/{id} returns 200 for unknown ids (2 of 3 tests pass), after its first test run."""
    from backend.graph import parallel_workflow as wf
    fake = _fake()
    calls = []

    async def write_tests(*_a, **_k):
        calls.append(1)
        return "```python\n# filepath: tests/test_todos.py\n" + fake.TESTS + "```\n"

    monkeypatch.setattr(wf.testing_agent, "run_async", write_tests)
    monkeypatch.chdir(tmp_path)                       # testing_node also writes a copy under ./generated_projects
    proj = tmp_path / "todo"
    (proj / "backend").mkdir(parents=True)
    (proj / "tests").mkdir()
    (proj / "backend" / "main.py").write_text(fake.BUGGY_MAIN, encoding="utf-8")
    (proj / "tests" / "test_todos.py").write_text(fake.TESTS, encoding="utf-8")
    state = {"project_path": str(proj), "plan": {"project_name": "todo"}, "backend": "", "frontend": "",
             "files": {"backend/main.py": fake.BUGGY_MAIN, "tests/test_todos.py": fake.TESTS},
             "fixes": [], "retry_count": 0}
    state.update(asyncio.run(wf.testing_node(state)))
    assert state["test_results"]["success"] is False and len(calls) == 1
    return wf, fake, state, proj, calls


def _attempt(wf, state, cycle, main_py):
    """One repair cycle with a scripted patch: patch -> re-run the tests (and judge the patch)."""
    state["fixes"] = state["fixes"] + [{"changes": {"backend/main.py": main_py}, "strategy": "llm_search_replace",
                                        "root_cause": "GET /todos/{id} returns 200 for an unknown id"}]
    state["current_debug_cycle"] = cycle
    state.update(asyncio.run(wf.patch_node(state)))
    state.update(asyncio.run(wf.testing_node(state)))
    return state["repair_history"][-1]


def test_a_regressing_patch_is_rolled_back_on_disk_then_a_fix_is_kept(tmp_path, monkeypatch):
    wf, fake, state, proj, calls = _loop(tmp_path, monkeypatch)
    main_py = proj / "backend" / "main.py"

    first = _attempt(wf, state, 1, fake.REGRESSING_MAIN)          # deletes /health: test_health now fails
    assert first["verdict"] == "regressed" and first["rolled_back"] is True
    assert first["newly_failing"] == ["tests/test_todos.py::test_health"]
    assert main_py.read_text(encoding="utf-8") == fake.BUGGY_MAIN, "the regression is not left on disk"
    assert state["files"]["backend/main.py"] == fake.BUGGY_MAIN
    assert state["test_results"]["failed_tests"] == ["tests/test_todos.py::test_missing_todo_is_404"], \
        "the evidence is from the restored files"
    assert state["applied_fix"]["rolled_back"] is True, "a rolled-back patch is never remembered as a verified fix"

    second = _attempt(wf, state, 2, fake.FIXED_MAIN)
    assert second["verdict"] == "fixed" and not second.get("rolled_back")
    assert second["newly_passing"] == ["tests/test_todos.py::test_missing_todo_is_404"]
    assert main_py.read_text(encoding="utf-8") == fake.FIXED_MAIN and state["test_results"]["success"] is True
    assert len(calls) == 1, "the suite is generated once: repair cycles re-run the same tests"
    assert wf.repair_escalation(state) is None


def test_a_rolled_back_patch_is_never_reapplied_and_the_loop_stops_without_progress(tmp_path, monkeypatch):
    wf, fake, state, proj, _ = _loop(tmp_path, monkeypatch)
    assert _attempt(wf, state, 1, fake.REGRESSING_MAIN)["verdict"] == "regressed"
    assert wf.repair_escalation(state) is None, "one bad attempt is not yet a stall"

    again = _attempt(wf, state, 2, fake.REGRESSING_MAIN)
    assert again["verdict"] == "no_patch" and again["note"] == "same patch as a rolled-back attempt"
    assert (proj / "backend" / "main.py").read_text(encoding="utf-8") == fake.BUGGY_MAIN
    assert wf.repair_escalation(state) == "STOPPED_NO_PROGRESS"


def test_a_patch_that_changes_nothing_is_rolled_back(tmp_path, monkeypatch):
    wf, fake, state, proj, _ = _loop(tmp_path, monkeypatch)
    attempt = _attempt(wf, state, 1, fake.NO_EFFECT_MAIN)
    assert attempt["verdict"] == "no_effect" and attempt["rolled_back"] is True
    assert (proj / "backend" / "main.py").read_text(encoding="utf-8") == fake.BUGGY_MAIN


def test_the_proposer_skips_rolled_back_patches_and_tells_the_model_what_was_tried(monkeypatch):
    import backend.services.llm as llm
    from backend.agents.repair_strategies import propose_repairs
    monkeypatch.setenv("AIFORGE_LLM_REPAIR", "1")
    files = {"backend/main.py": "app = FastAPI()\n"}
    errors = [{"file": "backend/main.py", "line": 1, "message": "Undefined name `FastAPI`"}]
    strategy, changes = propose_repairs(files, "", errors)
    assert strategy == "add_missing_imports"

    prompts = []
    monkeypatch.setattr(llm, "generate_text", lambda s, p, **k: prompts.append(p) or "no edits")
    history = rp.history_for_prompt([{"attempt": 1, "source": strategy, "files": ["backend/main.py"],
                                      "verdict": "regressed", "newly_failing": ["tests/test_main.py::test_health"]}])
    assert propose_repairs(files, "", errors, rejected={rp.patch_hash(changes)}, history=history) == ("none", {})
    assert len(prompts) == 1, "the deterministic patch was skipped and the model got its turn"
    assert "ROLLED BACK" in prompts[0] and "test_health" in prompts[0]



def test_fixing_one_error_of_a_chain_is_progress_not_no_effect():
    """Seen in the benchmark: the import repair added the missing `Depends`; the tests still errored, now on the next
    bug, and the correct fix was rolled back as no_effect."""
    before = {**_snap(1, [], ["t::a", "t::b"]), "error_line": "E   NameError: name 'Depends' is not defined"}
    after = {**_snap(1, [], ["t::a", "t::b"]), "error_line": "E   ImportError: cannot import name 'get_db'"}
    assert rp.judge_attempt(before, after)["verdict"] == "improved"
    same = {**_snap(1, [], ["t::a", "t::b"]), "error_line": "E   NameError: name 'Depends' is not defined"}
    assert rp.judge_attempt(before, same)["verdict"] == "no_effect", "the same error is still no progress"
    broke = {**_snap(1, [], ["t::a", "t::b"]), "error_line": ""}
    assert rp.judge_attempt(before, broke)["verdict"] == "no_effect", "no error line to compare: not counted"
