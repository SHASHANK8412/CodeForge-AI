"""
Day 42 - AI Solutions Architect & Pre-Coding Planning Verification Suite
==========================================================================
Validates all 12 Day 42 test scenarios:
1. Requirement Analysis
2. Domain Detection
3. Tech Stack Recommendation
4. Database Planner
5. API Planner
6. Folder Generator
7. Task Breakdown
8. Dependency Graph
9. Risk Analyzer
10. Cost Estimator
11. Workflow Integration (Execution Order & Pre-Coding Gate)
12. Dashboard UI State Verification
"""
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.planner.comprehensive_planner import (
    RequirementAnalyzer,
    DomainDetector,
    TechStackRecommender,
    DatabasePlanner,
    ApiPlanner,
    FolderGenerator,
    TaskBreakdownPlanner,
    DependencyGraphPlanner,
    RiskAnalyzer,
    CostEstimator,
    ComprehensivePlanner,
    WorkflowOrchestrator
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
    print(" AIForge Day 42 - Architecture Planning & Workflow Verification Suite")
    print("======================================================================")

    # ==============================================================
    section("Test 1 – Requirement Analysis")
    # ==============================================================
    req_analyzer = RequirementAnalyzer()
    res1 = req_analyzer.analyze("Build an AI-powered Expense Tracker with OCR bill scanning and analytics.")

    frs = res1.get("functional_requirements", [])
    nfrs = res1.get("non_functional_requirements", [])

    check("Executive Summary generated", bool(res1.get("executive_summary")))
    check("Functional Requirements present", len(frs) >= 5 and "Login" in frs and "OCR Receipt Scan" in frs)
    check("Non-Functional Requirements present", len(nfrs) >= 4 and any("JWT" in n for n in nfrs))
    check("User Stories generated", len(res1.get("user_stories", [])) >= 3)
    check("Acceptance Criteria generated", len(res1.get("acceptance_criteria", [])) >= 3)
    check("Assumptions generated", len(res1.get("assumptions", [])) >= 3)
    check("Constraints generated", len(res1.get("constraints", [])) >= 3)
    check("No code generated yet", res1.get("code_generated") is False)

    # ==============================================================
    section("Test 2 – Domain Detection")
    # ==============================================================
    detector = DomainDetector()
    prompts_to_test = [
        ("Build an online hospital management system.", "Healthcare"),
        ("Netflix Clone", "Entertainment"),
        ("Amazon Clone", "E-commerce"),
        ("ChatGPT Clone", "AI"),
        ("Instagram Clone", "Social Media"),
        ("Stock Trading Platform", "FinTech"),
        ("Learning Management System", "Education")
    ]

    all_domains_correct = True
    for p, expected_domain in prompts_to_test:
        detected = detector.detect(p)
        correct = (detected == expected_domain)
        check(f"Prompt '{p}' -> {detected}", correct, f"Expected: {expected_domain}, Got: {detected}")
        if not correct:
            all_domains_correct = False

    check("All domains correctly identified", all_domains_correct)

    # ==============================================================
    section("Test 3 – Tech Stack Recommendation")
    # ==============================================================
    recommender = TechStackRecommender()
    stack = recommender.recommend("Build a ride booking app.")

    check("Frontend: React", stack.get("frontend") == "React")
    check("Backend: FastAPI", stack.get("backend") == "FastAPI")
    check("Database: PostgreSQL", stack.get("database") == "PostgreSQL")
    check("Cache: Redis", stack.get("cache") == "Redis")
    check("Maps: Google Maps", stack.get("maps") == "Google Maps")
    check("Deployment: Docker", stack.get("deployment") == "Docker")
    check("Cloud: AWS", stack.get("cloud") == "AWS")

    # ==============================================================
    section("Test 4 – Database Planner")
    # ==============================================================
    db_planner = DatabasePlanner()
    db_schema = db_planner.plan("Food Delivery App")
    table_names = [t["table"] for t in db_schema]
    expected_tables = ["Users", "Restaurants", "Orders", "Menu", "Payments", "Drivers", "Reviews"]

    has_all_tables = all(tbl in table_names for tbl in expected_tables)
    check("All expected tables generated (Users, Restaurants, Orders, Menu, Payments, Drivers, Reviews)", has_all_tables)

    has_keys = all("primary_key" in t and "foreign_keys" in t and "indexes" in t and "relationships" in t for t in db_schema)
    check("Schema includes Primary Keys, Foreign Keys, Indexes, and Relationships", has_keys)

    # ==============================================================
    section("Test 5 – API Planner")
    # ==============================================================
    api_planner = ApiPlanner()
    api_spec = api_planner.plan("Build a task management application.")

    paths = [f"{ep['method']} {ep['path']}" for ep in api_spec]
    expected_paths = ["POST /login", "POST /signup", "GET /tasks", "POST /tasks", "PUT /tasks/{id}", "DELETE /tasks/{id}"]
    has_endpoints = all(p in paths for p in expected_paths)
    check("All REST endpoints planned", has_endpoints)

    has_endpoint_details = all("request_body" in ep and "response" in ep and "status_code" in ep and "validation" in ep for ep in api_spec)
    check("Each endpoint includes Request Body, Response, Status Code, and Validation", has_endpoint_details)

    # ==============================================================
    section("Test 6 – Folder Generator")
    # ==============================================================
    folder_gen = FolderGenerator()
    folders = folder_gen.generate()
    expected_folders = ["frontend/", "backend/", "database/", "docker/", "docs/", "tests/", "scripts/", ".github/"]
    has_folders = all(f in folders for f in expected_folders)
    check("Complete directory structure produced", has_folders)

    # ==============================================================
    section("Test 7 – Task Breakdown")
    # ==============================================================
    task_planner = TaskBreakdownPlanner()
    tasks = task_planner.breakdown()
    expected_task_order = ["1 Authentication", "2 Database", "3 Backend", "4 Frontend", "5 Testing", "6 Deployment"]
    check("Logical execution order produced", tasks == expected_task_order)

    # ==============================================================
    section("Test 8 – Dependency Graph")
    # ==============================================================
    dep_planner = DependencyGraphPlanner()
    graph = dep_planner.generate()
    rules_valid = dep_planner.verify_rules(graph)
    check("Dependencies graph generated", bool(graph))
    check("Backend waits for API, Frontend waits for Backend, Testing waits for everything", rules_valid)

    # ==============================================================
    section("Test 9 – Risk Analyzer")
    # ==============================================================
    risk_analyzer = RiskAnalyzer()
    risks = risk_analyzer.analyze("Build YouTube.")
    risk_names = [r["risk"] for r in risks]
    expected_risks = ["Large Video Storage", "CDN", "High Traffic", "Scalability", "Authentication", "Bandwidth", "Database Load"]
    has_risks = all(r in risk_names for r in expected_risks)
    has_mitigations = all("mitigation" in r and len(r["mitigation"]) > 5 for r in risks)
    check("All YouTube architectural risks detected", has_risks)
    check("Actionable mitigation suggestions provided for every risk", has_mitigations)

    # ==============================================================
    section("Test 10 – Cost Estimator")
    # ==============================================================
    estimator = CostEstimator()
    costs = estimator.estimate("Build a task management application.")
    check("Estimated Development Time present", "estimated_development_time" in costs)
    check("Token Usage present", "token_usage" in costs)
    check("RAM present", "ram" in costs)
    check("CPU present", "cpu" in costs)
    check("Storage present", "storage" in costs)
    check("Deployment Cost present", "deployment_cost" in costs)

    # ==============================================================
    section("Test 11 – Workflow Integration")
    # ==============================================================
    orchestrator = WorkflowOrchestrator()
    res11 = orchestrator.run_pipeline("Build an AI Resume Builder")

    trace = res11["execution_trace"]
    planning_stages = trace[:8]
    coding_stages = trace[8:]

    expected_planning = [
        "Planner Agent", "Requirement Agent", "Architect Agent", "Database Planner",
        "API Planner", "Task Breakdown", "Risk Analyzer", "Cost Estimator"
    ]
    expected_coding = ["Frontend Agent", "Backend Agent", "Testing Agent", "Documentation Agent"]

    check("Execution order: Planning phase precedes Coding phase", planning_stages == expected_planning and coding_stages == expected_coding)
    check("No coding agents start before planning phase is complete", res11["planning_complete_before_coding"] is True)
    check("All planning artifacts available to downstream agents", bool(res11["artifacts"]))

    # ==============================================================
    section("Test 12 – Dashboard Verification")
    # ==============================================================
    planner = ComprehensivePlanner()
    full_plan = planner.plan_project("Build an AI Resume Builder")

    ui_keys_present = {
        "Functional Requirements": bool(full_plan["requirements"]["functional_requirements"]),
        "Non-functional Requirements": bool(full_plan["requirements"]["non_functional_requirements"]),
        "User Stories": bool(full_plan["requirements"]["user_stories"]),
        "Tech Stack": bool(full_plan["tech_stack"]),
        "Architecture Diagram": bool(full_plan["domain"]),
        "Database Schema": bool(full_plan["database_schema"]),
        "API Endpoints": bool(full_plan["api_specifications"]),
        "Folder Structure": bool(full_plan["folder_structure"]),
        "Task Breakdown": bool(full_plan["task_breakdown"]),
        "Dependency Graph": bool(full_plan["dependency_graph"]),
        "Risks": bool(full_plan["risks"]),
        "Cost Estimation": bool(full_plan["cost_estimate"])
    }

    all_ui_elements = all(ui_keys_present.values())
    check("Dashboard UI payload contains all 12 required planning elements", all_ui_elements)

    # Summary
    print("\n" + "="*70)
    print(f" DAY 42 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
