"""
AIForge V2 – PostgreSQL Connection & Database Engine
====================================================
Establishes SQLAlchemy engine, SessionLocal factory, and Base model declarations.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/aiforge")

# Fallback for local testing if postgres is offline
if "postgresql" in DATABASE_URL:
    try:
        engine = create_engine(DATABASE_URL, pool_size=20, max_overflow=10, pool_pre_ping=True)
        # Quick test connection
        with engine.connect() as conn:
            pass
    except Exception:
        # Fallback to local SQLite in-memory for testing safety
        DATABASE_URL = "sqlite:///./aiforge_v2_memory.db"
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
