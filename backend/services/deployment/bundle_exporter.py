import logging
import zipfile
from pathlib import Path
from typing import Dict, Any

_logger = logging.getLogger("aiforge.performance")

class BundleExporter:
    """
    Exports and packages all generated deployment infrastructure files (Docker files,
    cloud platform configs, env templates, CI/CD actions) and user manuals.
    """

    def __init__(self) -> None:
        pass

    def generate_deployment_guide(
        self,
        app_name: str,
        platform: str,
        reasoning: str,
        port: int = 8000
    ) -> str:
        """
        Generates a comprehensive Markdown deployment guide.
        """
        return f"""# Deployment Guide for {app_name}

This guide documents the procedures for packaging, configuring, and deploying the **{app_name}** application.

Based on your tech stack, we recommend deploying to **{platform}** because:
> *{reasoning}*

---

## 🐳 Option 1: Containerized Deployment via Docker

### Requirements
- Docker and Docker Compose installed locally.

### Local Development
To launch the complete application stack (frontend, backend, database) locally:
```bash
docker-compose up --build
```
This command builds the images, establishes bridging networks, and sets up persistent storage volumes.

### Port Mappings
- Frontend: `http://localhost:80`
- Backend API: `http://localhost:{port}`

---

## ☁ Option 2: Cloud Platform Deployments

### 1. Render Deployment (Recommended for Backend)
- A `render.yaml` blueprint has been generated at the project root.
- Connect your GitHub repository to Render.
- Create a new **Blueprint Route** on Render and point it to the repository. Render will auto-discover the services.

### 2. Vercel Deployment (Recommended for Frontend)
- Install the Vercel CLI: `npm i -g vercel`
- Run `vercel` in the `frontend` folder to trigger static hosting.
- Ensure your backend URL is set under the environment variables.

### 3. Railway Deployment
- Install the Railway CLI or connect your GitHub repository directly.
- Run `railway run` or push to your git branch.
- Add database services (Postgres, Mongo, etc.) directly in the Railway interface.

### 4. Fly.io Deployment
- Install the Fly CLI: `curl -L https://fly.io/install.sh | sh`
- Run `fly launch` to deploy using the pre-configured `fly.toml`.

---

## 🛠 Troubleshooting
- **Database Connection Failures**: Ensure database containers are healthy before backend containers boot. Docker-compose uses health checks to coordinate this sequence.
- **Port Conflict Errors**: If host ports are busy, map different host ports in `docker-compose.yml` (e.g. `8080:80`).
- **Environment Variable Errors**: Ensure you copy `.env.example` to `.env` and configure appropriate credentials.
"""

    def write_deployment_assets(
        self,
        project_path: Path,
        deployment_files: Dict[str, str],
        guide_content: str
    ) -> None:
        """
        Writes all generated deployment files to the project directory on disk.
        """
        _logger.info(f"Writing deployment files into project: {project_path}")
        
        # Write files (e.g. vercel.json, render.yaml, Dockerfiles, etc.)
        for filename, content in deployment_files.items():
            file_path = project_path / filename
            # Create subdirectories if needed (e.g., .github/workflows/)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

        # Write Deployment Guide
        guide_path = project_path / "docs" / "DEPLOYMENT.md"
        guide_path.parent.mkdir(parents=True, exist_ok=True)
        with open(guide_path, "w", encoding="utf-8") as f:
            f.write(guide_content)

        # Append deployment instructions to README.md
        readme_path = project_path / "README.md"
        instructions = f"\n\n## 🚀 Deployment & DevOps\nPlease refer to the [Deployment Guide](docs/DEPLOYMENT.md) for full instructions.\n"
        
        if readme_path.exists():
            with open(readme_path, "a", encoding="utf-8") as f:
                f.write(instructions)
        else:
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(f"# {project_path.name}\n" + instructions)

        _logger.info("Deployment files successfully written")
