from fastapi import APIRouter
from pydantic import BaseModel

from backend.agents.factory import AgentFactory


router = APIRouter()


class PlanRequest(BaseModel):
    message: str


@router.post("/plan")
def generate_plan(request: PlanRequest):

    planner = AgentFactory.create_agent("planner")

    response = planner.run(request.message)

    return {
        "plan": response
    }