import logging

_logger = logging.getLogger("aiforge.performance")

class RailwayGenerator:
    """
    Generates railway.toml configuration for deployment on Railway,
    customizing start commands, build pipelines, and health checks.
    """

    def __init__(self) -> None:
        pass

    def generate_config(self, framework: str = "fastapi", port: int = 8000) -> str:
        """
        Creates railway.toml layout.
        """
        _logger.info(f"Generating railway.toml configuration for framework: {framework}")
        
        framework = framework.lower()
        watch_path = "/"
        if framework == "fastapi":
            start_cmd = f"uvicorn backend.main:app --host 0.0.0.0 --port {port}"
            watch_path = "/health"
        elif framework == "express":
            start_cmd = "node src/index.js"
        else:
            start_cmd = "npm run start"

        return f"""# Railway Deployment Configuration
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "{start_cmd}"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3

[deploy.healthcheck]
path = "{watch_path}"
interval = 10
timeout = 5
startPeriod = 15
"""
