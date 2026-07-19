import logging
from backend.config import DEFAULT_PYTHON_VERSION, DEFAULT_NODE_VERSION

_logger = logging.getLogger("aiforge.performance")


class DockerGenerator:
    """
    Generates standard, production-ready Dockerfiles for both frontend (Node/Nginx)
    and backend (Python/Uvicorn) applications.
    """

    def __init__(self) -> None:
        pass

    def generate_backend_dockerfile(self, python_version: str = DEFAULT_PYTHON_VERSION) -> str:
        """
        Creates a production-ready Python Dockerfile for the FastAPI backend.
        """
        _logger.info("Generating backend Dockerfile...")
        dockerfile = f"""# Production Dockerfile for FastAPI backend
FROM python:{python_version}

# Prevent writing pyc files and buffer output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install native compilation dependencies for C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    && apt-get clean \\
    && rm -rf /var/lib/apt/lists/*

# Copy and install python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source directory
COPY . .

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
        _logger.info("Backend Dockerfile generated")
        return dockerfile

    def generate_frontend_dockerfile(self, node_version: str = DEFAULT_NODE_VERSION) -> str:
        """
        Creates a multi-stage build Node.js and Nginx Dockerfile for the React frontend.
        """
        _logger.info("Generating frontend Dockerfile...")
        dockerfile = f"""# Multi-stage production Dockerfile for Vite/React frontend
# Stage 1: Build source assets
FROM node:{node_version} AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .
RUN npm run build

# Stage 2: Serve built assets using Nginx
FROM nginx:alpine

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
"""
        _logger.info("Frontend Dockerfile generated")
        return dockerfile
