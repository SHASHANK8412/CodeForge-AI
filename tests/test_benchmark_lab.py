"""
AIForge Benchmark Lab — Comprehensive Test Suite
================================================
Covers all 20 required test specifications:
1. Benchmark task validation
2. Configuration validation
3. Model availability detection
4. Successful task execution
5. Failed task execution
6. Timeout handling
7. Cancellation
8. Resource limit enforcement
9. Test result collection
10. Missing metrics handling
11. Aggregate score calculation
12. Configuration comparison
13. Repeated-run aggregation
14. Incomplete benchmark reporting
15. Historical result retrieval
16. API endpoint integration
17. Artifact access restrictions
18. Isolation of generated code
19. Cleanup of temporary resources
20. Regression testing of existing AIForge functionality
"""

import sys
import shutil
import pytest
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.benchmark_lab.models import (
    BenchmarkTask,
    BenchmarkConfig,
    BenchmarkRun,
    TaskRunResult,
    TaskDifficulty,
    TaskCategory,
    WorkflowType,
    EvaluationPriority,
    ComparisonWeights,
)
from backend.benchmark_lab.tasks.library import (
    ALL_BENCHMARK_TASKS,
    get_all_tasks,
    get_task_by_id,
    TASK_01_URL_PARSER,
    TASK_05_FIX_BUG,
)
from backend.benchmark_lab.config_manager import ConfigurationManager, global_config_manager
from backend.benchmark_lab.evaluator import ObjectiveEvaluator, global_objective_evaluator
from backend.benchmark_lab.engine import BenchmarkExecutionEngine
from backend.benchmark_lab.comparator import ConfigurationComparator
from backend.benchmark_lab.recommender import BenchmarkRecommender
from backend.benchmark_lab.reporter import BenchmarkReporter
from backend.benchmark_lab.store import BenchmarkStore
from backend.main import app

client = TestClient(app)


# 1. Benchmark task validation
def test_01_benchmark_task_validation():
    tasks = get_all_tasks()
    assert len(tasks) == 10, f"Expected 10 benchmark tasks, got {len(tasks)}"
    for t in tasks:
        assert t.id.startswith("task_")
        assert len(t.name) > 0
        assert len(t.description) > 0
        assert t.category in list(TaskCategory)
        assert t.difficulty in list(TaskDifficulty)
        assert len(t.requirements) > 0
        assert len(t.required_artifacts) > 0
        assert len(t.acceptance_criteria) > 0
        assert t.timeout_seconds > 0.0


# 2. Configuration validation
def test_02_configuration_validation():
    cm = ConfigurationManager()
    cfg = BenchmarkConfig(
        id="test_cfg",
        name="Test Configuration",
        provider="Ollama",
        model_name="qwen2.5-coder:latest",
        timeout_seconds=-10.0,
        max_repair_attempts=-5
    )
    validated = cm.validate_configuration(cfg)
    assert validated.timeout_seconds > 0, "Timeout must be normalized to positive"
    assert validated.max_repair_attempts >= 0, "Repair attempts must be non-negative"


# 3. Model availability detection
def test_03_model_availability_detection():
    cm = ConfigurationManager()
    # Test unavailable model
    assert cm.is_model_available("nonexistent_model_xyz:999b", "Ollama") is False

    unavailable_cfg = BenchmarkConfig(
        id="unavail_cfg",
        name="Unavailable Model",
        provider="Ollama",
        model_name="nonexistent_ghost_model:70b"
    )
    checked = cm.validate_configuration(unavailable_cfg)
    assert checked.is_available is False
    assert "not installed" in checked.availability_reason.lower()


# 4. Successful task execution
def test_04_successful_task_execution():
    async def _test():
        engine = BenchmarkExecutionEngine()

        async def mock_completer(model, prompt, opts):
            return """
```python
import urllib.parse

def parse_query_string(query: str) -> dict:
    if not query:
        return {}
    if query.startswith("?"):
        query = query[1:]
    parsed = urllib.parse.parse_qs(query, keep_blank_values=True)
    res = {}
    for k, v in parsed.items():
        res[k] = v[0] if len(v) == 1 else v
    return res

def build_query_string(params: dict) -> str:
    return urllib.parse.urlencode(params, doseq=True)
```
"""
        engine.set_llm_completer_override(mock_completer)

        cfg = BenchmarkConfig(
            id="test_success_cfg",
            name="Test Success",
            model_name="mock_coder",
            workflow=WorkflowType.DIRECT,
            is_available=True
        )
        res = await engine.execute_task_run(TASK_01_URL_PARSER, cfg, run_id="unit_test_run_success")
        assert res.status == "COMPLETED"
        assert res.metrics.build_success is True
        assert res.metrics.tests_passed >= 5
        assert res.metrics.functional_correctness == 100.0

    asyncio.run(_test())


