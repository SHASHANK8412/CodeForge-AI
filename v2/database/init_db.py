"""
AIForge V2 – Database Initialization Script
===========================================
Creates all database tables defined in models_memory.py.
"""

from v2.database.db import engine, Base
from v2.database.models_memory import ProjectModelV2, TaskModelV2, ConversationModelV2, AgentLogModelV2


def init_database():
    Base.metadata.create_all(bind=engine)
    print("✓ AIForge V2 Persistent Memory database tables initialized successfully.")


if __name__ == "__main__":
    init_database()
