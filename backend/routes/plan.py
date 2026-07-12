from fastapi import APIRouter
import asyncio
from time import perf_counter
from pydantic import BaseModel

from backend.graph.workflow import graph


router = APIRouter()


class PlanRequest(BaseModel):
    message: str
    session_id: str = "default"


@router.post("/plan")
async def generate_plan(request: PlanRequest):

    started_at = perf_counter()

    result = await asyncio.to_thread(
        graph.invoke,
        {
            "prompt": request.message,
            "session_id": request.session_id,
        },
    )

    elapsed_ms = (perf_counter() - started_at) * 1000
    print(f"/plan completed in {elapsed_ms:.1f}ms")

    return {
        "plan": result["plan"],
        "architecture": result["architecture"],
        "session_id": request.session_id,
    }