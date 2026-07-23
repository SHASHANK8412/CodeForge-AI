"""
AIForge Intelligence & Quality REST API Endpoints
=================================================
FastAPI Endpoints for Days 86 & 87:
- GET /quality/latest
- GET /quality/history
- GET /recommendations
- GET /dashboard
- POST /analyze
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Body

from backend.intelligence.quality_engine import global_quality_engine
from backend.intelligence.recommendation_engine import global_recommendation_engine
from backend.database.quality_history import global_quality_history_db
from backend.dashboard.analytics import global_dashboard_analytics

router = APIRouter(prefix="/intelligence", tags=["Quality Intelligence"])
_logger = logging.getLogger("aiforge.routes")


@router.get("/quality/latest")
async def get_latest_quality():
    records = global_quality_history_db.get_all_records()
    latest = records[-1] if records else {"overall_score": 94.3, "project_name": "Default Project"}
    return {"status": "success", "latest_quality": latest}


@router.get("/quality/history")
async def get_quality_history():
    records = global_quality_history_db.get_all_records()
    return {"status": "success", "history": records}


@router.get("/recommendations")
async def get_recommendations():
    recs = global_recommendation_engine.generate_recommendations({
        "Architecture": 96, "Performance": 91, "Security": 95, "Documentation": 90, "Testing": 93, "Maintainability": 92
    })
    return {"status": "success", "recommendations": recs}


@router.get("/dashboard")
async def get_dashboard_analytics():
    data = global_dashboard_analytics.get_dashboard_data()
    return {"status": "success", "dashboard": data}


@router.post("/analyze")
async def analyze_project(payload: Dict[str, Any] = Body(...)):
    project_name = payload.get("project_name", "Enterprise SaaS")
    project_files = payload.get("project_files")
    result = global_quality_engine.analyze_project(project_name=project_name, project_files=project_files)
    return {"status": "success", "analysis": result}
