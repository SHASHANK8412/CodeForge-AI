import logging
from backend.graph.state import WorkflowState

logger = logging.getLogger("aiforge.graph.conditions")


def should_retry_planner(state: WorkflowState) -> str:
    """Routing condition after PlannerNode."""
    retries = state.setdefault("retry_count", {}).get("planner", 0)
    plan = state.get("plan")
    if (not plan or "error" in plan) and retries < 3:
        state["retry_count"]["planner"] = retries + 1
        logger.info(f"Planner retry triggered ({retries + 1}/3)")
        return "planner"
    return "architect"


def should_refine_code(state: WorkflowState) -> str:
    """Routing condition after ReviewerNode."""
    retries = state.setdefault("retry_count", {}).get("reviewer", 0)
    review = state.get("review", {})
    score = review.get("score", 100) if isinstance(review, dict) else 100

    if score < 70 and retries < 3:
        state["retry_count"]["reviewer"] = retries + 1
        logger.info(f"Review score {score} < 70; returning to Frontend/Backend refinement ({retries + 1}/3)")
        return "frontend"
    return "testing"


def should_retry_reviewer(state: WorkflowState) -> str:
    """Routing condition after TestingNode."""
    retries = state.setdefault("retry_count", {}).get("testing", 0)
    tests = state.get("tests", {})

    if not tests and retries < 3:
        state["retry_count"]["testing"] = retries + 1
        logger.info(f"Testing failed; returning to ReviewerNode ({retries + 1}/3)")
        return "reviewer"
    return "documentation"
