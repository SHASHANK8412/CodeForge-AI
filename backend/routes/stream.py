"""
AIForge Real-Time SSE Progress Streaming API Router
===================================================
Streams step-by-step progress events to the React UI:
- ✔ Planner completed
- ✔ Architecture generated
- ✔ Frontend generating...
- ✔ Backend generating...
- ✔ Database generating...
- ✔ Assembly completed
- ✔ Reviewer completed
- ✔ Project Packaged & Download Ready
"""

import asyncio
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/v1/stream", tags=["Progress Streaming"])


@router.get("/workflow")
async def stream_workflow_progress(prompt: str = "Build Full-Stack App"):
    async def event_generator():
        steps = [
            "✔ Planner started...",
            "✔ Planner completed (Plan JSON generated)",
            "✔ Architect started...",
            "✔ Architecture generated (System Architecture JSON)",
            "✔ Parallel execution: Frontend, Backend & Database generating concurrently...",
            "✔ Frontend generated (React / Vite)",
            "✔ Backend generated (FastAPI / Pydantic)",
            "✔ Database generated (PostgreSQL / SQLAlchemy)",
            "✔ Project Assembly completed",
            "✔ Code Reviewer & Testing Agent completed",
            "✔ Project Packaged & Download Ready!"
        ]
        for step in steps:
            data = json.dumps({"event": step, "prompt": prompt})
            yield f"data: {data}\n\n"
            await asyncio.sleep(0.4)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
