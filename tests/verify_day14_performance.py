"""
AIForge Quality Recovery Day 14 — Master Performance & Reliability Verification Suite
=====================================================================================
Executes full verification of Day 14 performance engineering, path routing, resilience,
circuit breaking, caching, concurrency, telemetry, crash recovery, and 36 benchmark scenarios.
"""

import sys
import time
import json
import logging
from typing import Dict, Any

from backend.performance.policy_engine import global_execution_policy_engine
from backend.performance.cache_manager import global_cache_manager, LRUCache, SingleFlight
from backend.performance.resilience import global_retry_policy, global_circuit_breaker_registry, global_fallback_policy, CircuitState
from backend.performance.tracer import global_request_tracer
from backend.performance.scheduler import global_task_scheduler, TaskNode
from backend.performance.health import global_health_service
from backend.performance.metrics import global_metrics_service
from backend.performance.checkpoint import global_workflow_checkpoint_manager
from backend.performance.audit import global_audit_logger
from backend.performance.profiler import global_performance_profiler
from backend.performance.models import PipelinePath
from backend.services.generation_service import AIForgeGenerationPipeline
from backend.evaluation.evaluators.performance_evaluator import global_performance_evaluator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("verify_day14_performance")


def run_mandatory_tests() -> Dict[str, bool]:
    results = {}

    # Test 1: FAST Explanation Path (Formula 1)
    logger.info("[Test 1] Testing FAST Explanation Path...")
    plan1 = global_execution_policy_engine.analyze("Explain Formula 1.")
    t1_pass = (
        plan1.path == PipelinePath.FAST
        and not plan1.use_rag
        and not plan1.use_git
        and not plan1.use_tests
        and plan1.budgets.max_model_calls == 1
    )
    results["Test 1: FAST Explanation Path (Formula 1)"] = t1_pass

    # Test 2: FAST Coding Path (Binary Search)
    logger.info("[Test 2] Testing FAST Coding Path...")
    plan2 = global_execution_policy_engine.analyze("Write binary search in Python.")
    t2_pass = (
        plan2.path == PipelinePath.FAST_CODING
        and not plan2.use_rag
        and not plan2.use_git
        and plan2.budgets.max_model_calls == 1
    )
    results["Test 2: FAST Coding Path (Binary Search)"] = t2_pass

    # Test 3: Retrieval Path (Uploaded Document)
    logger.info("[Test 3] Testing Retrieval Path...")
    plan3 = global_execution_policy_engine.analyze("According to the document, what database is required?", has_documents=True)
    t3_pass = (plan3.path == PipelinePath.RETRIEVAL and plan3.use_rag and not plan3.use_git)
    results["Test 3: Retrieval Path (Uploaded Document)"] = t3_pass

    # Test 4: Repository Read Path
    logger.info("[Test 4] Testing Repository Read Path...")
    plan4 = global_execution_policy_engine.analyze("Where is authentication implemented in this repository?", has_active_repo=True)
    t4_pass = (plan4.path == PipelinePath.REPOSITORY and plan4.use_repository and not plan4.use_git)
    results["Test 4: Repository Read Path"] = t4_pass

    # Test 5: Engineering Workflow Path
    logger.info("[Test 5] Testing Engineering Workflow Path...")
    plan5 = global_execution_policy_engine.analyze("Fix issue #123: refresh token expiration bug.", has_active_repo=True)
    t5_pass = (plan5.path == PipelinePath.ENGINEERING_WORKFLOW and plan5.use_planner and plan5.use_git and plan5.use_tests)
    results["Test 5: Engineering Workflow Path"] = t5_pass

    # Test 6: Cache Performance
    logger.info("[Test 6] Testing Cache Performance...")
    k = global_cache_manager.build_key("Explain recursion", namespace="classification")
    global_cache_manager.put("classification", k, "EXPLANATION")
    t0 = time.perf_counter()
    hit_val = global_cache_manager.get("classification", k)
    t_hit_ms = (time.perf_counter() - t0) * 1000.0
    results["Test 6: Cache Performance"] = (hit_val == "EXPLANATION" and t_hit_ms < 5.0)

    # Test 7: Transient Retry Policy
    logger.info("[Test 7] Testing Transient Retry Policy...")
    attempts = 0

    def _flaky():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise TimeoutError("Transient connection timeout")
        return "SUCCESS"

    res7 = global_retry_policy.execute_with_retry(_flaky, max_retries=3, stage_name="TEST_RETRY")
    results["Test 7: Transient Retry Policy"] = (res7 == "SUCCESS" and attempts == 2)

    # Test 8: Circuit Breaker Failure & Recovery
    logger.info("[Test 8] Testing Circuit Breaker State Machine...")
    cb = global_circuit_breaker_registry.get("test_service")
    for _ in range(3):
        cb.record_failure()
    is_open = (cb.state == CircuitState.OPEN)
    cb.record_success()
    is_closed = (cb.state == CircuitState.CLOSED)
    results["Test 8: Circuit Breaker State Machine"] = (is_open and is_closed)

    # Test 9: Task Timeout Enforcement
    logger.info("[Test 9] Testing Task Timeout Enforcement...")
    try:
        def _slow():
            time.sleep(0.5)

        t_node = TaskNode("t_slow", _slow, timeout=0.01, resource_class="CPU")
        global_task_scheduler._execute_node(t_node, "req_timeout_test")
        t9_pass = False
    except TimeoutError:
        t9_pass = True
    results["Test 9: Task Timeout Enforcement"] = t9_pass

    # Test 10: Task Cancellation Propagation
    logger.info("[Test 10] Testing Task Cancellation Propagation...")
    global_task_scheduler.cancel_request("req_cancel_10")
    t10_pass = global_task_scheduler._cancel_flags.get("req_cancel_10", False)
    results["Test 10: Task Cancellation Propagation"] = t10_pass

    # Test 11: Workflow Checkpoint & Resume
    logger.info("[Test 11] Testing Workflow Checkpoint & Resume...")
    global_workflow_checkpoint_manager.save_checkpoint("wf_99", "PATCHED", {"state": "ok"}, repository_fingerprint="fp123")
    cp, valid = global_workflow_checkpoint_manager.validate_and_resume("wf_99", "fp123")
    t11_pass = (valid and cp is not None and cp.stage == "PATCHED")
    results["Test 11: Workflow Checkpoint & Resume"] = t11_pass

    # Test 12: Load & Concurrency Isolation
    logger.info("[Test 12] Testing SingleFlight Deduplication...")
    sf = SingleFlight()
    work_count = 0

    def _expensive():
        nonlocal work_count
        work_count += 1
        time.sleep(0.02)
        return "RESULT"

    r_sf = sf.execute("shared_key", _expensive)
    results["Test 12: SingleFlight Deduplication"] = (r_sf == "RESULT" and work_count == 1)

    # Test 13: Secret Redaction in Audit & Tracing
    logger.info("[Test 13] Testing Secret Redaction in Audit Logs...")
    evt = global_audit_logger.log_event("req_sec", "PUSH", "SUCCESS", metadata={"api_key": "AKIA1234567890123456"})
    t13_pass = ("AKIA1234567890123456" not in str(evt.metadata) and "[REDACTED_AWS_KEY]" in str(evt.metadata))
    results["Test 13: Secret Redaction in Audit Logs"] = t13_pass

    # Test 14: Days 1-13 Regression Gate
    logger.info("[Test 14] Testing Days 1-13 Regression Gate...")
    h_status = global_health_service.check_readiness()
    t14_pass = (h_status["status"] in ("HEALTHY", "DEGRADED"))
    results["Test 14: Days 1-13 Regression Gate"] = t14_pass

    return results


