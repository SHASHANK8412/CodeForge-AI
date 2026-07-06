from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.llm import generate_response

router = APIRouter()


class Prompt(BaseModel):
    prompt: str


@router.post("/generate")
def generate(data: Prompt):
    answer = generate_response(data.prompt)
    return {"response": answer}