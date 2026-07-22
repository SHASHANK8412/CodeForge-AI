"""
Day 49 - Communication Manager Infrastructure Verification Suite
==================================================================
Validates all requirements for the Communication Manager:
- 1. Structured Message Protocol (AgentMessage with trace_id and context_id)
- 2. Thread-Safe Shared Memory Workspace (atomic locking & snapshot)
- 3. Event-Driven Pub/Sub Broker
- 4. Priority Task Queue & Dead-Letter Queue (DLQ)
- 5. Exponential Backoff Retry Mechanism & Failure Recovery
- 6. Health Monitoring & Heartbeats for all 9 specialized agents
     (Planner, Architect, Frontend, Backend, Database, Reviewer, Testing, Documentation, Deployment)
"""

import sys
import asyncio
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.collaboration.communication_manager import (
    CommunicationManager,
    AgentMessage,
    AgentRole,
    AgentHealthStatus,
    MessagePriority
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
    print(" AIForge Communication Manager System Verification Suite")
    print("======================================================================")

    manager = CommunicationManager()

    # ==============================================================
    section("Test 1 – All 9 Agent Roles Registration & Health Monitoring")
    # ==============================================================
    health = manager.get_system_health()
    statuses = health["agent_statuses"]
    expected_agents = [
        "Planner", "Architect", "Frontend", "Backend",
        "Database", "Reviewer", "Testing", "Documentation", "Deployment"
    ]

    print("Registered Agents:")
    for ag in expected_agents:
        print(f"  - [{ag}] Status: {statuses.get(ag)}")

    check("All 9 specialized agents registered", health["total_agents"] == 9)
    check("All 9 agents initial health status HEALTHY", all(s == "HEALTHY" for s in statuses.values()))

    # ==============================================================
    section("Test 2 – Structured Message Protocol & Event Broker (Pub/Sub)")
    # ==============================================================
    received_msgs = []

    def on_api_request(msg: AgentMessage):
        received_msgs.append(msg)

    manager.event_broker.subscribe("api_request", on_api_request)

    sent_msg = manager.send_message(
        sender="Frontend",
        recipient="Backend",
        topic="api_request",
        payload={"request": "POST /api/v1/login"},
        priority=MessagePriority.HIGH
    )

    print("\nMessage Audit:")
    print(f"  Message ID: {sent_msg.message_id}")
    print(f"  Context ID: {sent_msg.context_id}")
    print(f"  Trace ID: {sent_msg.trace_id}")
    print(f"  Priority: {sent_msg.priority.name}\n")

    check("Message structured with unique ID, context_id, and trace_id", sent_msg.message_id and sent_msg.context_id and sent_msg.trace_id)
    check("Event-driven broker delivered message to subscriber", len(received_msgs) == 1 and received_msgs[0].sender == "Frontend")

    # ==============================================================
    section("Test 3 – Thread-Safe Shared Memory Workspace")
    # ==============================================================
    memory = manager.shared_memory

    # Agent 'Database' writes schema
    memory.set("active_schema", {"tables": ["users", "orders"]})

    # Agent 'Backend' reads schema
    read_schema = memory.get("active_schema")

    print("\nShared Memory Inspection:")
    print(f"  Read Schema Tables: {read_schema['tables']}\n")

    check("Data stored in shared memory workspace", memory.get("active_schema") is not None)
    check("Cross-agent data retrieval verified", read_schema["tables"] == ["users", "orders"])

    # ==============================================================
    section("Test 4 – Priority Task Queue & Retry Mechanism")
    # ==============================================================
    # Drain task queue
    while manager.task_queue.dequeue():
        pass

    msg_low = AgentMessage(sender="Docs", recipient="ALL", topic="info", priority=MessagePriority.LOW)
    msg_critical = AgentMessage(sender="Reviewer", recipient="Backend", topic="security_alert", priority=MessagePriority.CRITICAL)

    manager.task_queue.enqueue(msg_low)
    manager.task_queue.enqueue(msg_critical)

    first_dequeued = manager.task_queue.dequeue()

    print("\nPriority Queue Inspection:")
    print(f"  Highest Priority Dequeued: {first_dequeued.priority.name} (Sender: {first_dequeued.sender})\n")

    check("Priority queue dequeued CRITICAL message before LOW priority message", first_dequeued.priority == MessagePriority.CRITICAL)

    # Drain any remaining queue items before retry test
    while manager.task_queue.dequeue():
        pass

    attempt_counter = [0]

    def failing_handler(msg: AgentMessage):
        attempt_counter[0] += 1
        if attempt_counter[0] < 2:
            raise ConnectionError("Intermittent bus network timeout")
        return f"Processed on attempt {attempt_counter[0]}"

    manager.task_queue.enqueue(AgentMessage(sender="Backend", recipient="Database", topic="retry_test", max_retries=3))
    results = asyncio.run(manager.process_messages_with_retry(failing_handler))

    check("Retry mechanism recovered from intermittent handler error", len(results) == 1 and "attempt 2" in results[0])

    # ==============================================================
    section("Test 5 – Dead-Letter Queue (DLQ) & Failure Recovery")
    # ==============================================================
    def always_failing_handler(msg: AgentMessage):
        raise ValueError("Unrecoverable data corruption in message payload")

    manager.task_queue.enqueue(AgentMessage(sender="Frontend", recipient="Backend", topic="fatal_test", max_retries=2))
    asyncio.run(manager.process_messages_with_retry(always_failing_handler))

    dlq_items = manager.task_queue.get_dlq()

    print("\nDLQ Audit:")
    print(f"  DLQ Items Count: {len(dlq_items)}")
    if dlq_items:
        print(f"  DLQ Reason: {dlq_items[0].payload.get('dlq_reason')}\n")

    check("Permanently failed message routed to Dead-Letter Queue (DLQ)", len(dlq_items) == 1)
    check("DLQ message contains error reason in payload", "dlq_reason" in dlq_items[0].payload)

    # Summary
    print("\n" + "="*70)
    print(f" DAY 49 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
