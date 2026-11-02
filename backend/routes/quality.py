import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from backend.graph.executor import global_workflow_executor
from backend.quality.report_generator import global_quality_report_generator
from backend.quality.benchmark import global_quality_benchmarker

logger = logging.getLogger("aiforge.routes.quality")

router = APIRouter(tags=["Quality Assurance & Performance"])


@router.get("/quality-report/{project_id}")
@router.get("/api/quality-report/{project_id}")
def get_quality_report(project_id: str):
    """Static analysis, security scan and quality scores of the project's recorded files."""
    status = global_workflow_executor.get_project_status(project_id)
    files = status.get("project_files", {})
    if not files:
        # never a report about invented sample files
        raise HTTPException(status_code=404, detail=f"No files are recorded for project '{project_id}'.")

    report = global_quality_report_generator.generate_full_report(files)
    report["project_id"] = project_id
    return report


@router.post("/optimize/{project_id}")
@router.post("/api/optimize/{project_id}")
def optimize_project(project_id: str):
    """Executes Auto-Fix Pipeline to format code, clean whitespace, and optimize performance."""
    status = global_workflow_executor.get_project_status(project_id)
    files = status.get("project_files", {})
    if not files:
        # never a report about invented sample files
        raise HTTPException(status_code=404, detail=f"No files are recorded for project '{project_id}'.")

    fixed_files = global_quality_report_generator.apply_autofix(files)
    new_report = global_quality_report_generator.generate_full_report(fixed_files)

    return {
        "status": "success",
        "project_id": project_id,
        "message": "Auto-Fix pipeline executed successfully.",
        "optimized_file_count": len(fixed_files),
        "new_quality_score": new_report["scores"]["overall_score"]
    }


@router.get("/api/projects/{generation_id}/quality")
def get_project_quality_center_data(generation_id: str):
    """
    The Quality Center report, computed only from recorded evidence (backend/quality/evidence.py): the Execution
    Guardian's latest verification, the Integration Engine's latest run and the project's files. A gate no recorded
    check covers is NOT_EVALUATED and has no score; nothing here is a fixed or estimated value.
    """
    from backend.quality import evidence
    from backend.routes.project import resolve_generated_project_dir
    target_dir = resolve_generated_project_dir(generation_id)
    if not target_dir:
        raise HTTPException(status_code=404, detail=f"No generated project found for '{generation_id}'.")

    ev = evidence.collect(generation_id, target_dir)
    gates = evidence.gates(ev)
    summ = evidence.summary(gates)
    tests = evidence.tests(ev)
    by_name = {g["name"][3:]: g for g in gates}

    def area(*names):
        rated = [by_name[n] for n in names if by_name[n]["status"] in ("PASSED", "FAILED", "WARNING", "BLOCKED")]
        return round(100.0 * sum(1 for g in rated if g["status"] == "PASSED") / len(rated), 1) if rated else None

    v, r = ev["verification"], ev["integration"]
    # No score without the core evidence: a README alone must not read as "100% excellent".
    pass_rate = summ["pass_rate"] if v is not None else None
    status = ("not_evaluated" if pass_rate is None else "excellent" if pass_rate >= 90 else "good" if pass_rate >= 75
              else "needs_improvement" if pass_rate >= 60 else "poor")
    auth_findings = [f for f in (r.findings if r else []) if f.rule == "auth_mismatch" and f.status in evidence.OPEN]
    sec_check = next((c for c in (v.checks if v else []) if c.name == "security_static"), None)
    recommendations = [{"priority": "HIGH" if g["status"] in ("FAILED", "BLOCKED") else "MEDIUM", "title": g["name"][3:],
                        "description": f"{g['findings'][0]} - {g['recommendation']}"}
                       for g in gates if g["status"] in ("FAILED", "BLOCKED", "WARNING")]
    if v is None:
        recommendations.append({"priority": "HIGH", "title": "Verify the project", "description":
                                "No Execution Guardian verification is recorded: run one so the checks are evidence."})
    if r is None:
        recommendations.append({"priority": "MEDIUM", "title": "Check component compatibility", "description":
                                "No Integration Engine run is recorded: register or derive a contract and run Verify."})
    contract_counts = (r.test_execution or {}).get("counts", {}) if r else {}
    contract_ran = bool(r and r.tests and (r.test_execution or {}).get("status") in ("PASSED", "FAILED"))
    return {
        "project_id": generation_id,
        "project_name": target_dir.name,
        "overall_score": pass_rate,              # None when no gate was evaluated
        "score_basis": "percentage of evaluated quality gates that passed (gates not evaluated are excluded); no score until an Execution Guardian verification exists",
        "status": status,
        "categories": {
            "code_quality": area("Python Syntax", "Code-Quality Gate"),
            "api_compatibility": area("API Contract Compatibility"),
            "database": area("Database Compatibility"),
            "security": area("Static Security Scan"),
            "build_and_startup": area("Python Dependency Install", "Backend Startup", "Frontend Dependency Install",
                                      "Frontend Build"),
            "testing": area("Python Tests", "Frontend Tests"),
            "documentation": area("Documentation"),
            "performance": None,
        },
        "quality_gates": gates,
        "passed_gates_count": summ["passed"],
        "evaluated_gates_count": summ["evaluated"],
        "total_gates_count": summ["total"],
        "tests": tests,
        "test_breakdown": {k: x for k, x in {
            "project tests": {"passed": tests["passed"], "total": tests["total"]} if tests else None,
            "contract tests": {"passed": contract_counts.get("passed", 0), "total": len(r.tests)} if contract_ran else None,
        }.items() if x},
        "security": {
            "critical": None, "high": None, "medium": None, "low": None,
            "checks": {k: x for k, x in {
                "static_scan (Bandit)": ({"PASSED": "PASSED", "FAILED": "WARNING"}.get(sec_check.status, sec_check.status)
                                         if sec_check else None),
                "auth_matches_contract": ("FAILED" if auth_findings else "PASSED") if r else None,
            }.items() if x},
        },
        "performance": {},
        "reviewer_findings": [],
        "testing_findings": {
            "status": "NOT_RUN" if tests is None else "FAIL" if tests["failed"] else "PASS",
            "tests_generated": None,
            "tests_executed": tests["total"] if tests else None,
            "tests_passed": tests["passed"] if tests else None,
            "tests_failed": tests["failed"] if tests else None,
            "failed_tests": tests["failing_tests"] if tests else [],
        },
        "recommendations": recommendations,
        "evidence": {
            "verification": {"id": v.id, "status": v.status, "source": v.source, "finished_at": v.finished_at} if v else None,
            "integration_run": {"id": r.id, "status": r.status, "kind": r.kind, "finished_at": r.finished_at} if r else None,
        },
    }
