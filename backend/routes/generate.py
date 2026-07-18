from fastapi import APIRouter
from pydantic import BaseModel

from backend.graph.parallel_workflow import parallel_graph as project_graph

router = APIRouter()


class Prompt(BaseModel):
    prompt: str
    session_id: str = "default"


@router.post("/generate")
async def generate(data: Prompt):

    result = await project_graph.ainvoke(
        {
            "prompt": data.prompt,
            "user_prompt": data.prompt,
            "session_id": data.session_id,
        }
    )

    return {
        "plan": result.get("plan", ""),
        "architecture": result.get("architecture", ""),
        "frontend": result.get("frontend", ""),
        "backend": result.get("backend", ""),
        "database": result.get("database", ""),
        "review": result.get("review", ""),
        "tests": result.get("tests", ""),
        "documentation": result.get("documentation", ""),

        # Preserve existing functionality
        "generated_code": result.get("backend", ""),
        "reviewed_code": result.get("review", ""),
        "testing_report": result.get("tests", ""),
        "explanation": result.get("documentation", ""),
    }