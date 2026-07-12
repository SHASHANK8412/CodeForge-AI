from fastapi import APIRouter
from pydantic import BaseModel

from backend.graph.workflow import graph


router = APIRouter()


class PlanRequest(BaseModel):
    message: str
    session_id: str = "default"


@router.post("/plan")
def generate_plan(request: PlanRequest):

    result = graph.invoke(
        {
            "prompt": request.message,
            "session_id": request.session_id,
        }
    )

    return {
        "plan": result["plan"],
        "architecture": result["architecture"],
        "session_id": request.session_id,
    }