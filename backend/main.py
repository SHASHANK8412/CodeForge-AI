from fastapi import FastAPI
from backend.routes.generate import router

app = FastAPI(
    title="AIForge",
    description="Multi-Agent AI Coding Assistant",
    version="0.1.0"
)

app.include_router(router)


@app.get("/")
def home():
    return {"message": "AIForge API is running 🚀"}