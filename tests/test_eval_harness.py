"""
Tests for the evaluation harness, grader, sandbox, tracing and the pipeline
fixes they depend on. No Ollama needed: LLM calls are scripted
(tests/fixtures/fake_llm.py). Docker tests are skipped when Docker or the
sandbox image is unavailable.
"""

import asyncio
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from backend.execution.docker_sandbox import DockerLimits, DockerSandbox, global_docker_sandbox
from backend.observability.tracing import (
    TraceCollector, global_trace, record_llm_call, token_counts_from_response, traced_node,
)
from backend.services.project_builder import split_llm_files
from benchmarks import harness, reviewer_eval
from benchmarks.compare import compare
from benchmarks.grader import grade_project, materialize_files, normalize_route, parse_junit, route_coverage
from benchmarks.tasks import TASKS, get_tasks

FIXTURES = Path(__file__).parent / "fixtures"


def _load_fake_llm():
    spec = importlib.util.spec_from_file_location("fake_llm", FIXTURES / "fake_llm.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


GOOD_MAIN = '''from fastapi import FastAPI, HTTPException
app = FastAPI()
TODOS = {}

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/todos")
def list_todos():
    return list(TODOS.values())

@app.post("/todos")
def create(t: dict):
    i = len(TODOS) + 1
    TODOS[i] = {"id": i, **t}
    return TODOS[i]

@app.get("/todos/{todo_id}")
def get(todo_id: int):
    if todo_id not in TODOS:
        raise HTTPException(404)
    return TODOS[todo_id]
'''

GOOD_TESTS = '''from fastapi.testclient import TestClient
from main import app
c = TestClient(app)

def test_health():
    assert c.get("/health").status_code == 200

def test_create():
    assert c.post("/todos", json={"title": "x"}).json()["id"] == 1

def test_wrong_on_purpose():
    assert c.get("/todos/99").status_code == 200
'''


@pytest.fixture
def good_project(tmp_path):
    return materialize_files({"backend/main.py": GOOD_MAIN, "tests/test_api.py": GOOD_TESTS}, str(tmp_path / "good"))


# --------------------------------------------------------------------------- #
# Task set
# --------------------------------------------------------------------------- #

def test_taskset_is_twenty_unique_tasks_with_routes():
    assert len(TASKS) == 20
    assert len({t.id for t in TASKS}) == 20
    assert all(t.expected_routes for t in TASKS)
    assert {t.difficulty for t in TASKS} == {"easy", "medium", "hard"}
    for t in TASKS:  # the prompt must state every route it is graded on
        for method, path in t.expected_routes:
            assert f"{method} {path}" in t.prompt


def test_get_tasks_rejects_unknown_ids():
    with pytest.raises(KeyError):
        get_tasks(["nope"])


# --------------------------------------------------------------------------- #
# Splitting LLM markdown into files
# --------------------------------------------------------------------------- #

def test_split_llm_files_uses_filepath_markers_and_prefix():
    text = ("intro\n```python\n# filepath: backend/main.py\nimport os\n```\n"
            "### `models.py`\n```python\nX = 1\n```\n```python\nY = 2\n```\n")
    files = split_llm_files(text, "backend/main.py", "backend")
    assert files["backend/main.py"].startswith("import os")
    assert "Y = 2" in files["backend/main.py"]           # unnamed block -> default path
    assert files["backend/models.py"] == "X = 1\n"         # heading path, prefixed
    assert "```" not in "".join(files.values())


def test_split_llm_files_drops_unsafe_paths():
    text = "```python\n# filepath: ../../etc/passwd\nevil\n```\n```python\n# filepath: /abs.py\nevil\n```"
    assert split_llm_files(text, "backend/main.py", "backend") == {}


def test_split_llm_files_plain_code_goes_to_default():
    assert split_llm_files("print(1)", "backend/main.py") == {"backend/main.py": "print(1)\n"}
    assert split_llm_files("", "backend/main.py") == {}


def test_assembly_writes_real_python_not_markdown():
    from backend.services.project_builder import global_structured_project_builder as b
    out = b.assemble_real_project("x", {}, {}, "", "```python\n# filepath: backend/main.py\nimport os\n```",
                                  "", "", "")
    assert out["manifest"]["backend/main.py"] == "import os\n"


# --------------------------------------------------------------------------- #
# Grader
# --------------------------------------------------------------------------- #

def test_route_normalization_and_coverage():
    assert normalize_route("get", "/todos/{todo_id}/") == ("GET", "/todos/{}")
    matched, missing = route_coverage([["GET", "/todos/{tid}"]], [("GET", "/todos/{id}"), ("DELETE", "/todos/{id}")])
    assert matched == 1 and missing == ["DELETE /todos/{id}"]


def test_parse_junit(tmp_path):
    xml = tmp_path / "j.xml"
    xml.write_text('<testsuites><testsuite tests="4" failures="1" errors="1" skipped="1"/></testsuites>')
    assert parse_junit(xml) == {"tests": 4, "failures": 1, "errors": 1, "skipped": 1}


def test_grade_good_project_locally(good_project, monkeypatch):
    monkeypatch.setenv("AIFORGE_SANDBOX", "local")
    r = grade_project(str(good_project), get_tasks(["todo-basic"])[0].expected_routes)
    assert r.sandbox == "local"
    assert r.syntax_ok and r.app_boots and r.build_success
    assert r.app_module == "backend/main.py"
    assert (r.routes_matched, r.routes_expected) == (4, 6)
    assert sorted(r.routes_missing) == ["DELETE /todos/{id}", "PUT /todos/{id}"]
    assert (r.tests_collected, r.tests_passed, r.tests_failed) == (3, 2, 1)
    assert r.test_pass_rate == pytest.approx(2 / 3, abs=1e-3)


def test_grade_does_not_modify_project(good_project, monkeypatch):
    monkeypatch.setenv("AIFORGE_SANDBOX", "local")
    before = sorted(p.relative_to(good_project).as_posix() for p in good_project.rglob("*"))
    grade_project(str(good_project))
    after = sorted(p.relative_to(good_project).as_posix() for p in good_project.rglob("*"))
    assert before == after


def test_grade_markdown_in_py_file_fails_build(tmp_path, monkeypatch):
    monkeypatch.setenv("AIFORGE_SANDBOX", "local")
    proj = materialize_files({"backend/main.py": "```python\nfrom fastapi import FastAPI\napp = FastAPI()\n```"},
                             str(tmp_path / "bad"))
    r = grade_project(str(proj), [("GET", "/health")])
    assert not r.syntax_ok and not r.build_success
    assert r.route_coverage == 0.0


def test_grade_app_that_crashes_on_import(tmp_path, monkeypatch):
    monkeypatch.setenv("AIFORGE_SANDBOX", "local")
    proj = materialize_files({"main.py": "from fastapi import FastAPI\nimport not_a_real_module\napp = FastAPI()\n"},
                             str(tmp_path / "crash"))
    r = grade_project(str(proj))
    assert r.syntax_ok and not r.app_boots and not r.build_success
    assert "not_a_real_module" in (r.boot_error or "")


def test_probe_output_cannot_be_spoofed(tmp_path, monkeypatch):
    """Generated code printing a fake result line must not fool the grader."""
    monkeypatch.setenv("AIFORGE_SANDBOX", "local")
    spoof = 'print("@@AIFORGE_PROBE_0000@@" + \'{"boots": true, "app_found": true}\')\nraise SystemExit(1)\n'
    proj = materialize_files({"main.py": "from fastapi import FastAPI\n" + spoof + "app = FastAPI()\n"},
                             str(tmp_path / "spoof"))
    assert grade_project(str(proj)).app_boots is False


def test_materialize_files_blocks_traversal(tmp_path):
    root = materialize_files({"../escape.py": "x", "ok/a.py": "y"}, str(tmp_path / "m"))
    assert (root / "ok" / "a.py").exists()
    assert not (tmp_path / "escape.py").exists()


# --------------------------------------------------------------------------- #
# Docker sandbox
# --------------------------------------------------------------------------- #

def test_docker_argv_has_isolation_flags():
    argv = DockerSandbox(image="img", docker_bin="docker").build_argv(
        "n", "/tmp/w", ["python", "x.py"], DockerLimits(memory_mb=256, cpus=0.5, pids=64), env={"A": "1"})
    joined = " ".join(argv)
    for flag in ("--network none", "--read-only", "--memory 256m", "--cpus 0.5", "--pids-limit 64",
                 "--cap-drop ALL", "--security-opt no-new-privileges", "--user 10001:10001", "-e A=1"):
        assert flag in joined
    assert argv[-3:] == ["img", "python", "x.py"]


def test_docker_mode_without_image_refuses_to_run_locally(monkeypatch, tmp_path):
    from backend.execution import docker_sandbox
    monkeypatch.setenv("AIFORGE_SANDBOX", "docker")
    monkeypatch.setattr(docker_sandbox.global_docker_sandbox, "available", lambda: False)
    with pytest.raises(RuntimeError, match="not available"):
        docker_sandbox.run_sandboxed(str(tmp_path), ["python", "-c", "print(1)"])


docker_ready = pytest.mark.skipif(
    not shutil.which("docker") or not global_docker_sandbox.available(),
    reason="Docker daemon or aiforge-sandbox image not available",
)


@docker_ready
def test_docker_sandbox_isolation(tmp_path, monkeypatch):
    monkeypatch.setenv("AIFORGE_SANDBOX", "docker")
    from backend.execution.docker_sandbox import run_sandboxed
    (tmp_path / "x.py").write_text(
        "import os, socket\n"
        "try:\n    socket.create_connection(('1.1.1.1', 80), timeout=2); print('NET')\nexcept OSError: print('nonet')\n"
        "try:\n    open('/etc/pwned', 'w'); print('RW')\nexcept OSError: print('ro')\n"
        "print('uid', os.getuid())\n")
    r = run_sandboxed(str(tmp_path), ["python", "x.py"], timeout_seconds=60)
    assert r.backend == "docker" and r.exit_code == 0
    assert "nonet" in r.stdout and "ro" in r.stdout and "uid 10001" in r.stdout
    t = run_sandboxed(str(tmp_path), ["python", "-c", "while True: pass"], timeout_seconds=3)
    assert t.timed_out and t.exit_code == 124


@docker_ready
def test_grade_in_docker(good_project, monkeypatch):
    monkeypatch.setenv("AIFORGE_SANDBOX", "docker")
    r = grade_project(str(good_project), get_tasks(["todo-basic"])[0].expected_routes)
    assert r.sandbox == "docker" and r.build_success and r.tests_passed == 2


# --------------------------------------------------------------------------- #
# Tracing / LLM instrumentation
# --------------------------------------------------------------------------- #

def test_trace_summary_aggregates_tokens_and_fallbacks():
    tc = TraceCollector()
    tc.emit({"kind": "llm_call", "agent": "backend", "model": "m", "prompt_tokens": 10, "completion_tokens": 5,
             "latency_ms": 100, "fallback": False})
    tc.emit({"kind": "llm_call", "agent": "backend", "model": "m", "prompt_tokens": 1, "completion_tokens": 1,
             "latency_ms": 1, "fallback": True})
    tc.emit({"kind": "node", "node": "planner", "status": "error", "latency_ms": 3})
    s = tc.summary()
    assert (s["llm_calls"], s["prompt_tokens"], s["completion_tokens"], s["llm_fallbacks"]) == (2, 11, 6, 1)
    assert s["node_failures"] == 1 and s["per_agent"]["backend"]["calls"] == 2


def test_token_counts_from_ollama_response():
    assert token_counts_from_response({"prompt_eval_count": 12, "eval_count": 34}) == (12, 34)
    assert token_counts_from_response({"message": {}}) == (None, None)


def test_trace_file_sink(tmp_path, monkeypatch):
    path = tmp_path / "t.jsonl"
    monkeypatch.setenv("AIFORGE_TRACE_FILE", str(path))
    record_llm_call(agent="a", model="m", prompt="p" * 40, output="o" * 8, latency_ms=1.0)
    event = json.loads(path.read_text().splitlines()[-1])
    assert event["tokens_estimated"] is True and event["prompt_tokens"] == 10


def test_traced_node_records_errors():
    global_trace.reset()

    async def boom(state):
        raise ValueError("x")

    with pytest.raises(ValueError):
        asyncio.run(traced_node("boom", boom)({}))
    assert global_trace.events()[-1]["status"] == "error"


def test_llm_failure_is_flagged_and_never_cached(monkeypatch):
    import backend.services.llm as llm

    async def down(*a, **k):
        raise ConnectionError("ollama down")

    monkeypatch.setattr(llm, "_chat_completion_async", down)
    monkeypatch.delenv("AIFORGE_DISABLE_LLM_CACHE", raising=False)
    llm.llm_cache.clear()
    global_trace.reset()
    out = asyncio.run(llm.generate_text_async("sys", "unique prompt for fallback test", task="backend"))
    assert "FastAPI" in out  # canned fallback
    assert global_trace.events()[-1]["fallback"] is True
    assert len(llm.llm_cache._cache) == 0
    # A second call must try the model again instead of serving cached canned output.
    asyncio.run(llm.generate_text_async("sys", "unique prompt for fallback test", task="backend"))
    assert global_trace.events()[-1]["cache_hit"] is False


def test_rag_can_be_disabled(monkeypatch):
    from backend.rag.pipeline import global_rag_pipeline
    monkeypatch.setenv("AIFORGE_RAG", "off")
    assert global_rag_pipeline.get_context_string_for_agent("backend", "anything") == ""


# --------------------------------------------------------------------------- #
# Harness
# --------------------------------------------------------------------------- #

async def _fake_pipeline(prompt, project_name, max_iterations, export_zip, output_dir):
    """Pretends to be the pipeline: emits LLM telemetry and returns files."""
    record_llm_call(agent="backend", model="fake", prompt=prompt, output="x", latency_ms=5,
                    prompt_tokens=100, completion_tokens=50)
    files = {"backend/main.py": GOOD_MAIN, "tests/test_api.py": GOOD_TESTS}
    pre = {"backend/main.py": "def broken(:\n", "tests/test_api.py": GOOD_TESTS}
    return {"success": True, "status": "PASS",
            "final_state": {"files": files, "pre_repair_files": pre, "iteration": 1,
                            "fixes": [{"diagnosis": "syntax"}], "review": {"score": 90, "issues": []}}}


async def _fallback_pipeline(**kwargs):
    record_llm_call(agent="backend", model="fake", prompt="p", output="x", latency_ms=1, fallback=True)
    return {"success": True, "status": "PASS", "final_state": {"files": {"backend/main.py": GOOD_MAIN}}}


def test_harness_run_with_fake_pipeline(tmp_path, monkeypatch):
    monkeypatch.setenv("AIFORGE_SANDBOX", "local")
    res = asyncio.run(harness.run_benchmark(task_ids=["todo-basic", "notes-sqlite"], label="unit",
                                            runs_dir=tmp_path, pipeline=_fake_pipeline))
    s = res["summary"]
    assert s["tasks_valid"] == 2
    assert s["build_success_rate"] == 1.0
    assert s["first_attempt_build_success_rate"] == 0.0     # pre-repair snapshot had a syntax error
    assert s["repair"]["build_fixed_by_repair"] == 2
    assert s["tokens_per_task_median"] == 150 and s["tokens_estimated"] is False
    assert s["tests_passed"] == 4 and s["tests_ran"] == 6
    run_dir = next(tmp_path.iterdir())
    assert (run_dir / "results.json").exists()
    report = (run_dir / "REPORT.md").read_text()
    assert "Build success" in report and "`todo-basic`" in report
    assert "| Metric | unit |" in compare([str(run_dir / "results.json")])


def test_harness_marks_fallback_runs_invalid(tmp_path, monkeypatch):
    monkeypatch.setenv("AIFORGE_SANDBOX", "local")
    res = asyncio.run(harness.run_benchmark(task_ids=["todo-basic"], runs_dir=tmp_path, pipeline=_fallback_pipeline))
    task = res["tasks"][0]
    assert task["valid"] is False and "fell back" in task["invalid_reason"]
    assert res["summary"]["tasks_valid"] == 0 and res["summary"]["build_success_rate"] is None


def test_harness_restores_environment(monkeypatch):
    monkeypatch.delenv("AIFORGE_RAG", raising=False)
    with harness.configured_env("m:1", "off", "on", None):
        import os
        assert os.environ["AIFORGE_RAG"] == "off" and os.environ["AIFORGE_CODING_MODEL"] == "m:1"
    import os
    assert "AIFORGE_RAG" not in os.environ


def test_harness_cli_list(capsys):
    assert harness.main(["list"]) == 0
    assert "todo-basic" in capsys.readouterr().out


# --------------------------------------------------------------------------- #
# Real pipeline, scripted LLM: generate -> run -> fail -> LLM repair -> pass
# --------------------------------------------------------------------------- #

def test_pipeline_end_to_end_repairs_planted_bug(tmp_path, monkeypatch):
    import backend.services.llm as llm
    fake = _load_fake_llm()
    calls = fake.install_on(monkeypatch, llm)
    monkeypatch.setenv("AIFORGE_SANDBOX", "local")
    monkeypatch.chdir(tmp_path)  # deployment step writes ./generated_projects

    res = asyncio.run(harness.run_benchmark(task_ids=["todo-basic"], label="e2e", runs_dir=tmp_path / "runs"))
    task = res["tasks"][0]

    assert task["valid"], task.get("invalid_reason")
    assert task["telemetry"]["prompt_tokens"] > 0 and not task["telemetry"]["tokens_estimated"]
    # The planner must receive the actual task prompt (it used to get "").
    planner_prompt = next(c for c in calls if "Chief Software Architect of AIForge — a Senior" in c[0])[1]
    assert "todo list REST API" in planner_prompt
    # Generated tests catch the planted bug before repair; LLM repair fixes it.
    assert task["initial"]["build_success"] and task["initial"]["tests_passed"] == 2
    assert task["final"]["tests_passed"] == 3 and task["final"]["test_pass_rate"] == 1.0
    assert task["final"]["route_coverage"] == 1.0
    assert task["pipeline"]["repair_attempts"] >= 1 and task["pipeline"]["self_reported_success"]
    assert task["pipeline"]["review"]["major"] == 1
    assert any("fixing a FastAPI project" in c[0] for c in calls)


def test_reviewer_eval_scoring():
    case = reviewer_eval.CASES[0]
    hit = reviewer_eval.score_case(case, {"issues": [{"severity": "critical", "problem": "SQL injection via f-string"}]})
    miss = reviewer_eval.score_case(case, {"issues": [{"severity": "minor", "problem": "naming"}]})
    clean = next(c for c in reviewer_eval.CASES if c.bug is None)
    alarm = reviewer_eval.score_case(clean, {"issues": [{"severity": "major", "problem": "x"}]})
    assert hit["detected"] and not miss["detected"] and alarm["false_alarm"]
    s = reviewer_eval.summarize([hit, miss, alarm])
    assert s["recall"] == 0.5 and s["false_alarm_rate"] == 1.0


def test_reviewer_eval_runs_with_scripted_reviewer(tmp_path):
    async def reviewer(code):
        found = "injection" if "f\"SELECT" in code else "none"
        return json.dumps({"status": "FAIL", "score": 50, "summary": "",
                           "issues": [{"severity": "critical", "problem": found, "fix": ""}] if found != "none" else []})

    res = asyncio.run(reviewer_eval.run_reviewer_eval(review_fn=reviewer, out_dir=tmp_path))
    assert res["summary"]["detected"] == 1 and res["summary"]["false_alarms"] == 0
    assert (tmp_path / "reviewer_eval.json").exists()
