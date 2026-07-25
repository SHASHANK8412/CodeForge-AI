"""
AIForge V2 – Deployment Guide Generator
=======================================
Generates DEPLOYMENT_GUIDE.md covering Docker Compose, Nginx, Render, Railway, and production setups.
"""

class DeploymentDocsGenerator:

    def generate_deployment_docs(self, project_name: str) -> str:
        return f"""# Production Deployment Guide – {project_name}

## 1. Docker Compose Production Deployment

```bash
# Build and run containers in detached mode
docker-compose up -d --build

# View container status
docker-compose ps

# Monitor logs
docker-compose logs -f
```

## 2. Environment Configurations
Ensure production secrets are supplied in your CI/CD environment or `.env.production`.

## 3. Health Checks & Monitoring
- **Backend API Health Check**: `GET http://localhost:8000/health`
- **Database Connection Check**: Validated automatically via SQLAlchemy pool ping.
"""


global_deployment_docs = DeploymentDocsGenerator()
