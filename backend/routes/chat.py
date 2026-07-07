from fastapi import APIRouter
from pydantic import BaseModel

from backend.agents.router_agent import RouterAgent

router = APIRouter()

router_agent = RouterAgent()


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
def chat(request: ChatRequest):

    response = router_agent.route(request.message)

    return {
        "response": response
    }