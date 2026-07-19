import logging

_logger = logging.getLogger("aiforge.performance")


class EnvGenerator:
    """
    Programmatically generates environment variable template file (.env.example)
    customized according to project specifications.
    """

    def __init__(self) -> None:
        pass

    def generate_env_example(self, db_engines: list[str]) -> str:
        """
        Creates environment variable definitions dynamically.
        """
        _logger.info("Generating .env.example templates...")

        db_type = "mongodb"
        for engine in db_engines:
            engine_clean = engine.lower()
            if engine_clean in {"mongodb", "postgresql", "mysql"}:
                db_type = engine_clean
                break

        # Define default DATABASE_URL string matching chosen engine
        if db_type == "postgresql":
            db_url = "postgresql://app_user:secure_password@localhost:5432/app_database"
        elif db_type == "mysql":
            db_url = "mysql+connector://app_user:secure_password@localhost:3306/app_database"
        else:
            db_url = "mongodb://admin:secure_password@localhost:27017/app_database?authSource=admin"

        env_template = f"""# ==============================================================================
# AIForge Generated Environment Configuration Example
# Copy this file to '.env' and fill in your actual credentials.
# ==============================================================================

# Server configuration
PORT=8000
HOST=0.0.0.0

# Database URL Connection String
DATABASE_URL={db_url}

# Authentication details
JWT_SECRET=super_secret_session_jwt_key_please_change_in_production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# External AI Model Integrations
OPENAI_API_KEY=your-openai-api-key-here
OLLAMA_MODEL=qwen2.5-coder:latest
OLLAMA_BASE_URL=http://localhost:11434

# Debug settings
DEBUG=True
"""
        _logger.info(".env.example generated successfully")
        return env_template
