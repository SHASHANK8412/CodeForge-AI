import logging
from typing import Dict, Any

_logger = logging.getLogger("aiforge.performance")

class DockerGenerator:
    """
    Generates production-grade, optimized, multi-stage Dockerfiles for various 
    frontend and backend frameworks (React, Vue, Next.js, FastAPI, Django, Flask, Express, etc.).
    """

    def __init__(self) -> None:
        pass

    def generate_frontend_dockerfile(self, framework: str = "react", port: int = 80) -> str:
        """
        Creates a production-ready, multi-stage frontend Dockerfile.
        """
        framework = framework.lower()
        _logger.info(f"Generating optimized frontend Dockerfile for framework: {framework} on port: {port}")

        if framework in ["next.js", "nextjs"]:
            # Optimized production multi-stage build for Next.js (SSR/Static)
            return f"""# Next.js multi-stage production Dockerfile
FROM node:20-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE {port}
ENV PORT={port}
CMD ["node", "server.js"]
"""

        # Fallback to standard Single Page Application serving via Nginx (React, Vue, Angular)
        return f"""# SPA (React/Vue/Angular) multi-stage production Dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.25-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
# Custom Nginx configuration routing fallback
RUN echo 'server {{ listen {port}; location / {{ root /usr/share/nginx/html; index index.html; try_files $uri $uri/ /index.html; }} }}' > /etc/nginx/conf.d/default.conf
EXPOSE {port}
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \\
  CMD wget --quiet --tries=1 --spider http://localhost:{port}/ || exit 1
CMD ["nginx", "-g", "daemon off;"]
"""

    def generate_backend_dockerfile(self, framework: str = "fastapi", port: int = 8000) -> str:
        """
        Creates a production-ready, security-hardened backend Dockerfile with build caching.
        """
        framework = framework.lower()
        _logger.info(f"Generating optimized backend Dockerfile for framework: {framework} on port: {port}")

        if framework in ["spring boot", "springboot", "java"]:
            return f"""# Java/Spring Boot production Dockerfile
FROM maven:3.9-eclipse-temurin-17-alpine AS build
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn clean package -DskipTests

FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
RUN addgroup -S spring && adduser -S spring -G spring
USER spring
COPY --from=build /app/target/*.jar app.jar
EXPOSE {port}
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \\
  CMD nc -z localhost {port} || exit 1
ENTRYPOINT ["java", "-jar", "app.jar"]
"""

        if framework == "express":
            return f"""# Node.js/Express production Dockerfile
FROM node:20-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY package.json package-lock.json* ./
RUN npm ci --only=production
COPY . .
RUN chown -R node:node /app
USER node
EXPOSE {port}
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \\
  CMD node -e "require('http').get('http://localhost:{port}/health', (r) => r.statusCode === 200 ? process.exit(0) : process.exit(1))" || exit 1
CMD ["node", "src/index.js"]
"""

        # Python frameworks (FastAPI, Django, Flask)
        startup_cmd = "uvicorn backend.main:app"
        if framework == "django":
            startup_cmd = "gunicorn core.wsgi:application"
        elif framework == "flask":
            startup_cmd = "gunicorn app:app"

        return f"""# Python/FastAPI/Django/Flask production Dockerfile
FROM python:3.11-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    libpq-dev \\
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \\
    libpq5 \\
    netcat-openbsd \\
    && rm -rf /var/lib/apt/lists/*
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE {port}
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \\
  CMD nc -z localhost {port} || exit 1
CMD ["python", "-m", "{startup_cmd.split()[0]}", "{startup_cmd.split()[1]}", "--host", "0.0.0.0", "--port", "{port}"]
"""

    def generate_dockerignore(self) -> str:
        """
        Returns a robust, standard .dockerignore configuration to prevent cache pollution.
        """
        return """# AIForge Docker Ignore Rules
.git
.github
node_modules
dist
build
.next
.venv
venv
env
__pycache__
*.pyc
*.pyo
*.pyd
.pytest_cache
.coverage
htmlcov
.env
.env.local
db.sqlite3
data/
*.zip
*.tar.gz
Dockerfile
docker-compose.yml
"""
