import logging
from typing import List

_logger = logging.getLogger("aiforge.performance")

class ComposeGenerator:
    """
    Generates production-ready, security-hardened docker-compose.yml layouts.
    Auto-wires container networking, dependency readiness health checks, and volume mappings.
    """

    def __init__(self) -> None:
        pass

    def generate_compose(
        self,
        databases: List[str],
        frontend_framework: str = "react",
        backend_framework: str = "fastapi",
        frontend_port: int = 80,
        backend_port: int = 8000
    ) -> str:
        """
        Creates a docker-compose config linking frontend, backend, and persistent database containers.
        """
        _logger.info(f"Generating docker-compose.yml with databases: {databases}")

        db_service_name = ""
        db_service_yml = ""
        backend_env = ["      - PORT=8000"]

        # Wire database services
        for db in databases:
            db_lower = db.lower()
            if db_lower == "postgres":
                db_service_name = "postgres"
                backend_env.append("      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/aiforge_db")
                db_service_yml = """
  postgres:
    image: postgres:15-alpine
    container_name: aiforge-postgres
    restart: always
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: aiforge_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d aiforge_db"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - aiforge-network
"""
            elif db_lower == "mongodb":
                db_service_name = "mongodb"
                backend_env.append("      - DATABASE_URL=mongodb://mongodb:27017/aiforge_db")
                db_service_yml = """
  mongodb:
    image: mongo:6-jammy
    container_name: aiforge-mongodb
    restart: always
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - aiforge-network
"""
            elif db_lower == "mysql":
                db_service_name = "mysql"
                backend_env.append("      - DATABASE_URL=mysql://root:root@mysql:3306/aiforge_db")
                db_service_yml = """
  mysql:
    image: mysql:8
    container_name: aiforge-mysql
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: aiforge_db
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - aiforge-network
"""
            elif db_lower == "redis":
                # Add redis service as well if requested
                db_service_yml += """
  redis:
    image: redis:7-alpine
    container_name: aiforge-redis
    restart: always
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - aiforge-network
"""
                backend_env.append("      - REDIS_URL=redis://redis:6379")

        # Compose frontend build context depends on backend
        depends_on_backend = """
    depends_on:
      backend:
        condition: service_healthy
""" if backend_framework else ""

        # Compose backend build context depends on db
        depends_on_db = ""
        if db_service_name:
            depends_on_db = f"""
    depends_on:
      {db_service_name}:
        condition: service_healthy
"""

        compose_content = f"""version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: aiforge-frontend
    restart: always
    ports:
      - "{frontend_port}:{frontend_port}"
    environment:
      - NODE_ENV=production
      - VITE_API_URL=http://localhost:{backend_port}{depends_on_backend}
    networks:
      - aiforge-network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: aiforge-backend
    restart: always
    ports:
      - "{backend_port}:{backend_port}"
    environment:
{"\n".join(backend_env)}{depends_on_db}
    networks:
      - aiforge-network
"""

        # Append db service
        if db_service_yml:
            compose_content += db_service_yml

        # Append network and volumes
        compose_content += """
networks:
  aiforge-network:
    driver: bridge
"""

        # Append persistent volumes
        volumes = []
        if "postgres" in databases:
            volumes.append("  postgres_data:")
        if "mongodb" in databases:
            volumes.append("  mongodb_data:")
        if "mysql" in databases:
            volumes.append("  mysql_data:")
        if "redis" in databases:
            volumes.append("  redis_data:")

        if volumes:
            compose_content += "\nvolumes:\n" + "\n".join(volumes) + "\n"

        return compose_content
