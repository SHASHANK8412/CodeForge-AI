import re
import logging
from typing import Dict, List, Set, Any
from backend.services.deployment.deployment_report import DeploymentReadinessReport

_logger = logging.getLogger("aiforge.performance")

class DeploymentValidator:
    """
    Validates Dockerfiles, compose setups, dependencies, env matching, port collisions,
    and returns a detailed diagnostics readiness report.
    """

    def __init__(self) -> None:
        pass

    def validate(
        self,
        project_name: str,
        state: Dict[str, Any],
        deployment_files: Dict[str, str],
        env_vars: Dict[str, str],
        frameworks: Dict[str, str],
        databases: List[str]
    ) -> DeploymentReadinessReport:
        """
        Runs comprehensive analysis over generated code and configuration files.
        """
        _logger.info(f"Running deployment validation suite for: {project_name}")
        
        errors: List[str] = []
        warnings: List[str] = []
        suggestions: List[str] = []

        # 1. Port Collision check
        frontend_port = 80
        backend_port = 8000
        
        # Read ports from dockerfiles if parsed or config
        for filename, content in deployment_files.items():
            if "Dockerfile" in filename:
                for line in content.splitlines():
                    if line.strip().upper().startswith("EXPOSE"):
                        parts = line.strip().split()
                        if len(parts) > 1:
                            try:
                                exp_port = int(parts[1])
                                if "frontend" in filename:
                                    frontend_port = exp_port
                                else:
                                    backend_port = exp_port
                            except ValueError:
                                pass

        if frontend_port == backend_port:
            errors.append(f"Port collision detected: Both frontend and backend expose port {frontend_port}.")
        else:
            suggestions.append(f"Frontend is bound to port {frontend_port} and Backend to {backend_port}.")

        # 2. Dockerfile Syntactic Validation
        for filename, content in deployment_files.items():
            if "Dockerfile" in filename:
                lines = [l.strip() for l in content.splitlines() if l.strip() and not l.strip().startswith("#")]
                has_from = any(l.upper().startswith("FROM") for l in lines)
                has_cmd_or_entry = any(l.upper().startswith("CMD") or l.upper().startswith("ENTRYPOINT") for l in lines)
                
                if not has_from:
                    errors.append(f"Invalid Dockerfile ({filename}): Missing required 'FROM' instruction.")
                if not has_cmd_or_entry:
                    errors.append(f"Invalid Dockerfile ({filename}): Missing 'CMD' or 'ENTRYPOINT' run instruction.")

        # 3. Environment Variable matching
        # Check if environment variables detected in code are listed in .env.example
        env_example_content = deployment_files.get(".env.example", "")
        for var in env_vars.keys():
            if var not in env_example_content:
                warnings.append(f"Environment variable '{var}' detected in code but missing from .env.example.")

        # 4. Dependency checks (Database drivers)
        requirements = state.get("requirements", "") or state.get("backend", "")
        pkg_json = state.get("package_json", "") or state.get("frontend", "")

        for db in databases:
            db_lower = db.lower()
            if db_lower == "postgres":
                if "psycopg2" not in requirements and "asyncpg" not in requirements:
                    warnings.append("PostgreSQL database choice detected, but no database driver (psycopg2 or asyncpg) found in requirements.")
                else:
                    suggestions.append("PostgreSQL database driver found.")
            elif db_lower == "mongodb":
                if "pymongo" not in requirements and "motor" not in requirements:
                    warnings.append("MongoDB choice detected, but no driver (pymongo or motor) found in requirements.")
            elif db_lower == "mysql":
                if "mysqlclient" not in requirements and "pymysql" not in requirements:
                    warnings.append("MySQL choice detected, but no driver (mysqlclient or pymysql) found in requirements.")

        # 5. Health Check endpoint validator
        backend_code = state.get("backend", "")
        if "fastapi" in frameworks.get("backend", "").lower():
            if "/health" not in backend_code and "@app.get(\"/health\"" not in backend_code:
                suggestions.append("Consider implementing a /health check API route in your FastAPI main.py to support container monitoring.")

        # Calculate readiness score
        # Base score 100%
        # Deduction of 25% per error, 10% per warning
        readiness_score = 100
        readiness_score -= len(errors) * 25
        readiness_score -= len(warnings) * 10
        readiness_score = max(0, min(100, readiness_score))

        ready = readiness_score >= 80

        # Suggested cloud platform detection
        fe_framework = frameworks.get("frontend", "").lower()
        be_framework = frameworks.get("backend", "").lower()
        has_postgres = "postgres" in [db.lower() for db in databases]

        suggested_platform = "Render"
        reasoning = "Standard multi-container microservice web architecture."

        if fe_framework in ["react", "vue", "angular", "static"] and not be_framework:
            suggested_platform = "Netlify"
            reasoning = "Static site framework without backend compute container needs."
        elif fe_framework in ["react", "vue", "next.js", "nextjs"] and be_framework == "":
            suggested_platform = "Vercel"
            reasoning = "Tailored static or serverless Node.js applications."
        elif "streamlit" in backend_code or "gradio" in backend_code:
            suggested_platform = "HuggingFace"
            reasoning = "Interactive Machine Learning space container requirements."
        elif has_postgres and be_framework in ["fastapi", "django", "express"]:
            suggested_platform = "Railway"
            reasoning = "Highly recommended for full-stack MERN/PERN databases and backend web deployments."

        return DeploymentReadinessReport(
            ready=ready,
            readiness_score=readiness_score,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            detected_frameworks=frameworks,
            detected_databases=databases,
            suggested_platform=suggested_platform,
            reasoning=reasoning
        )
