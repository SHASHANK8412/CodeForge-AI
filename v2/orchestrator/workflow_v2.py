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
    report_dict = report.dict()

    return {
        "planner_output": report.json(),
        "messages": [{"sender": "planner", "event": "PLANNING_BLUEPRINT_COMPLETED", "payload": {"fr_count": len(report.functional_requirements), "stories_count": len(report.user_stories)}}]
    }


# ---------------- Graph Construction ---------------- #

builder = StateGraph(ProjectStateV2)

builder.add_node("ceo", ceo_node)
builder.add_node("manager", manager_node)
builder.add_node("planner", planner_node)

builder.add_edge(START, "ceo")
builder.add_edge("ceo", "manager")
builder.add_edge("manager", "planner")
builder.add_edge("planner", END)

workflow_v2_graph = builder.compile()
