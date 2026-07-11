from fastapi import APIRouter
from pydantic import BaseModel

try:
    from ..graph.workflow import graph
except ImportError:
    from graph.workflow import graph

router = APIRouter()


class Prompt(BaseModel):
    prompt: str


@router.post("/generate")
def generate(data: Prompt):

    result = graph.invoke(
        {
            "prompt": data.prompt
        }
    )

    return {
        "plan": result["plan"],
        "response": result["response"]
    }