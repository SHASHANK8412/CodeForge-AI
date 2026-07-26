# FastAPI Production Guidelines

## Core Principles
1. **Asynchronous Handlers**: Use `async def` for I/O bound endpoints (database calls, HTTP requests).
2. **Pydantic Validation**: Use Pydantic `BaseModel` schemas for request payloads and response models (`response_model=ItemSchema`).
3. **Dependency Injection**: Leverage `Depends()` for database sessions, authentication, and configuration settings.
4. **CORS Middleware**: Enable `CORSMiddleware` with explicit allowed origins (`allow_origins=["*"]`).
5. **Uvicorn Server**: Deploy using Uvicorn ASGI server with standard worker processes (`uvicorn main:app --host 0.0.0.0 --port 8000`).
