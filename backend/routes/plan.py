from time import perf_counter

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class PlanRequest(BaseModel):
    message: str
    session_id: str = "default"


@router.post("/plan")
async def generate_plan(request: PlanRequest):
    """
    Plan and architecture for a request: runs only the planner and architect stages of the
    generation pipeline (it used to run the whole 14-stage project build to return these two).
    """
    from backend.graph.parallel_workflow import architect_node, planner_node

    started_at = perf_counter()
    state = {
        "prompt": request.message,
        "user_prompt": request.message,
        "project_id": request.session_id,
        "session_id": request.session_id,
        "generation_id": request.session_id,
    }
    state.update(await planner_node(state))
    state.update(await architect_node(state))

    return {
        "plan": state.get("plan"),
        "architecture": state.get("architecture"),
        "session_id": request.session_id,
        "elapsed_ms": round((perf_counter() - started_at) * 1000, 1),
    }
