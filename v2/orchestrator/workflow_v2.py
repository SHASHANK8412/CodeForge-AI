"""
AIForge V2 – Day 2 LangGraph Autonomous Orchestrator Workflow
=============================================================
Graph: START -> CEO Agent -> Project Manager Agent -> Planner Agent -> END
"""

import logging
from typing import Dict, Any, List, TypedDict, Optional
from typing_extensions import Annotated
from langgraph.graph import StateGraph, START, END

from v2.agents.ceo.agent import global_ceo_agent_v2
from v2.agents.manager.agent import global_manager_agent_v2
from backend.agents.planner_agent import PlannerAgent

_logger = logging.getLogger("aiforge.v2.orchestrator")
planner_agent = PlannerAgent()


def _merge_list(left: list, right: list) -> list:
    return left + right


class ProjectStateV2(TypedDict):
    user_prompt: str
    ceo_evaluation: Optional[Dict[str, Any]]
    tasks: Optional[List[Dict[str, Any]]]
    planner_output: Optional[str]
    architect_output: Optional[str]
    frontend_output: Optional[str]
    backend_output: Optional[str]
    database_output: Optional[str]
    reviewer_output: Optional[str]
    testing_output: Optional[str]
    messages: Annotated[List[Dict[str, Any]], _merge_list]


# ---------------- Node Implementations ---------------- #

def ceo_node(state: ProjectStateV2) -> Dict[str, Any]:
    prompt = state["user_prompt"]
    _logger.info(f"LangGraph Workflow V2: CEO Node executing for prompt '{prompt[:60]}...'")

    eval_result = global_ceo_agent_v2.evaluate_project(prompt)
    eval_dict = eval_result.dict()

    return {
        "ceo_evaluation": eval_dict,
        "messages": [{"sender": "ceo", "event": "CEO_EVALUATION_COMPLETED", "payload": eval_dict}]
    }


def manager_node(state: ProjectStateV2) -> Dict[str, Any]:
    _logger.info("LangGraph Workflow V2: Project Manager Node executing...")
    ceo_eval = state.get("ceo_evaluation", {})

    from v2.agents.ceo.models import CEOProjectEvaluation
    eval_obj = CEOProjectEvaluation(**ceo_eval)

    task_items = global_manager_agent_v2.generate_task_breakdown(eval_obj)
    tasks_dicts = [t.dict() for t in task_items]

    return {
        "tasks": tasks_dicts,
        "messages": [{"sender": "manager", "event": "TASKS_BREAKDOWN_GENERATED", "payload": {"count": len(tasks_dicts)}}]
    }


def planner_node(state: ProjectStateV2) -> Dict[str, Any]:
    _logger.info("LangGraph Workflow V2: Planner Node executing...")
    prompt = state["user_prompt"]
    from v2.agents.planner.planner_service import global_planner_service

    report = global_planner_service.analyze_project(prompt)

    return {
        "planner_output": report.json(),
        "messages": [{"sender": "planner", "event": "PLANNING_BLUEPRINT_COMPLETED", "payload": {"fr_count": len(report.functional_requirements), "stories_count": len(report.user_stories)}}]
    }


def architect_node(state: ProjectStateV2) -> Dict[str, Any]:
    _logger.info("LangGraph Workflow V2: Architect Node executing...")
    prompt = state["user_prompt"]
    from v2.agents.architect.agent import global_architect_agent_v2

    report = global_architect_agent_v2.design_architecture(prompt)

    return {
        "architect_output": report.json(),
        "messages": [{"sender": "architect", "event": "ARCHITECTURE_DESIGN_COMPLETED", "payload": {"apis_count": len(report.apis), "tables_count": len(report.database.tables)}}]
    }


def frontend_node(state: ProjectStateV2) -> Dict[str, Any]:
    _logger.info("LangGraph Workflow V2: Frontend Node executing...")
    prompt = state["user_prompt"]
    from v2.agents.frontend.agent import global_frontend_agent_v2

    report = global_frontend_agent_v2.generate_frontend(prompt)

    return {
        "frontend_output": report.json(),
        "messages": [{"sender": "frontend", "event": "FRONTEND_APPLICATION_GENERATED", "payload": {"components_count": len(report.components), "pages_count": len(report.pages)}}]
    }


def backend_node(state: ProjectStateV2) -> Dict[str, Any]:
    _logger.info("LangGraph Workflow V2: Backend Node executing...")
    prompt = state["user_prompt"]
    from v2.agents.backend.agent import global_backend_agent_v2

    report = global_backend_agent_v2.generate_backend(prompt)

    return {
        "backend_output": report.json(),
        "messages": [{"sender": "backend", "event": "BACKEND_APPLICATION_GENERATED", "payload": {"apis_count": len(report.apis), "services_count": len(report.services)}}]
    }


def database_node(state: ProjectStateV2) -> Dict[str, Any]:
    _logger.info("LangGraph Workflow V2: Database Node executing...")
    prompt = state["user_prompt"]
    from v2.agents.database.agent import global_database_agent_v2

    report = global_database_agent_v2.generate_database(prompt)

    return {
        "database_output": report.json(),
        "messages": [{"sender": "database", "event": "DATABASE_PERSISTENCE_GENERATED", "payload": {"tables_count": len(report.tables), "indexes_count": len(report.indexes)}}]
    }


def reviewer_node(state: ProjectStateV2) -> Dict[str, Any]:
    _logger.info("LangGraph Workflow V2: Reviewer Node executing...")
    prompt = state["user_prompt"]
    from v2.agents.reviewer.agent import global_reviewer_agent_v2

    report = global_reviewer_agent_v2.review_project(prompt)

    return {
        "reviewer_output": report.json(),
        "messages": [{"sender": "reviewer", "event": "PROJECT_CODE_REVIEW_COMPLETED", "payload": {"overall_score": report.overall_score, "issues_count": len(report.issues)}}]
    }


def testing_node(state: ProjectStateV2) -> Dict[str, Any]:
    _logger.info("LangGraph Workflow V2: Testing Node executing...")
    prompt = state["user_prompt"]
    from v2.agents.testing.agent import global_testing_agent_v2

    report = global_testing_agent_v2.generate_tests(prompt)

    return {
        "testing_output": report.json(),
        "messages": [{"sender": "testing", "event": "FULLSTACK_TESTING_COMPLETED", "payload": {"passed_count": report.passed_count, "coverage_pct": report.coverage.overall_coverage_pct}}]
    }


# ---------------- Graph Construction ---------------- #

builder = StateGraph(ProjectStateV2)

builder.add_node("ceo", ceo_node)
builder.add_node("manager", manager_node)
builder.add_node("planner", planner_node)
builder.add_node("architect", architect_node)
builder.add_node("frontend", frontend_node)
builder.add_node("backend", backend_node)
builder.add_node("database", database_node)
builder.add_node("reviewer", reviewer_node)
builder.add_node("testing", testing_node)

builder.add_edge(START, "ceo")
builder.add_edge("ceo", "manager")
builder.add_edge("manager", "planner")
builder.add_edge("planner", "architect")
builder.add_edge("architect", "frontend")
builder.add_edge("frontend", "backend")
builder.add_edge("backend", "database")
builder.add_edge("database", "reviewer")
builder.add_edge("reviewer", "testing")
builder.add_edge("testing", END)

workflow_v2_graph = builder.compile()
