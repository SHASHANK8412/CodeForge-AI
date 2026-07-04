from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {
        "project": "AIForge",
        "message": "Welcome to AIForge!"
    }