"""
AIForge V2 – FastAPI Settings & Config Generator
================================================
Generates Pydantic BaseSettings config module supporting environment variables.
"""


class FastAPIConfigGenerator:

    def generate_config_code(self) -> str:
        return """import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "AIForge V2 FastAPI App"
    ENV: str = os.getenv("ENV", "development")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/aiforge_v2")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super_secret_jwt_key_2026")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

settings = Settings()
"""


global_config_generator = FastAPIConfigGenerator()
