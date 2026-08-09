"""
AIForge V2 Day 30 Verification Suite
=====================================
End-to-end verification script for AIForge V2 Day 30 deliverables:
1. Message Bus & Inter-Agent Communication Protocol (TASK, RESPONSE, REQUEST, ERROR, EVENT, WARNING, COMPLETE)
2. Agent Inbox Management & Priority Queue Processing (CRITICAL, HIGH, MEDIUM, LOW)
3. Shared Project Context Synchronization (State Updates, Artifact Storage, Agent Output Retrieval)
4. Event Dispatcher & Pub/Sub Event Timeline (PROJECT_STARTED, TASK_ASSIGNED, BUILD_FINISHED, etc.)
5. Inter-Agent Dependency Manager (Task Blocking & Automatic Resumption)
6. Priority-Based Conflict Resolution Engine (PM > Reviewer > Testing > Architect > Dev)
7. Communication Logging to `logs/communication.log`
8. Enhanced Collaboration Dashboard REST APIs
"""

import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.communication.protocol import AgentMessage, MessageType, MessagePriority
from backend.communication.message_bus import global_message_bus
from backend.communication.shared_context import global_shared_context
from backend.communication.events import global_event_dispatcher, SystemEventType
from backend.communication.dependency_manager import global_dependency_manager
from backend.communication.conflict_resolution import global_conflict_resolver
from backend.communication.communication_logger import global_communication_logger

PASS = "[PASS]"
FAIL = "[FAIL]"
_results = {"passed": 0, "failed": 0}


def section(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def check(name: str, condition: bool, detail: str = ""):
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


def run_v2_day30_verification():
    print("======================================================================")
    print(" 💬 AIForge V2 – Day 30 Multi-Agent Communication & Collaboration Verification")
    print("======================================================================\n")

    section("1. Message Bus & Agent Protocol Schema")
    msg1 = AgentMessage(
        sender="Planner Agent",
        receiver="Architect Agent",
        type=MessageType.TASK,
        priority=MessagePriority.HIGH,
        payload={"summary": "Generate architecture blueprint for Food Delivery App."}
    )
    delivered = global_message_bus.send_message(msg1)
    check("Sent AgentMessage via MessageBus", delivered["sender"] == "Planner Agent")

    all_msgs = global_message_bus.get_all_messages()
    check("Retrieved all messages from MessageBus", len(all_msgs) >= 5)

    section("2. Agent Inbox Queues & Priority Processing")
    inbox = global_message_bus.get_agent_inbox("Architect Agent")
    check("Retrieved Architect Agent inbox queue", len(inbox) >= 1)

    processed = global_message_bus.process_next_message("Architect Agent")
    check("Processed highest priority message from inbox", processed is not None and processed["acknowledged"])

    section("3. Shared Project Context & Artifact Storage")
    ctx = global_shared_context.get_context()
    check("Read Shared Project Context", ctx["project_name"] == "Food Delivery App")

    art = global_shared_context.store_artifact("openapi_schema.json", {"paths": ["/api/v1/login"]}, agent="Architect Agent")
    check("Stored shared artifact in project context", art["created_by"] == "Architect Agent")

    retrieved_art = global_shared_context.get_artifact("openapi_schema.json")
    check("Retrieved shared artifact from context", retrieved_art is not None and "paths" in retrieved_art["content"])

    upd_ctx = global_shared_context.update_state({"completed_tasks": ["Planner Setup", "Architecture Spec", "DB Schema"]})
    check("Updated shared project state", len(upd_ctx["completed_tasks"]) == 3)

    section("4. Event Dispatcher & Subscriptions")
    events_received = []

    def on_task_completed(event):
        events_received.append(event)

    global_event_dispatcher.subscribe(SystemEventType.TASK_COMPLETED, on_task_completed)
    
    pub_event = global_event_dispatcher.publish(
        event_type=SystemEventType.TASK_COMPLETED,
        publisher="Backend Agent",
        data={"task": "Authentication API", "status": "Done"}
    )
    check("Published system event & executed subscriber callback", len(events_received) >= 1 and pub_event["event_type"] == SystemEventType.TASK_COMPLETED)

    timeline = global_event_dispatcher.get_event_timeline()
    check("Retrieved system event timeline", len(timeline) >= 2)

    section("5. Inter-Agent Dependency Manager")
    dep = global_dependency_manager.register_dependency(
        consumer_agent="Frontend Agent",
        prerequisite="Payment Gateway Backend API",
        provider_agent="Backend Agent"
    )
    check("Registered task execution dependency", dep["status"] == "WAITING")
    check("Verified Frontend Agent is blocked by dependency", global_dependency_manager.is_agent_blocked("Frontend Agent"))

    resolved = global_dependency_manager.resolve_dependency("Payment Gateway Backend API")
    check("Resolved task dependency and unblocked agent", len(resolved) >= 1 and not global_dependency_manager.is_agent_blocked("Frontend Agent"))

    section("6. Priority-Based Conflict Resolution Engine")
    conflict = global_conflict_resolver.resolve_conflict(
        topic="Button Component Accessibility Styling",
        agent_a="Reviewer Agent",
        proposal_a="Increase contrast ratio to WCAG AAA compliance",
        agent_b="Frontend Agent",
        proposal_b="Keep current subtle palette to preserve design mockups"
    )
    check("Resolved inter-agent conflict using role priority (Reviewer > Frontend)", conflict["winning_agent"] == "Reviewer Agent")

    section("7. Communication Logging")
    logs = global_communication_logger.get_logs()
    check("Recorded communication log entries", len(logs) >= 5)

    log_file = Path(__file__).resolve().parents[1] / "logs" / "communication.log"
    check("Persisted interaction logs to `logs/communication.log`", log_file.exists())

    # Summary
    print("\n" + "="*70)
    print(f" AIFORGE V2 DAY 30 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = run_v2_day30_verification()
    sys.exit(0 if success else 1)
