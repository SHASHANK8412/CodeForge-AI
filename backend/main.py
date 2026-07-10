from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from .graph.workflow import graph
except ImportError:
    from graph.workflow import graph

app = FastAPI(
    title="AIForge API",
    description="Multi-Agent AI Software Engineer Backend",
    version="1.0.0"
)

# Allow frontend (React/Vite) to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PromptRequest(BaseModel):
    prompt: str


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
def generate(request: PromptRequest):
    try:
        result = graph.invoke(
            {
                "prompt": request.prompt,
                "response": ""
            }
        )

        return {
            "success": True,
            "response": result["response"]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )