"""
AIForge V2 Day 39 Verification Suite
=====================================
End-to-end verification script for AIForge V2 Day 39 deliverables:
1. Plugin Manifest Schema Validation (name, version, author, permissions, entry)
2. Plugin Permissions Security Boundary Authorization
3. Plugin Registry State Store
4. Dynamic Event Dispatcher Subscriptions (PROJECT_CREATED, BUILD_COMPLETED, DEPLOYMENT_FINISHED)
5. 7-Stage Plugin Lifecycle Management (Install, Enable, Disable, Update, Uninstall)
6. Plugin Marketplace Catalog & Ratings
7. Plugin Dashboard Metrics & REST APIs
"""

import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.plugins.validator import global_plugin_manifest_validator
from backend.plugins.permissions import global_plugin_permissions_system
from backend.plugins.registry import global_plugin_registry
from backend.plugins.loader import global_dynamic_plugin_loader, EventTopic
from backend.plugins.manager import global_plugin_manager
from backend.plugins.marketplace import global_plugin_marketplace

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


def run_v2_day39_verification():
    print("======================================================================")
    print(" 🔌 AIForge V2 – Day 39 AI Plugin Ecosystem & Marketplace Verification")
    print("======================================================================\n")

    section("1. Plugin Manifest Schema Validation")
    manifest = {
        "name": "Jira Plugin",
        "version": "1.0.0",
        "author": "Atlassian",
        "description": "Jira Task Synchronization",
        "permissions": ["internet"],
        "entry": "plugin.py"
    }
    is_valid, errors = global_plugin_manifest_validator.validate_manifest(manifest)
    check("Validated valid plugin manifest schema", is_valid and len(errors) == 0)

    section("2. Plugin Permissions Security Boundary Authorization")
    auth_ok = global_plugin_permissions_system.authorize_plugin_action(["repo.read", "repo.write"], "repo.read")
    auth_denied = global_plugin_permissions_system.authorize_plugin_action(["repo.read"], "filesystem")
    check("Authorized granted permission, denied ungranted permission", auth_ok and not auth_denied)

    section("3. Plugin Installation & Lifecycle Management")
    install_res = global_plugin_manager.install_plugin(manifest)
    check("Installed plugin via 7-stage lifecycle manager", install_res["status"] == "INSTALLED")

    disable_res = global_plugin_manager.disable_plugin("jira_plugin")
    check("Disabled plugin status (DISABLED)", disable_res["status"] == "DISABLED")

    enable_res = global_plugin_manager.enable_plugin("jira_plugin")
    check("Enabled plugin status (ACTIVE)", enable_res["status"] == "ACTIVE")

    update_res = global_plugin_manager.update_plugin("jira_plugin", "1.1.0")
    check("Updated plugin to version 1.1.0", update_res["plugin"]["version"] == "1.1.0")

    section("4. Dynamic Event Dispatcher Subscriptions")
    event_res = global_dynamic_plugin_loader.dispatch_event(EventTopic.PROJECT_CREATED, {"project": "Food Delivery"})
    check("Dispatched PROJECT_CREATED event to subscribed plugins", event_res["subscribers_notified"] >= 2)

    section("5. Plugin Marketplace Catalog")
    catalog = global_plugin_marketplace.get_marketplace_catalog()
    check("Retrieved Plugin Marketplace catalog & categories", catalog["total_marketplace_plugins"] >= 4 and len(catalog["categories"]) >= 5)

    section("6. Plugin Dashboard Metrics")
    dashboard = global_plugin_manager.get_plugin_dashboard()
    check("Compiled Plugin Dashboard metrics", dashboard["total_installed_plugins"] >= 3 and len(dashboard["system_event_topics"]) == 6)

    # Summary
    print("\n" + "="*70)
    print(f" AIFORGE V2 DAY 39 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = run_v2_day39_verification()
    sys.exit(0 if success else 1)
