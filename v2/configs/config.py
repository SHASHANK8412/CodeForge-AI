"""
AIForge V2 – Centralized Enterprise Configuration
==================================================
Configurations for LLMs, PostgreSQL, Redis, ChromaDB, Docker, GitHub, Logging, Security, and Memory.
"""

import os
from pathlib import Path
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class LLMConfig(BaseModel):
    ollama_base_url: str = Field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    default_model: str = Field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen2.5-coder:latest"))
    ceo_model: str = Field(default="qwen2.5-coder:latest")
    architect_model: str = Field(default="qwen2.5-coder:latest")
    coder_model: str = Field(default="qwen2.5-coder:latest")
    temperature: float = 0.2
    top_p: float = 0.9
    num_ctx: int = 8192


class DatabaseConfig(BaseModel):
    postgres_url: str = Field(
        default_factory=lambda: os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/aiforge_v2")
    )
    sqlite_memory_db: str = Field(default=str(PROJECT_ROOT / "backend" / "database" / "memory.db"))
    max_connections: int = 20
    echo_sql: bool = False


class RedisConfig(BaseModel):
    redis_url: str = Field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    cache_ttl_seconds: int = 3600
    enabled: bool = True


class VectorDBConfig(BaseModel):
    chroma_persist_dir: str = Field(default=str(PROJECT_ROOT / "v2" / "vector_store" / "chroma_db"))
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    top_k_chunks: int = 5


class SecurityConfig(BaseModel):
    jwt_secret: str = Field(default_factory=lambda: os.getenv("JWT_SECRET", "aiforge_v2_super_secret_key_2026"))
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440


class AppConfig(BaseModel):
    app_name: str = "AIForge V2 Enterprise"
    version: str = "2.0.0"
    environment: str = Field(default_factory=lambda: os.getenv("ENV", "development"))
    llm: LLMConfig = Field(default_factory=LLMConfig)
    db: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    vector_db: VectorDBConfig = Field(default_factory=VectorDBConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)


global_v2_config = AppConfig()
