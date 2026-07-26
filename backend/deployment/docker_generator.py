import logging
from typing import Dict, Any

logger = logging.getLogger("aiforge.deployment.docker_generator")


class DockerGenerator:
    """
    DockerGenerator builds production-grade Dockerfiles for Python/FastAPI backends
    and Node/React frontends.
    """

    def generate_backend_dockerfile(self) -> str:
        return (
            "FROM python:3.12-slim\n\n"
            "WORKDIR /app\n\n"
            "RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*\n\n"
            "COPY requirements.txt .\n"
            "RUN pip install --no-cache-dir -r requirements.txt\n\n"
            "COPY . .\n\n"
            "EXPOSE 8000\n"
            "HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:8000/health || exit 1\n\n"
            'CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]\n'
        )

    def generate_frontend_dockerfile(self) -> str:
        return (
            "FROM node:20-alpine AS builder\n\n"
            "WORKDIR /app\n\n"
            "COPY package*.json .\n"
            "RUN npm ci\n\n"
            "COPY . .\n"
            "RUN npm run build\n\n"
            "FROM nginx:alpine\n"
            "COPY --from=builder /app/dist /usr/share/nginx/html\n"
            "EXPOSE 80\n"
            'CMD ["nginx", "-g", "daemon off;"]\n'
        )


# Global DockerGenerator Instance
global_docker_generator = DockerGenerator()
