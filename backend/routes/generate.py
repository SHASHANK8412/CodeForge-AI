from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field
import time
import uuid

from backend.services.generation_service import global_generation_pipeline

router = APIRouter()


class Prompt(BaseModel):
    prompt: str
    session_id: str = "default"


class GenerateProjectPayload(BaseModel):
    project_name: str = Field(default="My AIForge Project")
    description: str = Field(description="User project requirements")
    frontend: str = Field(default="React")
    backend: str = Field(default="FastAPI")
    database: str = Field(default="PostgreSQL")
    styling: str = Field(default="Tailwind CSS")
    authentication: bool = Field(default=True)
    testing: bool = Field(default=True)
    documentation: bool = Field(default=True)
    docker: bool = Field(default=True)
    security_review: bool = Field(default=True)
    local_llm: bool = Field(default=True)
    model: str = Field(default="qwen2.5-coder")
    rag: bool = Field(default=True)
    code_review: bool = Field(default=True)
    auto_repair: bool = Field(default=True)


# Status, cancel and stream for generations are served by backend/generation/routes.py (the real
# pipeline); this module used to register the same paths with a made-up "completed" status.
GENERATIONS_DB: dict[str, dict] = {}


@router.post("/generate")
@router.post("/api/generate")
@router.post("/api/project/generate")
async def generate(data: GenerateProjectPayload | Prompt):
    if isinstance(data, GenerateProjectPayload):
        full_prompt = f"Project Name: {data.project_name}. Stack: {data.frontend}, {data.backend}, {data.database}, {data.styling}. Description: {data.description}"
        gen_id = f"aiforge-{uuid.uuid4().hex[:8]}"

        # Legacy synchronous path. The UI uses POST /api/generations (the LangGraph pipeline);
        # record only what this call actually produced.
        gen_result = await global_generation_pipeline.generate(
            user_prompt=full_prompt,
            session_id=gen_id
        )

        safe_name = "".join([c if c.isalnum() or c in " -_" else "_" for c in data.project_name]).strip()

        GENERATIONS_DB[gen_id] = {
            "generation_id": gen_id,
            "project_name": data.project_name,
            "stack": {
                "frontend": data.frontend,
                "backend": data.backend,
                "database": data.database,
                "styling": data.styling
            },
            "status": "COMPLETED" if gen_result.validation_passed else "COMPLETED_WITH_WARNINGS",
            "progress": 100,
            "quality_score": gen_result.quality_score,
            "validation_passed": gen_result.validation_passed,
        }

        return {
            "success": True,
            "generation_id": gen_id,
            "project_name": data.project_name,
            "location": f"generated_projects/{safe_name}",
            "quality_score": gen_result.quality_score,
            "validation_passed": gen_result.validation_passed
        }
    else:
        gen_result = await global_generation_pipeline.generate(
            user_prompt=data.prompt,
            session_id=data.session_id
        )

        return {
            "plan": gen_result.plan_text,
            "architecture": gen_result.arch_text,
            "frontend": gen_result.files_map.get("frontend/src/App.jsx", ""),
            "backend": gen_result.files_map.get("backend/main.py", ""),
            "database": gen_result.files_map.get("backend/models.py", ""),
            # This synchronous path does not review or test the code, so those fields are empty
            # (they used to say "15/15 Quality Gates Passed" / "Pytest Suite Generated").
            "review": None,
            "tests": None,
            "documentation": gen_result.response,

            # Preserve existing contract fields
            "generated_code": gen_result.files_map.get("backend/main.py", gen_result.response),
            "reviewed_code": None,
            "testing_report": None,
            "explanation": gen_result.response,
            "intent": gen_result.intent,
            "agent": gen_result.agent,
            "quality_score": gen_result.quality_score,
            "validation_passed": gen_result.validation_passed
        }
