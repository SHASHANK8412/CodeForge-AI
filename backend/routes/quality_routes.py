"""
FastAPI Routes for Day 36 Autonomous Code Quality, Security & Compliance Platform
===================================================================================
Exposes REST APIs for static code analysis, security scanning, dependency auditing, compliance validation, software metrics computation, automated refactoring suggestions, and project certification.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from backend.quality.static_analyzer import global_static_code_analyzer
from backend.quality.security_scanner import global_security_scanner
from backend.quality.dependency_scanner import global_dependency_scanner
from backend.quality.compliance_checker import global_compliance_checker
from backend.quality.code_metrics import global_code_metrics_engine
from backend.quality.certification import global_certification_engine

router = APIRouter(tags=["Autonomous Code Quality, Security & Compliance"])


class AnalyzeQualityInput(BaseModel):
    project_path: Optional[str] = "src/"
    project_name: Optional[str] = "Project"


class CertifyProjectInput(BaseModel):
    project_name: Optional[str] = "Project"


@router.post("/quality/analyze")
@router.post("/api/v1/quality/analyze")
async def analyze_project_quality(req: AnalyzeQualityInput) -> Dict[str, Any]:
    """Performs full static code inspection, complexity analysis, and vulnerability scan."""
    try:
        path = req.project_path or "src/"
        name = req.project_name or "Project"
        static_res = global_static_code_analyzer.analyze_project(path)
        sec_res = global_security_scanner.scan_project(path)
        metrics_res = global_code_metrics_engine.calculate_metrics(name)

        return {
            "status": "success",
            "static_analysis": static_res,
            "security_scan": sec_res,
            "code_metrics": metrics_res
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/quality/report")
@router.get("/api/v1/quality/report")
async def get_quality_report(project_name: Optional[str] = Query("Project", description="Target project name")) -> Dict[str, Any]:
    """Retrieves full quality certification report and score breakdown."""
    cert = global_certification_engine.certify_project(project_name or "Project")
    return {"status": "success", "quality_report": cert}


@router.get("/quality/metrics")
@router.get("/api/v1/quality/metrics")
async def get_code_metrics(project_name: Optional[str] = Query("Project", description="Target project name")) -> Dict[str, Any]:
    """Retrieves Cyclomatic Complexity, Maintainability Index, Technical Debt, and Test Coverage."""
    metrics = global_code_metrics_engine.calculate_metrics(project_name or "Project")
    return {"status": "success", "code_metrics": metrics}


@router.get("/quality/security")
@router.get("/api/v1/quality/security")
async def get_security_scan_results(project_path: Optional[str] = Query("src/", description="Target project directory path")) -> Dict[str, Any]:
    """Retrieves OWASP Top 10 vulnerability scan results."""
    sec = global_security_scanner.scan_project(project_path or "src/")
    return {"status": "success", "security_scan": sec}


@router.get("/quality/compliance")
@router.get("/api/v1/quality/compliance")
async def get_compliance_status(project_name: Optional[str] = Query("Project", description="Target project name")) -> Dict[str, Any]:
    """Retrieves OWASP, REST API, GDPR logging, and coding standards compliance report."""
    comp = global_compliance_checker.check_compliance(project_name or "Project")
    return {"status": "success", "compliance_report": comp}


@router.post("/quality/certify")
@router.post("/api/v1/quality/certify")
async def certify_project_release(req: CertifyProjectInput) -> Dict[str, Any]:
    """Issues AIForge Project Certification (Grade A+, Deployment Ready: YES) if all quality gates pass."""
    try:
        cert = global_certification_engine.certify_project(req.project_name or "Project")
        return {"status": "success", "certification": cert}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/quality/dashboard")
@router.get("/api/v1/quality/dashboard")
async def get_quality_dashboard() -> Dict[str, Any]:
    """Retrieves Quality Dashboard data: Overall Quality Score, Security Score, Performance Score, Technical Debt, Compliance Status, Dependency Health, Code Metrics, Quality Trends."""
    dash = global_certification_engine.get_quality_dashboard()
    return {"status": "success", "quality_dashboard": dash}