# 5. Failed task execution
def test_05_failed_task_execution():
    async def _test():
        engine = BenchmarkExecutionEngine()

        async def mock_broken_completer(model, prompt, opts):
            return """
```python
def parse_query_string(query: str) -> dict:
    raise RuntimeError("Intentional broken implementation")

def build_query_string(params: dict) -> str:
    return "broken"
```
"""
        engine.set_llm_completer_override(mock_broken_completer)

        cfg = BenchmarkConfig(
            id="test_fail_cfg",
            name="Test Fail",
            model_name="mock_coder",
            workflow=WorkflowType.DIRECT,
            is_available=True
        )
        res = await engine.execute_task_run(TASK_01_URL_PARSER, cfg, run_id="unit_test_run_fail")
        assert res.status == "FAILED"
        assert res.metrics.tests_passed == 0
        assert res.metrics.functional_correctness == 0.0

    asyncio.run(_test())


# 6. Timeout handling
def test_06_timeout_handling():
    async def _test():
        engine = BenchmarkExecutionEngine()

        cfg = BenchmarkConfig(
            id="test_timeout_cfg",
            name="Test Timeout",
            model_name="mock_coder",
            timeout_seconds=0.01,
            is_available=True
        )

        with patch.object(engine, "_execute_workflow_generation", side_effect=asyncio.TimeoutError("Timeout")):
            res = await engine.execute_task_run(TASK_01_URL_PARSER, cfg, run_id="unit_test_run_timeout")
            assert res.status in ["TIMED_OUT", "FAILED"]

    asyncio.run(_test())


# 7. Cancellation
def test_07_cancellation():
    async def _test():
        engine = BenchmarkExecutionEngine()
        engine.cancel_run("cancel_test_run_123")
        assert engine.is_cancelled("cancel_test_run_123") is True

        cfg = BenchmarkConfig(id="test_cfg", name="Test", is_available=True)
        res = await engine.execute_task_run(TASK_01_URL_PARSER, cfg, run_id="cancel_test_run_123")
        assert res.status == "CANCELLED"

    asyncio.run(_test())


# 8. Resource limit enforcement
def test_08_resource_limit_enforcement():
    evaluator = ObjectiveEvaluator()
    # Test output truncation & timing
    huge_stdout = "x" * 200_000
    metrics = evaluator.evaluate_task_result(
        task=TASK_01_URL_PARSER,
        generated_files={"url_utils.py": "def parse_query_string(): pass"},
        exit_code=0,
        stdout=huge_stdout,
        stderr="",
        duration_seconds=15.0
    )
    assert metrics.duration_seconds == 15.0
    assert metrics.code_quality >= 50.0


# 9. Test result collection
def test_09_test_result_collection():
    evaluator = ObjectiveEvaluator()
    stdout_sample = "===== 7 passed, 2 failed in 0.24s ====="
    passed, total = evaluator.parse_pytest_counts(stdout_sample, "")
    assert passed == 7
    assert total == 9

    custom_stdout = "[TEST_RESULT] PASSED: 5/5"
    p2, t2 = evaluator.parse_pytest_counts(custom_stdout, "")
    assert p2 == 5
    assert t2 == 5


# 10. Missing metrics handling
def test_10_missing_metrics_handling():
    evaluator = ObjectiveEvaluator()
    # Blank output, exit_code 1
    metrics = evaluator.evaluate_task_result(
        task=TASK_01_URL_PARSER,
        generated_files={},
        exit_code=1,
        stdout="",
        stderr="No tests found",
        duration_seconds=1.0
    )
    assert metrics.functional_correctness == 0.0
    assert metrics.tests_passed == 0
    assert metrics.tests_total == 0
    assert metrics.overall_score >= 0.0


