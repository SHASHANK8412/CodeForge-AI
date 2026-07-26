import logging
from typing import Dict, Any

logger = logging.getLogger("aiforge.deployment.compose_generator")


class ComposeGenerator:
    """
    ComposeGenerator constructs multi-container docker-compose.yml with
    frontend, backend, postgres, redis, environment variables, and health checks.
    """

    def generate_compose_yml(self, project_name: str = "app") -> str:
        safe_name = project_name.lower().replace(" ", "_")
        return f"""version: "3.9"

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: {safe_name}_backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/app_db
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=production_secret_key_aiforge_v2
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    networks:
      - app_net

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: {safe_name}_frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    networks:
      - app_net

  postgres:
    image: postgres:16-alpine
    container_name: {safe_name}_postgres
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=app_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - app_net

  redis:
    image: redis:7-alpine
    container_name: {safe_name}_redis
    ports:
      - "6379:6379"
    networks:
      - app_net

networks:
  app_net:
    driver: bridge

volumes:
  postgres_data:
"""


# Global ComposeGenerator Instance
global_compose_generator = ComposeGenerator()
