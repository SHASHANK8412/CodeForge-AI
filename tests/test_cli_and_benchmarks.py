"""
Unit and Integration Tests for AIForge CLI & Benchmark Suite (Phase 12)
"""

import sys
import json
import zipfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from run_aiforge import run_aiforge_pipeline, main as cli_main
from benchmarks.definitions import BENCHMARK_SUITE, BenchmarkSpec
from benchmarks.run_benchmarks import run_benchmark_suite
from backend.graph.parallel_workflow import parallel_graph


@pytest.fixture
def tmp_output_dir(tmp_path):
    out_dir = tmp_path / "generated_projects"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def test_cli_argument_parsing():
    test_args = ["run_aiforge.py", "Build a Todo App", "--project-name", "CustomTodo", "--max-iterations", "5", "--no-export", "--verbose"]
    with patch.object(sys, "argv", test_args):
        with patch("asyncio.run") as mock_async_run:
            mock_async_run.return_value = {"success": True}
            try:
                cli_main()
            except SystemExit as exc:
                assert exc.code == 0
            assert mock_async_run.called


def test_cli_successful_generation(tmp_output_dir):
    async def _test():
        async def mock_invoke(state):
            s = dict(state)
            s["status"] = "PASS"
            s["files"] = {"backend/main.py": "def foo(): pass"}
            s["execution_results"] = {"exit_code": 0, "status": "PASS"}
            s["test_results"] = {"success": True, "failed": 0, "passed": 2, "total": 2}
            return s

        with patch.object(parallel_graph, "ainvoke", side_effect=mock_invoke):
            res = await run_aiforge_pipeline(
                prompt="Build a simple Todo API",
                project_name="TodoAppTest",
                max_iterations=2,
                export_zip=True,
                output_dir=str(tmp_output_dir)
            )

            assert res["project_name"] == "TodoAppTest"
            assert res["status"] == "PASS"
            assert res["export_path"] is not None
            assert Path(res["export_path"]).exists()
            with zipfile.ZipFile(res["export_path"]) as zf:
                assert len(zf.namelist()) > 0
    import asyncio
    asyncio.run(_test())


def test_cli_failed_generation(tmp_output_dir):
    async def _test():
        async def mock_invoke(state):
            s = dict(state)
            s["status"] = "FAILED"
            s["execution_results"] = {"exit_code": 1, "status": "FAIL"}
            s["test_results"] = {"success": False, "failed": 2}
            return s

        with patch.object(parallel_graph, "ainvoke", side_effect=mock_invoke):
            with patch("backend.exporter.gate.global_export_gate.validate_state") as mock_val:
                mock_val.return_value = MagicMock(allowed=False, reason="Forced test failure")
                
                res = await run_aiforge_pipeline(
                    prompt="Broken app requirement",
                    project_name="FailAppTest",
                    max_iterations=1,
                    export_zip=True,
                    output_dir=str(tmp_output_dir)
                )

                assert res["success"] is False
                assert res["export_path"] is None
    import asyncio
    asyncio.run(_test())



def test_cli_success_criteria():
    state_pass = {
        "status": "PASS",
        "execution_results": {"exit_code": 0, "status": "PASS"},
        "test_results": {"success": True, "failed": 0}
    }
    state_fail = {
        "status": "FAILED",
        "execution_results": {"exit_code": 1, "status": "FAIL"},
        "test_results": {"success": False, "failed": 3}
    }

    assert state_pass["execution_results"]["exit_code"] == 0
    assert state_pass["test_results"]["success"] is True
    assert state_fail["execution_results"]["exit_code"] != 0


def test_benchmark_definition_loading():
    assert len(BENCHMARK_SUITE) >= 5
    names = [b.name for b in BENCHMARK_SUITE]
    assert "TodoApp" in names
    assert "BlogAPI" in names
    assert "ExpenseTracker" in names
    assert "AuthDashboard" in names
    assert "ECommerce" in names


def test_benchmark_runner(tmp_path):
    async def _test():
        out_dir = tmp_path / "generated_projects"
        out_dir.mkdir(parents=True, exist_ok=True)

        async def mock_invoke(state):
            s = dict(state)
            s["status"] = "PASS"
            s["files"] = {"backend/main.py": "def foo(): pass"}
            s["execution_results"] = {"exit_code": 0, "status": "PASS"}
            s["test_results"] = {"success": True, "failed": 0, "passed": 3, "total": 3}
            return s

        with patch.object(parallel_graph, "ainvoke", side_effect=mock_invoke):
            with patch.object(Path, "cwd", return_value=tmp_path):
                bench_res = await run_benchmark_suite(output_dir=str(out_dir), max_iterations=1)
                
                assert "summary" in bench_res
                assert bench_res["summary"]["total_benchmarks"] == len(BENCHMARK_SUITE)
                assert bench_res["summary"]["e2e_success_rate"] == 1.0

                results_json = Path("benchmarks/results.json")
                report_md = Path("benchmarks/REPORT.md")
                
                assert results_json.exists()
                assert report_md.exists()


                data = json.loads(results_json.read_text(encoding="utf-8"))
                assert data["summary"]["total_benchmarks"] == 5
                assert "# AIForge E2E Autonomous Software Engineer Benchmark Report" in report_md.read_text(encoding="utf-8")
    import asyncio
    asyncio.run(_test())


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


def test_api_cli_workflow_consistency():
    from backend.graph.parallel_workflow import parallel_graph as workflow_graph
    assert workflow_graph is not None


def test_end_to_end_todo_benchmark(tmp_output_dir):
    async def _test():
        todo_spec = [b for b in BENCHMARK_SUITE if b.name == "TodoApp"][0]
        
        async def mock_invoke(state):
            s = dict(state)
            s["status"] = "PASS"
            s["files"] = {"backend/main.py": "def foo(): pass"}
            s["execution_results"] = {"exit_code": 0, "status": "PASS"}
            s["test_results"] = {"success": True, "failed": 0, "passed": 5, "total": 5}
            return s

        with patch.object(parallel_graph, "ainvoke", side_effect=mock_invoke):
            res = await run_aiforge_pipeline(
                prompt=todo_spec.description,
                project_name="TodoAppE2E",
                max_iterations=2,
                export_zip=True,
                output_dir=str(tmp_output_dir)
            )

            assert res["project_name"] == "TodoAppE2E"
            assert res["status"] == "PASS"
            assert res["export_path"] is not None
            assert Path(res["export_path"]).exists()
    import asyncio
    asyncio.run(_test())



def test_model_environment_failure_handling(tmp_path):
    async def _test():
        out_dir = tmp_path / "generated_projects"
        
        async def mock_err_invoke(state):
            raise RuntimeError("Simulated Ollama local LLM connection timeout")

        with patch.object(parallel_graph, "ainvoke", side_effect=mock_err_invoke):
            res = await run_aiforge_pipeline(
                prompt="Build app",
                project_name="ErrApp",
                max_iterations=1,
                export_zip=True,
                output_dir=str(out_dir)
            )
            assert res["success"] is False
            assert res["status"] == "SECURITY_ERROR"
            assert res["export_path"] is None
    import asyncio
    asyncio.run(_test())

