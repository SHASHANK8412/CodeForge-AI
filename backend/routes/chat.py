from fastapi import APIRouter
from pydantic import BaseModel

from backend.graph.workflow import graph

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
def chat(request: ChatRequest):

    result = graph.invoke(
        {
            "prompt": request.message
        }
    )

    return {
        "plan": result["plan"],
        "architecture": result["architecture"],
        "response": result["response"]
    }   