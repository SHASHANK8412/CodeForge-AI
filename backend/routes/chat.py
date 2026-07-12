from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json
import asyncio
from time import perf_counter
from pydantic import BaseModel

from backend.graph.workflow import graph

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


@router.post("/chat")
async def chat(request: ChatRequest):

    started_at = perf_counter()

    result = await asyncio.to_thread(
        graph.invoke,
        {
            "prompt": request.message,
            "session_id": request.session_id,
        },
    )

    elapsed_ms = (perf_counter() - started_at) * 1000
    print(f"/chat completed in {elapsed_ms:.1f}ms")

    return {
        "plan": result["plan"],
        "architecture": result["architecture"],
        "response": result["response"],
        "session_id": request.session_id,
    }   


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    started_at = perf_counter()
    payload = {
        "prompt": request.message,
        "session_id": request.session_id,
    }

    def event_stream():
        for chunk in graph.stream(payload):
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

        elapsed_ms = (perf_counter() - started_at) * 1000
        yield f"data: {json.dumps({'type': 'timing', 'route': 'chat_stream', 'elapsed_ms': round(elapsed_ms, 1)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")