"""
AIForge REST API — AI Usage & Analytics Telemetry
=================================================
Endpoints:
- GET /api/analytics/metrics
"""

from fastapi import APIRouter
from backend.analytics.usage_service import global_usage_service

router = APIRouter(prefix="/api/analytics", tags=["AI Usage & Telemetry"])


@router.get("/metrics")
def get_analytics_metrics():
    metrics = global_usage_service.get_platform_metrics()
    return {
        "success": True,
        "metrics": metrics
    }
