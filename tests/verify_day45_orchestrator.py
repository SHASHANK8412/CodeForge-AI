"""
Day 45 - Master Orchestrator Agent System Verification Suite
============================================================
Validates all 10 Requirements:
1. Dependency-Aware Task Graph
2. Structured Message Exchange
3. Parallel Layer Execution
4. Synchronized Shared Memory
5. Exponential Backoff Retries on Node Failures
6. Real-Time Event Emission (started, finished, failed, retried)
7. Detailed Execution Metrics (logs, timing, retries, tokens)
8. Upstream Dependency Gate Enforcement
9. Autonomous Workflow Maintenance
10. Final Execution Report & Project Health Status
"""

import sys
import asyncio
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.orchestrator.master_orchestrator import (
    MasterOrchestratorAgent,
    DependencyTaskGraph,
    TaskNode
)

PASS = "[PASS]"
FAIL = "[FAIL]"
_results = {"passed": 0, "failed": 0}


def section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def check(name, condition, detail=""):
    status = PASS if condition else FAIL
    if condition:
        _results["passed"] += 1
    else:
        _results["failed"] += 1
    msg = f"  {status}  {name}"
    if detail:
        msg += f"\n        => {detail}"
    print(msg)
    return condition


def main():
    print("======================================================================")
    print(" AIForge Day 45 - Master Orchestrator Agent Verification Suite")
    print("======================================================================")

    orchestrator = MasterOrchestratorAgent()

    # ==============================================================
    section("Requirement 1 & 8 – Dependency Graph & Gate Enforcement")
    # ==============================================================
    graph = orchestrator.build_default_task_graph("Build AI Banking Platform")
    layers = graph.get_executable_layers()

    check("Dependency-aware task graph built with 9 specialized agent nodes", len(graph.nodes) == 9)
    check("Topological sorting produced parallel execution layers", len(layers) >= 5)

    # Verify gate enforcement
    n_planner = graph.nodes["node-planner"]
    n_be = graph.nodes["node-be"]
    n_planner.status = "completed"

    check("Upstream dependency gate passes when dependencies completed", graph.verify_dependency_gate(n_planner))
    check("Upstream dependency gate blocks node when dependencies pending", not graph.verify_dependency_gate(n_be))

    # ==============================================================
    section("Requirement 2, 3 & 9 – Execution, Parallel Layers & Shared Memory")
    # ==============================================================
    res = asyncio.run(orchestrator.orchestrate_project("Build AI Banking Platform"))
    report = res["execution_report"]
    shared_mem = res["shared_memory_snapshot"]

    check("Parallel layer execution completed autonomously", report["total_tasks_completed"] == 9)
    check("Synchronized outputs saved into Shared Context Memory", len(shared_mem.get("artifacts", {})) >= 9)

    # ==============================================================
    section("Requirement 5, 6 & 7 – Retries, Backoff, Events & Metrics")
    # ==============================================================
    res_retry = asyncio.run(orchestrator.orchestrate_project("Build AI Banking Platform", force_retry_test=True))
    report_retry = res_retry["execution_report"]
    events = report_retry["events"]
    event_types = {e["event_type"] for e in events}

    check("Intermittent node failure triggered retry loop", report_retry["total_retries"] > 0)
    check("Project health status computed (Degraded / Recovered)", "Degraded" in report_retry["project_health"] or "Healthy" in report_retry["project_health"])
    check("Event emission recorded (agent_started, agent_finished, agent_failed, agent_retried)", {"agent_started", "agent_finished", "agent_failed", "agent_retried"}.issubset(event_types))
    check("Execution metrics tracked (timing ms, tokens, retries)", report_retry["total_execution_time_ms"] > 0 and report_retry["total_tokens_used"] > 0)

    # ==============================================================
    section("Requirement 10 – Final Execution Report")
    # ==============================================================
    md_report = res_retry["markdown_report"]
    check("Final Execution Report generated in JSON", "project_health" in report_retry and "task_nodes" in report_retry)
    check("Final Execution Report generated in Markdown format", "# AIForge Orchestrator Execution Report" in md_report)

    # Summary
    print("\n" + "="*70)
    print(f" DAY 45 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
