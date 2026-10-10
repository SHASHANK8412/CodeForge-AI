"""
AIForge Portfolio Dashboard Manager
====================================
Aggregates status, metrics, health, and progress across all workspace projects for executive portfolio visibility.
"""

import time
from typing import Dict, Any, List
from backend.workspace.scheduler import global_agent_scheduler


class PortfolioDashboardManager:
    """
    Manages portfolio aggregation and project health analytics.
    """

    def __init__(self) -> None:
        self.project_stats: Dict[str, Dict[str, Any]] = {
            "proj_ecommerce": {
                "project_id": "proj_ecommerce",
                "name": "Ecommerce Platform",
                "health": "Healthy",
                "completion_percentage": 85,
                "running_tasks": 2,
                "failed_tasks": 0,
                "deployment_status": "Deployed to Staging",
                "active_agents": ["Backend Agent", "QA Agent"]
            },
            "proj_hospital": {
                "project_id": "proj_hospital",
                "name": "Hospital Management",
                "health": "Healthy",
                "completion_percentage": 70,
                "running_tasks": 3,
                "failed_tasks": 0,
                "deployment_status": "Build Passing",
                "active_agents": ["Product Manager Agent", "Architect Agent"]
            },
            "proj_airesume": {
                "project_id": "proj_airesume",
                "name": "AI Resume Analyzer",
                "health": "Healthy",
                "completion_percentage": 95,
                "running_tasks": 1,
                "failed_tasks": 0,
                "deployment_status": "Production Live",
                "active_agents": ["DevOps Agent"]
            },
            "proj_crm": {
                "project_id": "proj_crm",
                "name": "CRM System",
                "health": "Healthy",
                "completion_percentage": 60,
                "running_tasks": 2,
                "failed_tasks": 0,
                "deployment_status": "In Development",
                "active_agents": ["Frontend Agent"]
            }
        }

    def register_or_update_project(
        self,
        project_id: str,
        name: str,
        health: str = "Healthy",
        completion_percentage: int = 50,
        running_tasks: int = 1,
        failed_tasks: int = 0,
        deployment_status: str = "In Development",
        active_agents: List[str] = None
    ) -> Dict[str, Any]:
        info = {
            "project_id": project_id,
            "name": name,
            "health": health,
            "completion_percentage": max(0, min(100, completion_percentage)),
            "running_tasks": running_tasks,
            "failed_tasks": failed_tasks,
            "deployment_status": deployment_status,
            "active_agents": active_agents or ["Backend Agent"]
        }
        self.project_stats[project_id] = info
        return info

    def get_portfolio_dashboard(self) -> Dict[str, Any]:
        scheduler_status = global_agent_scheduler.get_scheduler_status()

        total_projects = len(self.project_stats)
        projects_list = list(self.project_stats.values())

        total_running_tasks = sum(p["running_tasks"] for p in projects_list) + scheduler_status["in_progress_tasks"]
        total_failed_tasks = sum(p["failed_tasks"] for p in projects_list)
        active_agents_count = scheduler_status["busy_agents"]
        
        avg_completion = round(sum(p["completion_percentage"] for p in projects_list) / max(1, total_projects), 1)

        health_breakdown = {
            "Healthy": len([p for p in projects_list if p["health"] == "Healthy"]),
            "Warning": len([p for p in projects_list if p["health"] == "Warning"]),
            "Critical": len([p for p in projects_list if p["health"] == "Critical"])
        }

        return {
            "timestamp": time.time(),
            "total_projects": total_projects,
            "active_agents": active_agents_count,
            "total_agents": scheduler_status["total_agents"],
            "running_tasks": total_running_tasks,
            "failed_tasks": total_failed_tasks,
            "average_completion_percentage": avg_completion,
            "health_breakdown": health_breakdown,
            "projects": projects_list,
            "scheduler_overview": scheduler_status
        }


global_portfolio_dashboard = PortfolioDashboardManager()
