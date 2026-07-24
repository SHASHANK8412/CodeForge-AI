"""
AIForge Day 96 & 97 Learning Analytics API Router
=================================================
Endpoints:
- GET /analytics
"""

from fastapi import APIRouter
from backend.learning.metrics import global_analytics_collector
from backend.learning.project_memory import global_project_memory_store

router = APIRouter(tags=["Analytics"])


@router.get("/analytics")
def get_learning_analytics():
    metrics = global_analytics_collector.calculate_performance_metrics()
    projects = global_project_memory_store.get_all_projects()

    return {
        "status": "success",
        "projects_count": len(projects),
        "metrics": metrics,
        "timeline_trends": [
            {"project": "Project 1", "learned": "Learned Authentication"},
            {"project": "Project 2", "learned": "Learned Better Database"},
            {"project": "Project 3", "learned": "Improved Performance"},
            {"project": "Project 4", "learned": "Reduced Bugs by 40%"}
        ]
    }
