from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes.chat import router
from backend.routes.plan import router as planner_router

app = FastAPI(
    title="AIForge",
    description="Multi-Agent AI Coding Assistant",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(planner_router)

@app.get("/")
def home():
    return {"message": "AIForge API is running 🚀"}