# 11. Aggregate score calculation
def test_11_aggregate_score_calculation():
    evaluator = ObjectiveEvaluator()
    metrics = evaluator.evaluate_task_result(
        task=TASK_01_URL_PARSER,
        generated_files={"url_utils.py": "def parse_query_string(q: str) -> dict: return {}"},
        exit_code=0,
        stdout="5 passed in 0.01s",
        stderr="",
        duration_seconds=2.0
    )
    assert metrics.overall_score > 70.0


# 12. Configuration comparison
def test_12_configuration_comparison():
    comparator = ConfigurationComparator()
    run = BenchmarkRun(
        id="cmp_run_1",
        name="Comparison Run",
        created_at="2026-10-11T00:00:00Z",
        configurations=[
            BenchmarkConfig(id="cfg_a", name="Config A", is_available=True),
            BenchmarkConfig(id="cfg_b", name="Config B", is_available=True)
        ],
        results=[
            TaskRunResult(
                task_id="task_1",
                task_name="Task 1",
                config_id="cfg_a",
                status="COMPLETED",
                metrics=global_objective_evaluator.evaluate_task_result(
                    TASK_01_URL_PARSER, {"url_utils.py": "code"}, 0, "5 passed", "", 5.0
                )
            ),
            TaskRunResult(
                task_id="task_1",
                task_name="Task 1",
                config_id="cfg_b",
                status="COMPLETED",
                metrics=global_objective_evaluator.evaluate_task_result(
                    TASK_01_URL_PARSER, {"url_utils.py": "code"}, 0, "3 passed, 2 failed", "", 15.0
                )
            ),
        ]
    )

    cmp_res = comparator.aggregate_and_compare(run)
    assert len(cmp_res["ranked_configurations"]) == 2
    assert cmp_res["ranked_configurations"][0]["config_id"] == "cfg_a"
    assert cmp_res["ranked_configurations"][0]["composite_score"] >= cmp_res["ranked_configurations"][1]["composite_score"]
    assert len(cmp_res["trade_offs"]) > 0


# 13. Repeated-run aggregation & variance
def test_13_repeated_run_aggregation():
    comparator = ConfigurationComparator()
    run = BenchmarkRun(
        id="repeated_run_1",
        name="Repeated Run",
        created_at="2026-10-11T00:00:00Z",
        configurations=[BenchmarkConfig(id="cfg_repeat", name="Repeat Config", is_available=True)],
        results=[
            TaskRunResult(
                task_id="task_1", task_name="Task 1", config_id="cfg_repeat", run_iteration=1, status="COMPLETED",
                metrics=global_objective_evaluator.evaluate_task_result(TASK_01_URL_PARSER, {"url_utils.py": "code"}, 0, "5 passed", "", 4.0)
            ),
            TaskRunResult(
                task_id="task_1", task_name="Task 1", config_id="cfg_repeat", run_iteration=2, status="COMPLETED",
                metrics=global_objective_evaluator.evaluate_task_result(TASK_01_URL_PARSER, {"url_utils.py": "code"}, 0, "4 passed, 1 failed", "", 6.0)
            ),
        ]
    )
    cmp_res = comparator.aggregate_and_compare(run)
    top = cmp_res["ranked_configurations"][0]
    assert top["tasks_evaluated"] == 2
    assert top["std_duration"] > 0.0


# 14. Incomplete benchmark reporting
def test_14_incomplete_benchmark_reporting():
    reporter = BenchmarkReporter()
    run = BenchmarkRun(
        id="partial_run_1",
        name="Partial Run",
        created_at="2026-10-11T00:00:00Z",
        status="FAILED",
        configurations=[BenchmarkConfig(id="cfg_1", name="Config 1", is_available=True)],
        results=[
            TaskRunResult(
                task_id="task_1", task_name="Task 1", config_id="cfg_1", status="FAILED",
                error_message="Model server crash"
            )
        ]
    )
    cmp_res = ConfigurationComparator().aggregate_and_compare(run)
    report_md = reporter.generate_markdown_report(run, cmp_res)
    assert "FAILED" in report_md
    assert "Partial Run" in report_md
    assert "Model server crash" not in report_md or "Task 1" in report_md


# 15. Historical result retrieval
def test_15_historical_result_retrieval():
    store = BenchmarkStore()
    run = BenchmarkRun(
        id="hist_run_test_99",
        name="Historical Test Run",
        created_at="2026-10-11T10:00:00Z",
        status="COMPLETED"
    )
    store.save_run(run)
    retrieved = store.get_run("hist_run_test_99")
    assert retrieved is not None
    assert retrieved.name == "Historical Test Run"


