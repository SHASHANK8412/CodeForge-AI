"""
Tests for the AIForge CLI (run_aiforge.py) and the benchmark runner.

The CLI drives a stand-in graph with the same contract as the real parallel_graph: it refuses to run without a
thread_id, streams node updates, pauses at the two human checkpoints and resumes after update_state().
"""

import asyncio
import json
import sys
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

import run_aiforge
from run_aiforge import main as cli_main, run_aiforge_pipeline
from benchmarks.definitions import BENCHMARK_SUITE
from benchmarks.run_benchmarks import run_benchmark_suite
from backend.services.llm import LLMUnavailableError


class FakeGraph:
    """planner, architect | human_approval | backend, testing | final_approval | packaging"""

    SEGMENTS = [["planner", "architect"], ["backend", "testing"], ["packaging"]]
    PAUSES = ["human_approval", "final_approval", None]

    def __init__(self, result=None, fail_with=None):
        self.result = result or {}
        self.fail_with = fail_with
        self.segment = 0
        self.values = {}
        self.updates = []

    async def astream(self, payload, config=None, stream_mode=None):
        assert config and config["configurable"].get("thread_id"), "the real graph needs a thread_id"
        if payload is not None:
            self.values = dict(payload)
        if self.fail_with:
            raise self.fail_with
        for node in self.SEGMENTS[self.segment]:
            if node == "testing":
                self.values.update(self.result)
            yield {node: {}}

    def get_state(self, config):
        pause = self.PAUSES[self.segment]
        return SimpleNamespace(values=self.values, next=(pause,) if pause else ())

    def update_state(self, config, update, as_node=None):
        self.updates.append((as_node, update))
        self.values.update(update)
        self.segment += 1


PASSING = {"files": {"backend/main.py": "def foo(): pass"}, "execution_results": {"exit_code": 0, "status": "PASS"},
           "test_results": {"success": True, "failed": 0, "passed": 2, "total": 2}}


@pytest.fixture
def tmp_output_dir(tmp_path):
    out_dir = tmp_path / "generated_projects"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


@pytest.fixture
def gate_allows():
    with patch("backend.exporter.gate.global_export_gate.validate_state") as v:
        v.return_value = SimpleNamespace(allowed=True, reason="", model_dump=lambda: {"allowed": True})
        yield v


def test_cli_argument_parsing():
    test_args = ["run_aiforge.py", "Build a Todo App", "--project-name", "CustomTodo", "--max-iterations", "5",
                 "--no-export", "--verbose", "--approve-architecture"]
    with patch.object(sys, "argv", test_args), patch("asyncio.run") as mock_async_run:
        mock_async_run.side_effect = lambda coro: (coro.close(), {"success": True})[1]
        with pytest.raises(SystemExit) as exc:
            cli_main()
        assert exc.value.code == 0 and mock_async_run.called


def test_cli_runs_every_stage_through_both_approvals_and_exports(tmp_output_dir, gate_allows):
    graph = FakeGraph(PASSING)
    res = asyncio.run(run_aiforge_pipeline("Build a simple Todo API", project_name="TodoAppTest",
                                           output_dir=str(tmp_output_dir), approve_architecture=True,
                                           approve_final=True, graph=graph))
    assert res["steps"] == ["planner", "architect", "backend", "testing", "packaging"]
    assert [node for node, _ in graph.updates] == ["human_approval", "final_approval"]
    assert res["success"] is True and Path(res["export_path"]).exists()
    with zipfile.ZipFile(res["export_path"]) as zf:
        assert zf.namelist()


def test_cli_never_approves_the_final_checkpoint_on_its_own(tmp_output_dir, gate_allows):
    graph = FakeGraph(PASSING)
    asked = []
    res = asyncio.run(run_aiforge_pipeline("Build app", project_name="NoDeploy", output_dir=str(tmp_output_dir),
                                           approve_architecture=True, ask=lambda q: asked.append(q) or False,
                                           graph=graph))
    assert asked == ["Approve the final checkpoint?"]
    assert "packaging" not in res["steps"] and len(graph.updates) == 1
    assert res["status"] == "AWAITING_FINAL_APPROVAL"
    assert res["success"] is True, "the project was generated and verified before the final checkpoint"


def test_cli_stops_when_the_architecture_is_not_approved(tmp_output_dir):
    graph = FakeGraph(PASSING)
    res = asyncio.run(run_aiforge_pipeline("Build app", project_name="Rejected", output_dir=str(tmp_output_dir),
                                           ask=lambda q: False, graph=graph))
    assert res["steps"] == ["planner", "architect"]
    assert res["status"] == "STOPPED_AT_ARCHITECTURE_APPROVAL" and res["success"] is False
    assert res["export_path"] is None


