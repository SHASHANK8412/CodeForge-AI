from fastapi import APIRouter
from pydantic import BaseModel

try:
    from ..agents.router_agent import RouterAgent
except ImportError:
    from agents.router_agent import RouterAgent

router = APIRouter()

router_agent = RouterAgent()


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
def chat(request: ChatRequest):
    print("=" * 50)
    print("Incoming:", request.message)

    response = router_agent.route(request.message)

    print("Returned:", response)
    print("Type:", type(response))
    print("=" * 50)

    return {
        "response": response
    }