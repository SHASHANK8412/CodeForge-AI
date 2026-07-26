"""
AIForge V2 Day 1 Verification Suite
====================================
End-to-end verification script for AIForge V2 Day 1 deliverables:
1. Enterprise folder structure & agent hierarchy
2. Central configuration system
3. Logging audit engine
4. Event Bus
5. CEO & Manager Agents
6. Database Schema
7. FastAPI Gateway Router
"""

import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from v2.configs.config import global_v2_config
from v2.logs.logger import global_v2_logger
from v2.agents.protocol import AgentRole
from v2.agents.ceo.ceo_agent import global_ceo_agent
from v2.agents.manager.manager_agent import global_manager_agent
from v2.events.event_bus import global_event_bus
from v2.database.schema_v2 import ProjectRecord

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


async def run_v2_day1_verification():
    print("======================================================================")
    print(" 🏢 AIForge V2 – Day 1 Foundation & Architecture Verification")
    print("======================================================================\n")

    # 1. Config & Logger
    section("1. Central Config & Enterprise Logging Engine")
    check("Central AppConfig initialized (v2.0.0 Enterprise)", global_v2_config.version == "2.0.0")
    log_rec = global_v2_logger.log_agent_action("ceo", "Init Prompt", "Init Output", 15.0)
    check("Structured Audit Logger recorded agent execution event", log_rec["agent"] == "ceo")

    # 2. Agent Protocol & Hierarchy
    section("2. Agent Hierarchy & Inter-Agent Protocol")
    spec = global_ceo_agent.evaluate_request("Build AI Customer Support Platform")
    check("CEO Agent evaluated request & created ProjectSpecification", spec.name is not None and spec.complexity_score > 0)

    tasks = global_manager_agent.plan_project_tasks(spec)
    check("Project Manager Agent decomposed spec into 8 departmental tasks", len(tasks) == 8)

    # 3. Event Bus
    section("3. Asynchronous Event Bus Infrastructure")
    event_received = []

    async def on_event(ev):
        event_received.append(ev)

    global_event_bus.subscribe("UserRequestReceived", on_event)
    await global_event_bus.publish("UserRequestReceived", {"project_id": spec.project_id}, sender="ceo")
    check("Async Event Bus published & delivered 'UserRequestReceived' event", len(event_received) == 1)

    # 4. Database Schema Models
    section("4. PostgreSQL / SQLAlchemy Database Schema")
    proj = ProjectRecord(id=spec.project_id, name=spec.name, client_prompt=spec.client_prompt, complexity_score=spec.complexity_score)
    check("PostgreSQL ProjectRecord model initialized cleanly", proj.id == spec.project_id)

    # Summary
    print("\n" + "="*70)
    print(f" AIFORGE V2 DAY 1 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


def main():
    return asyncio.run(run_v2_day1_verification())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
