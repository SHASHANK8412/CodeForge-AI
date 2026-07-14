from fastapi import APIRouter
from pydantic import BaseModel

from backend.graph.workflow import graph

router = APIRouter()


class Prompt(BaseModel):
    prompt: str
    session_id: str = "default"


@router.post("/generate")
def generate(data: Prompt):

    result = graph.invoke(
        {
            "prompt": data.prompt,
            "session_id": data.session_id,
        }
    )

    return {
        "generated_code": result.get("generated_code", ""),
        "reviewed_code": result.get("reviewed_code", ""),
        "testing_report": result.get("testing_report", ""),
        "explanation": result.get("explanation", ""),
    }