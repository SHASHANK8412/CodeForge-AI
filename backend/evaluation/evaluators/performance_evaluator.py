"""
AIForge Quality Recovery Day 14 — Performance Benchmark Evaluator
===================================================================
Automated evaluator for Day 14 performance engineering, path routing,
caching, resilience, recovery, and telemetry metrics.
"""

import json
import time
import logging
from typing import Dict, Any, List

from backend.performance.policy_engine import global_execution_policy_engine
from backend.performance.cache_manager import global_cache_manager, SingleFlight, LRUCache
from backend.performance.resilience import global_retry_policy, global_circuit_breaker_registry, global_fallback_policy, CircuitState
from backend.performance.tracer import global_request_tracer
from backend.performance.scheduler import global_task_scheduler, TaskNode
from backend.performance.health import global_health_service
from backend.performance.metrics import global_metrics_service
from backend.performance.checkpoint import global_workflow_checkpoint_manager
from backend.performance.audit import global_audit_logger
from backend.performance.profiler import global_performance_profiler

logger = logging.getLogger("aiforge.evaluation.performance_evaluator")


class PerformanceEvaluator:
    """Evaluator for running Day 14 performance and reliability benchmarks."""

    def evaluate_dataset(self, dataset_path: str) -> Dict[str, Any]:
        """Evaluates all test scenarios in day14_performance_dataset.json."""
        with open(dataset_path, "r", encoding="utf-8") as f:
            cases = json.load(f)

        passed = 0
        failed = 0
        details = []

        for case in cases:
            cid = case["id"]
            cname = case["name"]
            category = case["category"]
            c_pass = True
            msg = "PASS"

            try:
                # 1. Policy & Path Routing Tests
                if category in ("FAST_PATH", "RETRIEVAL_PATH", "REPOSITORY_PATH", "ENGINEERING_PATH", "POLICY"):
                    prompt = case["query"]
                    plan = global_execution_policy_engine.analyze(
                        prompt=prompt,
                        has_documents=case.get("has_documents", False),
                        has_active_repo=case.get("has_active_repo", False)
                    )

                    if "expected_path" in case and plan.path.value != case["expected_path"]:
                        c_pass = False
                        msg = f"Expected path '{case['expected_path']}', got '{plan.path.value}'"
                    elif "expected_rag" in case and plan.use_rag != case["expected_rag"]:
                        c_pass = False
                        msg = f"Expected use_rag={case['expected_rag']}, got {plan.use_rag}"
                    elif "expected_git" in case and plan.use_git != case["expected_git"]:
                        c_pass = False
                        msg = f"Expected use_git={case['expected_git']}, got {plan.use_git}"

                # 2. Caching Tests
                elif category == "CACHING":
                    if case.get("test_cache_repeat"):
                        k = global_cache_manager.build_key(case["query"], namespace="classification")
                        global_cache_manager.put("classification", k, "EXPLANATION")
                        val = global_cache_manager.get("classification", k)
                        if val != "EXPLANATION":
                            c_pass = False
                            msg = "Cache repeat lookup failed"
                    elif case.get("test_lru_eviction"):
                        lru = LRUCache(maxsize=3)
                        lru.put("k1", 1)
                        lru.put("k2", 2)
                        lru.put("k3", 3)
                        lru.put("k4", 4)
                        if lru.get("k1") is not None:
                            c_pass = False
                            msg = "LRU eviction failed to purge oldest item"
                    elif case.get("test_ttl_expiry"):
                        lru = LRUCache(maxsize=10, default_ttl=0.01)
                        lru.put("kt", 100)
                        time.sleep(0.02)
                        if lru.get("kt") is not None:
                            c_pass = False
                            msg = "TTL expiration failed"
                    elif case.get("test_single_flight"):
                        sf = SingleFlight()
                        c_count = 0

                        def _slow_work():
                            nonlocal c_count
                            c_count += 1
                            time.sleep(0.05)
                            return 42

                        r1 = sf.execute("sf_key", _slow_work)
                        if r1 != 42 or c_count != 1:
                            c_pass = False
                            msg = "Single flight failed to execute once"

                # 3. Concurrency Tests
                elif category == "CONCURRENCY":
                    if case.get("test_dag_execution"):
                        t1 = TaskNode("t1", lambda: 10, resource_class="CPU")
                        t2 = TaskNode("t2", lambda: 20, dependencies=["t1"], resource_class="CPU")
                        res = global_task_scheduler.run_dag([t1, t2])
                        if res.get("t1") != 10 or res.get("t2") != 20:
                            c_pass = False
                            msg = "DAG execution order failed"
                    elif case.get("test_cancellation"):
                        global_task_scheduler.cancel_request("req_cancel_test")
                        if not global_task_scheduler._cancel_flags.get("req_cancel_test"):
                            c_pass = False
                            msg = "Request cancellation flag failed"

                # 4. Resilience Tests
                elif category == "RESILIENCE":
                    if case.get("test_transient_retry"):
                        attempts = 0

                        def _flaky():
                            nonlocal attempts
                            attempts += 1
                            if attempts < 2:
                                raise TimeoutError("Temporary timeout")
                            return "SUCCESS"

                        res = global_retry_policy.execute_with_retry(_flaky, max_retries=3, stage_name="TEST_FLAKY")
                        if res != "SUCCESS" or attempts != 2:
                            c_pass = False
                            msg = "Transient retry failed"
                    elif case.get("test_non_retryable"):
                        try:
                            global_retry_policy.execute_with_retry(lambda: (_ for _ in ()).throw(ValueError("Invalid syntax")), max_retries=3)
                            c_pass = False
                            msg = "Non-retryable error was incorrectly retried"
                        except ValueError:
                            c_pass = True
                    elif case.get("test_circuit_transitions"):
                        cb = global_circuit_breaker_registry.get("test_circuit")
                        for _ in range(3):
                            cb.record_failure()
                        if cb.state != CircuitState.OPEN:
                            c_pass = False
                            msg = "Circuit breaker failed to trip to OPEN"

                # 5. Recovery Tests
                elif category == "RECOVERY":
                    if case.get("test_save_checkpoint"):
                        cp = global_workflow_checkpoint_manager.save_checkpoint("wf_001", "PATCHED", {"files": ["main.py"]})
                        if cp.stage != "PATCHED":
                            c_pass = False
                            msg = "Checkpoint save failed"
                    elif case.get("test_resume_checkpoint"):
                        cp, valid = global_workflow_checkpoint_manager.validate_and_resume("wf_001", "")
                        if not valid or not cp or cp.stage != "PATCHED":
                            c_pass = False
                            msg = "Checkpoint resume failed"

                # 6. Observability Tests
                elif category == "OBSERVABILITY":
                    if case.get("test_correlation_ids"):
                        tr = global_request_tracer.start_trace(request_id="req_obs_100")
                        if tr.request_id != "req_obs_100":
                            c_pass = False
                            msg = "Trace correlation ID mapping failed"
                    elif case.get("test_secret_redaction"):
                        evt = global_audit_logger.log_event("req_obs_200", "COMMIT", "SUCCESS", metadata={"token": "ghp_12345678901234567890"})
                        if "ghp_12345678901234567890" in str(evt.metadata):
                            c_pass = False
                            msg = "Secret token was not redacted in audit event"
                    elif case.get("test_health_check"):
                        h = global_health_service.check_readiness()
                        if "status" not in h:
                            c_pass = False
                            msg = "Health service check failed"

            except Exception as ex:
                c_pass = False
                msg = f"Unhandled exception: {ex}"

            if c_pass:
                passed += 1
            else:
                failed += 1

            details.append({
                "id": cid,
                "name": cname,
                "category": category,
                "status": "PASS" if c_pass else "FAIL",
                "message": msg
            })

        total = len(cases)
        return {
            "total_evaluated": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": round(passed / total, 4) if total > 0 else 0.0,
            "details": details
        }


global_performance_evaluator = PerformanceEvaluator()