def test_cli_failed_generation_is_not_exported(tmp_output_dir):
    failing = {"execution_results": {"exit_code": 1, "status": "FAIL"}, "test_results": {"success": False, "failed": 2}}
    res = asyncio.run(run_aiforge_pipeline("Broken app", project_name="FailAppTest", output_dir=str(tmp_output_dir),
                                           approve_architecture=True, approve_final=True, graph=FakeGraph(failing)))
    assert res["success"] is False and res["export_path"] is None


@pytest.mark.parametrize("exc,category", [
    (LLMUnavailableError("planner", "qwen2.5", "connection refused"), "MODEL_UNAVAILABLE"),
    (asyncio.TimeoutError(), "TIMEOUT"),
    (RuntimeError("boom"), "ERROR (RuntimeError)"),
])
def test_cli_reports_the_real_failure_category(tmp_path, exc, category):
    res = asyncio.run(run_aiforge_pipeline("Build app", project_name="ErrApp", output_dir=str(tmp_path / "out"),
                                           graph=FakeGraph(fail_with=exc)))
    assert res["status"] == category and res["success"] is False and res["export_path"] is None


def test_cli_uses_the_real_graph_with_a_thread_id_by_default(tmp_path):
    """Regression: the CLI called parallel_graph.ainvoke() without a thread_id and crashed on the checkpointer."""
    seen = {}

    async def fake_astream(payload, config=None, stream_mode=None):
        seen["config"] = config
        return
        yield  # pragma: no cover - makes this an async generator

    with patch.object(run_aiforge.parallel_graph, "astream", side_effect=fake_astream), \
            patch.object(run_aiforge.parallel_graph, "get_state", return_value=SimpleNamespace(values={}, next=())):
        asyncio.run(run_aiforge_pipeline("Build app", project_name="Cfg", output_dir=str(tmp_path / "out")))
    assert seen["config"]["configurable"]["thread_id"].startswith("cli-")


def test_benchmark_definition_loading():
    assert len(BENCHMARK_SUITE) >= 5
    names = [b.name for b in BENCHMARK_SUITE]
    assert "TodoApp" in names
    assert "BlogAPI" in names
    assert "ExpenseTracker" in names
    assert "AuthDashboard" in names
    assert "ECommerce" in names


def test_benchmark_runner(tmp_path, gate_allows):
    """Runs the suite against the stand-in graph; the reports go to a temporary folder, never over the
    committed benchmark results."""
    out_dir = tmp_path / "generated_projects"
    report_dir = tmp_path / "reports"

    async def per_benchmark(*args, **kwargs):
        return await run_aiforge_pipeline(*args, graph=FakeGraph(PASSING), **kwargs)

    with patch("benchmarks.run_benchmarks.run_aiforge_pipeline", side_effect=per_benchmark):
        bench_res = asyncio.run(run_benchmark_suite(output_dir=str(out_dir), max_iterations=1,
                                                    report_dir=str(report_dir)))

    assert bench_res["summary"]["total_benchmarks"] == len(BENCHMARK_SUITE)
    assert bench_res["summary"]["e2e_success_rate"] == 1.0
    data = json.loads((report_dir / "results.json").read_text(encoding="utf-8"))
    assert data["summary"]["total_benchmarks"] == len(BENCHMARK_SUITE)
    assert "# AIForge E2E Autonomous Software Engineer Benchmark Report" in (report_dir / "REPORT.md").read_text(encoding="utf-8")


def test_metrics_calculation():
    sample_records = [
        {"e2e_success": True, "export_success": True, "self_healed": False, "debug_attempts": 0, "duration_seconds": 10.0, "iterations_used": 1},
        {"e2e_success": True, "export_success": True, "self_healed": True, "debug_attempts": 1, "duration_seconds": 20.0, "iterations_used": 2},
        {"e2e_success": False, "export_success": False, "self_healed": False, "debug_attempts": 2, "duration_seconds": 30.0, "iterations_used": 3}
    ]

    total = len(sample_records)
    passed = sum(1 for r in sample_records if r["e2e_success"])
    healed = sum(1 for r in sample_records if r["self_healed"])
    repairs = sum(r["debug_attempts"] for r in sample_records)

    e2e_rate = passed / total
    healing_rate = healed / repairs if repairs > 0 else 0.0

    assert e2e_rate == pytest.approx(0.6667, 0.01)
    assert healing_rate == pytest.approx(0.3333, 0.01)
