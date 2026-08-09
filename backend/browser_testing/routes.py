"""
AIForge Day 17 — Autonomous Browser Testing REST API Routes
============================================================
Endpoints for:
- POST /api/projects/{projectId}/browser-tests/run
- GET  /api/projects/{projectId}/browser-tests/report
- POST /api/projects/{projectId}/browser-tests/self-test
- POST /api/projects/{projectId}/browser-tests/{scenarioId}/diagnose
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user
from backend.browser_testing.service import global_browser_service

day17_browser_testing_router = APIRouter(prefix="/api/projects", tags=["Autonomous Browser Testing"])


class RunBrowserTestsPayload(BaseModel):
    base_url: str = "http://localhost:3000"


@day17_browser_testing_router.post("/{project_id}/browser-tests/run")
async def run_browser_tests(
    project_id: str,
    payload: Optional[RunBrowserTestsPayload] = None,
    user: dict = Depends(get_current_user)
):
    base_url = payload.base_url if payload else "http://localhost:3000"
    report = global_browser_service.run_project_browser_tests(project_id, base_url)
    return {"status": "success", "report": report.model_dump()}


@day17_browser_testing_router.get("/{project_id}/browser-tests/report")
async def get_browser_test_report(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    report = global_browser_service.get_latest_report(project_id)
    return {"status": "success", "report": report.model_dump()}


@day17_browser_testing_router.post("/{project_id}/browser-tests/self-test")
async def run_aiforge_selftest(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    report = global_browser_service.run_aiforge_selftest()
    return {"status": "success", "report": report.model_dump()}


@day17_browser_testing_router.post("/{project_id}/browser-tests/{scenario_id}/diagnose")
async def diagnose_and_repair(
    project_id: str,
    scenario_id: str,
    user: dict = Depends(get_current_user)
):
    res = global_browser_service.diagnose_and_repair_failure(project_id, scenario_id)
    return {"status": "success", "repair_result": res}
