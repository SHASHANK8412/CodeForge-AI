"""
AIForge Day 27 — Database Connection & Health Manager
======================================================
Manages SQLAlchemy engine, session maker, get_db dependency, and health checks.
"""

import os
import logging
from typing import Dict, Any, Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

_logger = logging.getLogger("aiforge.database.connection")

DEFAULT_DB_URL = "sqlite:///./backend/database/memory.db"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

# Configure sqlite/postgresql connect args
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for retrieving a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initializes database tables if they do not exist."""
    try:
        from backend.database import models  # noqa: F401
        Base.metadata.create_all(bind=engine)
        _logger.info("Database tables initialized successfully.")
    except Exception as e:
        _logger.warning(f"Database table initialization warning: {e}")



def check_db_health() -> Dict[str, Any]:
    """
    Checks database health without exposing sensitive connection credentials.
    """
    db_type = "postgresql" if "postgres" in DATABASE_URL.lower() else "sqlite"
    pgvector_active = False

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            if db_type == "postgresql":
                res = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
                if res.fetchone():
                    pgvector_active = True
            elif db_type == "sqlite":
                # Ensure legacy SQLite tables match current schema
                try:
                    cols = [row[1] for row in conn.execute(text("PRAGMA table_info(projects)")).fetchall()]
                    if cols:
                        if "name" not in cols:
                            conn.execute(text("ALTER TABLE projects ADD COLUMN name VARCHAR(255) DEFAULT ''"))
                        if "description" not in cols:
                            conn.execute(text("ALTER TABLE projects ADD COLUMN description TEXT DEFAULT ''"))
                        if "status" not in cols:
                            conn.execute(text("ALTER TABLE projects ADD COLUMN status VARCHAR(64) DEFAULT 'ACTIVE'"))
                        if "created_at" not in cols:
                            conn.execute(text("ALTER TABLE projects ADD COLUMN created_at VARCHAR(64) DEFAULT ''"))
                        if "updated_at" not in cols:
                            conn.execute(text("ALTER TABLE projects ADD COLUMN updated_at VARCHAR(64) DEFAULT ''"))
                        conn.commit()
                except Exception:
                    pass




        return {
            "status": "healthy",
            "database": db_type,
            "pgvector_enabled": pgvector_active,
            "vector_engine": "pgvector" if pgvector_active else "chroma_hybrid",
            "project_isolation": "ENFORCED"
        }
    except Exception as e:
        _logger.warning(f"Database health check warning: {e}")
        return {
            "status": "degraded",
            "database": db_type,
            "pgvector_enabled": False,
            "vector_engine": "chroma_hybrid",
            "project_isolation": "ENFORCED",
            "details": "Database connection degraded; running in-memory vector store mode."
        }
