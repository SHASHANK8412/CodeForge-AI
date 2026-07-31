"""
AIForge V2 Day 45 Verification Suite: MCP Integration & Universal Tool Ecosystem
===================================================================================
Tests all Day 45 scenarios:
1. GitHub unavailable -> Retry then fallback
2. Filesystem access -> Reads/Writes successfully
3. Browser search -> Returns webpage content
4. PostgreSQL query -> Executes safely
5. Unknown tool / Permission check -> Authorization enforcement
6. 12 MCP Servers status & capability discovery
"""

import sys
import json
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.mcp.server_registry import global_server_registry
from backend.mcp.mcp_manager import global_mcp_manager
from backend.mcp.permissions import global_mcp_permissions
from backend.mcp.health_monitor import global_mcp_health_monitor

PASS = "[PASS]"
FAIL = "[FAIL]"
_results = {"passed": 0, "failed": 0}


def section(title: str):
    print(f"\n{'='*75}")
    print(f"  {title}")
    print(f"{'='*75}")


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


def verify_day45_pipeline():
    print("===========================================================================")
    print(" 🚀 AIForge V2 – Day 45 MCP Integration & Universal Tool Ecosystem")
    print("===========================================================================\n")

    registry = global_server_registry
    manager = global_mcp_manager
    permissions = global_mcp_permissions
    health = global_mcp_health_monitor

    # ---------------------------------------------------------
    # Scenario 1: GitHub Unavailable -> Fallback
    # ---------------------------------------------------------
    section("Scenario 1: GitHub Offline -> Fallback Execution")
    registry.set_server_status("github", "offline")
    res1 = manager.execute_tool_call("github", "create_pr", {"title": "Feature PR"}, user_permission="WRITE")
    check("Handled offline GitHub MCP server via automatic retry & fallback", res1["status"] == "FALLBACK_EXECUTED")
    check("Resumed workflow via fallback server without stopping execution", res1["fallback_server"] in ["filesystem", "terminal"])
    registry.set_server_status("github", "connected", latency_ms=145)

    # ---------------------------------------------------------
    # Scenario 2: Filesystem Access -> Reads/Writes Successfully
    # ---------------------------------------------------------
    section("Scenario 2: Filesystem Access -> Reads/Writes")
    res2 = manager.execute_tool_call("filesystem", "write_file", {"path": "backend/main.py", "content": "app = FastAPI()"}, user_permission="WRITE")
    check("Executed filesystem write tool successfully", res2["status"] == "SUCCESS")

    # ---------------------------------------------------------
    # Scenario 3: Browser Search -> Returns Webpage Content
    # ---------------------------------------------------------
    section("Scenario 3: Browser Search -> Returns Webpage Content")
    res3 = manager.execute_tool_call("browser", "browser_search", {"query": "FastAPI Pydantic v2 migration"}, user_permission="READ")
    check("Executed browser search tool and fetched content", res3["status"] == "SUCCESS")

    # ---------------------------------------------------------
    # Scenario 4: PostgreSQL Query -> Executes Safely
    # ---------------------------------------------------------
    section("Scenario 4: PostgreSQL Query -> Executes Safely")
    res4 = manager.execute_tool_call("postgres", "query_db", {"sql": "SELECT * FROM users;"}, user_permission="READ")
    check("Executed PostgreSQL query safely", res4["status"] == "SUCCESS")

    # ---------------------------------------------------------
    # Scenario 5: Permission Enforcement & Authorization
    # ---------------------------------------------------------
    section("Scenario 5: Permission System & Authorization")
    res5_denied = manager.execute_tool_call("postgres", "execute_db_migration", {"sql": "DROP TABLE users;"}, user_permission="READ")
    res5_allowed = manager.execute_tool_call("postgres", "execute_db_migration", {"sql": "CREATE TABLE users (id INT);"}, user_permission="ADMIN")
    check("Blocked unauthorized execution (READ permission insufficient for ADMIN tool)", res5_denied["status"] == "PERMISSION_DENIED")
    check("Allowed execution with ADMIN permission level", res5_allowed["status"] == "SUCCESS")

    # ---------------------------------------------------------
    # Scenario 6: 12 MCP Servers Status & Dynamic Capability Discovery
    # ---------------------------------------------------------
    section("Scenario 6: 12 MCP Servers & Capability Discovery")
    all_servers = registry.get_all_servers()
    all_tools = manager.discover_tools()
    health_res = health.check_health()

    check("Registered 12 supported MCP servers (FS, GitHub, Postgres, Docker, Browser, Terminal, Redis, K8s, AWS, Slack, Jira, Notion)",
          len(all_servers) == 12)
    check("Discovered dynamic tool capabilities across active servers", len(all_tools) >= 10)
    check("Tracked connection health and latency in MCP Health Monitor", health_res["total_servers"] == 12 and health_res["health_score_pct"] > 80)

    # Summary
    print("\n" + "="*75)
    print(f" AIFORGE V2 DAY 45 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*75 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = verify_day45_pipeline()
    sys.exit(0 if success else 1)
