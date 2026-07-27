import logging
from langgraph.graph import StateGraph, END, START

from backend.graph.state import WorkflowState
from backend.graph.nodes import (
    planner_node,
    project_manager_node,
    architect_node,
    frontend_node,
    backend_node,
    database_node,
    reviewer_node,
    testing_node,
    documentation_node,
    export_node,
    learning_enricher_node,
    learning_updater_node,
)
from backend.graph.conditions import (
    should_retry_planner,
    should_refine_code,
    should_retry_reviewer,
)

logger = logging.getLogger("aiforge.graph.workflow")


def create_workflow_graph():
    """
    Constructs the LangGraph autonomous multi-agent software engineering workflow graph:
    START -> Planner -> Project Manager -> Architect -> Frontend -> Backend -> Database -> Reviewer -> Testing -> Documentation -> Export -> END
    """
    workflow = StateGraph(WorkflowState)

    # 1. Add Agent Nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("learning_enricher", learning_enricher_node)
    workflow.add_node("project_manager", project_manager_node)
    workflow.add_node("architect", architect_node)
    workflow.add_node("frontend", frontend_node)
    workflow.add_node("backend", backend_node)
    workflow.add_node("database", database_node)
    workflow.add_node("reviewer", reviewer_node)
    workflow.add_node("testing", testing_node)
    workflow.add_node("documentation", documentation_node)
    workflow.add_node("learning_updater", learning_updater_node)
    workflow.add_node("export", export_node)

    # 2. Add Sequential Edges
    workflow.add_edge(START, "planner")

    workflow.add_conditional_edges(
        "planner",
        should_retry_planner,
        {
            "planner": "planner",
            "architect": "learning_enricher"
        }
    )

    workflow.add_edge("learning_enricher", "project_manager")
    workflow.add_edge("project_manager", "architect")

    workflow.add_edge("architect", "frontend")
    workflow.add_edge("frontend", "backend")
    workflow.add_edge("backend", "database")
    workflow.add_edge("database", "reviewer")

    workflow.add_conditional_edges(
        "reviewer",
        should_refine_code,
        {
            "frontend": "frontend",
            "testing": "testing"
        }
    )

    workflow.add_conditional_edges(
        "testing",
        should_retry_reviewer,
        {
            "reviewer": "reviewer",
            "documentation": "documentation"
        }
    )

    workflow.add_edge("documentation", "learning_updater")
    workflow.add_edge("learning_updater", "export")
    workflow.add_edge("export", END)

    compiled_graph = workflow.compile()
    logger.info("Compiled LangGraph Day 16 Autonomous Workflow Graph successfully.")
    return compiled_graph


# Global compiled workflow graph
graph = create_workflow_graph()