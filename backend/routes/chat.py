from fastapi import APIRouter
from pydantic import BaseModel

from backend.graph.workflow import graph

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


@router.post("/chat")
def chat(request: ChatRequest):

    result = graph.invoke(
        {
            "prompt": request.message,
            "session_id": request.session_id,
        }
    )

    return {
        "plan": result["plan"],
        "architecture": result["architecture"],
        "response": result["response"],
        "session_id": request.session_id,
    }   