"""
AIForge V2 – FastAPI Middleware Generator
=========================================
Generates CORS, Request ID Tracking, Response Timing, and Exception Handler middlewares.
"""

from typing import List
from v2.agents.backend.models import BackendMiddlewareSpec


class FastAPIBackendMiddlewareGenerator:

    def generate_default_middlewares(self) -> List[BackendMiddlewareSpec]:
        return [
            BackendMiddlewareSpec(
                middleware_name="CORSMiddleware",
                purpose="Allows cross-origin requests from frontend SPA clients",
                code_content="""from fastapi.middleware.cors import CORSMiddleware

def setup_cors(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
"""
            ),
            BackendMiddlewareSpec(
                middleware_name="RequestTimingMiddleware",
                purpose="Logs request execution time and assigns unique Request ID",
                code_content="""import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

class RequestTimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        req_id = str(uuid.uuid4())
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = req_id
        response.headers["X-Response-Time-MS"] = f"{elapsed_ms:.2f}"
        return response
"""
            )
        ]


global_middleware_generator = FastAPIBackendMiddlewareGenerator()
