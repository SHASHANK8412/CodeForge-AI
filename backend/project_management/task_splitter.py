"""
AIForge Task Splitter & Feature Decomposer
==========================================
Decomposes high-level software project requests (e.g., "Build a Food Delivery App") into granular development tasks
across Frontend, Backend, Database, Authentication, Payments, Orders, Admin Panel, Notifications, Deployment, Documentation.
"""

import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.project_management")


class TaskSplitter:
    """
    Decomposes high-level requirements into structured engineering tasks.
    """

    def decompose_project(self, project_prompt: str) -> List[Dict[str, Any]]:
        prompt_lower = project_prompt.lower()
        _logger.info(f"TaskSplitter: Decomposing project prompt: '{project_prompt}'")

        if "food" in prompt_lower or "delivery" in prompt_lower:
            task_names = [
                ("TASK-101", "Design Database Schema & Models", "Database", "Critical"),
                ("TASK-102", "Implement JWT Authentication & User Authorization", "Backend", "High"),
                ("TASK-103", "Develop Order Management & Restaurant API Endpoints", "Backend", "High"),
                ("TASK-104", "Integrate Stripe & Digital Wallet Payment Gateway", "Payments", "High"),
                ("TASK-105", "Build Customer & Driver React UI Dashboards", "Frontend", "Medium"),
                ("TASK-106", "Implement Real-time Push Notifications & Order Tracking", "Notifications", "Medium"),
                ("TASK-107", "Build Admin Panel Portal", "Admin Panel", "Low"),
                ("TASK-108", "Setup Docker Multi-stage Containerization & CI/CD Pipeline", "Deployment", "Medium"),
                ("TASK-109", "Generate OpenAPI Documentation & Deployment README", "Documentation", "Low")
            ]
        else:
            task_names = [
                ("TASK-101", "Design Relational Database Models", "Database", "Critical"),
                ("TASK-102", "Implement REST API Gateway & Authentication", "Backend", "High"),
                ("TASK-103", "Develop React Tailwind Frontend Dashboard", "Frontend", "High"),
                ("TASK-104", "Integrate Payment & Billing APIs", "Payments", "Medium"),
                ("TASK-105", "Setup Multi-Stage Docker Container & CI/CD Deployment", "Deployment", "Medium"),
                ("TASK-106", "Generate OpenAPI Spec & System Documentation", "Documentation", "Low")
            ]

        tasks = []
        for tid, desc, category, priority in task_names:
            tasks.append({
                "task_id": tid,
                "description": desc,
                "category": category,
                "priority": priority,
                "status": "Todo"
            })

        _logger.info(f"TaskSplitter: Generated {len(tasks)} tasks for '{project_prompt}'")
        return tasks


global_task_splitter = TaskSplitter()
