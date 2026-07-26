import logging
from typing import Dict, Any

logger = logging.getLogger("aiforge.exporter.env_generator")


class EnvGenerator:
    """
    EnvGenerator creates a clean, production-ready .env.example environment variable template.
    """

    def generate_env_example(self, tech_stack: Dict[str, Any] = None) -> str:
        db_type = (tech_stack or {}).get("database", "PostgreSQL").lower()
        db_url = "postgresql://postgres:postgres@localhost:5432/app_db" if "postgre" in db_type else "sqlite:///./app.db"

        env_content = f"""# AIForge V2 Generated Environment Configuration Template
# Copy this file to .env before starting the server

# Database Configuration
DATABASE_URL={db_url}

# Security & Authentication
SECRET_KEY=aiforge_v2_secret_key_change_in_production
JWT_SECRET=jwt_secret_key_aiforge_v2_2026
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Server Settings
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# AI & RAG Settings
OPENAI_API_KEY=your_openai_api_key_here
OLLAMA_BASE_URL=http://localhost:11434
CHROMA_DB_PATH=./vector_store
"""
        return env_content


# Global EnvGenerator Instance
global_env_generator = EnvGenerator()
