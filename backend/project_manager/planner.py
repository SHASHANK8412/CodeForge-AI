import logging
from typing import Dict, Any, List

from backend.agents.product_manager import global_product_manager_agent
from backend.project_manager.epics import global_epic_generator
from backend.project_manager.stories import global_user_story_generator
from backend.project_manager.tasks import global_task_breakdown_engine
from backend.project_manager.dependency_graph import global_project_dependency_graph
from backend.project_manager.sprint import global_sprint_planner
from backend.project_manager.tracker import global_progress_tracker
from backend.project_manager.analytics import global_pm_analytics

logger = logging.getLogger("aiforge.project_manager.planner")


class ProjectPlanner:
    """
    ProjectPlanner orchestrates the entire autonomous Project Management pipeline:
    Prompt -> PM Analysis -> Epics -> User Stories -> Task Breakdown -> DAG -> Sprints -> Progress -> Analytics.
    """

    def plan_project(self, prompt: str) -> Dict[str, Any]:
        pm_analysis = global_product_manager_agent.analyze_requirements(prompt)
        epics = global_epic_generator.generate_epics(prompt)
        stories = global_user_story_generator.generate_stories(epics)
        tasks = global_task_breakdown_engine.generate_tasks(stories)
        dag = global_project_dependency_graph.build_dag(tasks)
        sprints = global_sprint_planner.plan_sprints(tasks)
        progress = global_progress_tracker.track_progress(tasks)
        analytics = global_pm_analytics.calculate_analytics(tasks)

        logger.info(f"ProjectPlanner completed project plan for '{prompt[:30]}'")
        return {
            "prompt": prompt,
            "pm_analysis": pm_analysis,
            "epics": epics,
            "user_stories": stories,
            "tasks": tasks,
            "dependency_graph": dag,
            "sprints": sprints,
            "progress": progress,
            "analytics": analytics
        }


# Global ProjectPlanner Instance
global_project_planner = ProjectPlanner()