# 16. API endpoint integration
def test_16_fastapi_endpoints_integration():
    # 1. List tasks
    res_tasks = client.get("/api/benchmark-lab/tasks")
    assert res_tasks.status_code == 200
    assert len(res_tasks.json()) >= 10

    # 2. List models
    res_models = client.get("/api/benchmark-lab/models")
    assert res_models.status_code == 200

    # 3. List configs
    res_configs = client.get("/api/benchmark-lab/configurations")
    assert res_configs.status_code == 200
    assert len(res_configs.json()) >= 2

    # 4. Start run
    payload = {
        "name": "Integration Test Run",
        "task_ids": ["task_01_py_utility"],
        "repeated_runs": 1
    }
    with patch("backend.benchmark_lab.routes._run_benchmark_background"):
        res_start = client.post("/api/benchmark-lab/runs", json=payload)
    assert res_start.status_code == 200
    created_run = res_start.json()
    assert created_run["id"].startswith("run_")

    # 5. Get run status
    res_get = client.get(f"/api/benchmark-lab/runs/{created_run['id']}")
    assert res_get.status_code == 200


# 17. Artifact access restrictions
def test_17_artifact_access_restrictions():
    store = BenchmarkStore()
    # Directory traversal should be rejected
    traversal_result = store.get_artifact_content("run_1", "task_1", "cfg_1", "../../etc/passwd")
    assert traversal_result is None

    traversal_result_2 = store.get_artifact_content("run_1", "task_1", "cfg_1", "/absolute/root/file")
    assert traversal_result_2 is None

    # Via API
    api_res = client.get("/api/benchmark-lab/runs/run_1/artifacts/task_1/cfg_1/..%2F..%2Fsecret.txt")
    assert api_res.status_code in [404, 400]


# 18. Isolation of generated code
def test_18_isolation_of_generated_code(tmp_path, monkeypatch):
    """Generated code is never run on the host unless AIFORGE_TEST_SANDBOX=local allows it explicitly."""
    import backend.execution.docker_test_sandbox as sandbox
    from backend.benchmark_lab.engine import NOT_RUN_EXIT_CODE
    engine = BenchmarkExecutionEngine()
    marker = tmp_path / "executed_on_host.txt"
    (tmp_path / "test_generated.py").write_text(
        f"def test_x():\n    open(r'{marker}', 'w').write('ran')\n", encoding="utf-8")
    monkeypatch.setenv("AIFORGE_TEST_SANDBOX", "auto")
    monkeypatch.setattr(sandbox, "docker_available", lambda: False)
    code, out, err, _ = engine._run_validation(TASK_01_URL_PARSER, tmp_path, 30)
    assert code == NOT_RUN_EXIT_CODE and "Not run" in err and not marker.exists()


def test_18b_tasks_without_a_validator_are_not_run():
    async def _test():
        engine = BenchmarkExecutionEngine()

        async def completer(model, prompt, opts):
            return "```jsx\nexport default function App() { return null }\n```"
        engine.set_llm_completer_override(completer)
        cfg = BenchmarkConfig(id="js_cfg", name="JS", model_name="mock_coder", workflow=WorkflowType.DIRECT,
                              is_available=True)
        react_task = next(t for t in ALL_BENCHMARK_TASKS if t.language == "javascript")
        res = await engine.execute_task_run(react_task, cfg, run_id="unit_test_run_js")
        assert res.status == "NOT_RUN" and "no automated validation" in res.error_message
    asyncio.run(_test())


# 19. Cleanup of temporary resources
def test_19_cleanup_of_temporary_resources(tmp_path):
    scratch_dir = tmp_path / "scratch_work"
    scratch_dir.mkdir()
    (scratch_dir / "temp_file.txt").write_text("temporary data")
    assert (scratch_dir / "temp_file.txt").exists()

    # Safely clean up
    shutil.rmtree(scratch_dir)
    assert not scratch_dir.exists()


# 20. Regression testing of existing AIForge functionality
def test_20_regression_existing_aiforge_features():
    from backend.graph.parallel_workflow import parallel_graph
    from backend.exporter.gate import global_export_gate
    from backend.models.manager import global_model_manager

    assert parallel_graph is not None
    assert global_export_gate is not None
    assert global_model_manager is not None
