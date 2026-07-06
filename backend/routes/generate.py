from fastapi import APIRouter
from pydantic import BaseModel

from backend.agents.factory import AgentFactory

router = APIRouter()


class Prompt(BaseModel):
    agent: str
    prompt: str


@router.post("/generate")
def generate(data: Prompt):

    agent = AgentFactory.get_agent(data.agent)

    response = agent.run(data.prompt)

    return {
        "response": response
    }