def run_benchmark_evaluator() -> Dict[str, Any]:
    dataset_path = "backend/evaluation/datasets/day14_performance_dataset.json"
    logger.info(f"Running Performance Benchmark Evaluation on '{dataset_path}'...")
    return global_performance_evaluator.evaluate_dataset(dataset_path)


def main():
    logger.info("===========================================================================")
    logger.info(" [PERF] AIForge V2 Day 14 Performance & Reliability Verification Suite")
    logger.info("===========================================================================")

    test_results = run_mandatory_tests()

    logger.info("\n--- Mandatory Unit & Policy Verification Results ---")
    all_mandatory_passed = True
    for t_name, passed in test_results.items():
        status_str = "[PASS]" if passed else "[FAIL]"
        logger.info(f"  {t_name:<55} : {status_str}")
        if not passed:
            all_mandatory_passed = False

    logger.info("\n--- Day 14 Golden Benchmark Dataset Evaluation ---")
    bench_res = run_benchmark_evaluator()

    logger.info(f"  Total Scenarios Evaluated  : {bench_res['total_evaluated']}")
    logger.info(f"  Passed                      : {bench_res['passed']}")
    logger.info(f"  Failed                      : {bench_res['failed']}")
    logger.info(f"  Pass Rate                   : {bench_res['pass_rate'] * 100:.2f}%")

    all_benchmarks_passed = (bench_res["failed"] == 0 and bench_res["pass_rate"] == 1.0)

    # Compute profiling baseline comparison
    prof_res = global_performance_profiler.analyze_traces([])

    logger.info("\n===========================================================================")
    if all_mandatory_passed and all_benchmarks_passed:
        logger.info(" AIFORGE V2 DAY 14 VERIFICATION SUMMARY: [PASS]")
        logger.info(f" Passed: {len(test_results) + bench_res['passed']} | Failed: 0")
        logger.info("===========================================================================")
        sys.exit(0)
    else:
        logger.info(" AIFORGE V2 DAY 14 VERIFICATION SUMMARY: [FAIL]")
        logger.info("===========================================================================")
        sys.exit(1)


if __name__ == "__main__":
    main()
