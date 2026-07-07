from fastapi import APIRouter
from pydantic import BaseModel

from backend.agents.router_agent import RouterAgent

router = APIRouter()


class Prompt(BaseModel):
    prompt: str


@router.post("/generate")
def generate(data: Prompt):

    router_agent = RouterAgent()

    agent = router_agent.get_agent(data.prompt)

    response = agent.run(data.prompt)

    return {
        "response": response
    }