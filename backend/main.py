from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from time import perf_counter
from pydantic import BaseModel

from backend.graph.workflow import graph
from backend.routes.chat import router as chat_router
from backend.routes.rag import legacy_router as rag_legacy_router
from backend.routes.rag import router as rag_router
from backend.routes.plan import router as plan_router
from backend.routes.memory import router as memory_router

app = FastAPI(
    title="AIForge API",
    description="Multi-Agent AI Software Engineer Backend",
    version="1.0.0"
)

# Allow frontend (React/Vite) to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

def register_routers() -> None:
    app.include_router(chat_router)
    app.include_router(rag_router)
    app.include_router(rag_legacy_router)
    app.include_router(plan_router)
    app.include_router(memory_router)


register_routers()


class PromptRequest(BaseModel):
    prompt: str
    session_id: str = "default"


@app.get("/")
def home():
    return {
        "status": "running",
        "project": "AIForge",
        "message": "🚀 AIForge Backend is running successfully!"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/generate")
async def generate(request: PromptRequest):
    started_at = perf_counter()
    try:
        result = await asyncio.to_thread(
            graph.invoke,
            {
                "prompt": request.prompt,
                "session_id": request.session_id,
            },
        )

        elapsed_ms = (perf_counter() - started_at) * 1000
        print(f"/generate completed in {elapsed_ms:.1f}ms")

        return {
            "generated_code": result.get("generated_code", ""),
            "reviewed_code": result.get("reviewed_code", ""),
            "testing_report": result.get("testing_report", ""),
            "explanation": result.get("explanation", ""),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )