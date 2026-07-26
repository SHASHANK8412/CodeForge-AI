"""
AIForge V2 – Seed Data Generator
================================
Generates Python seed scripts (`seed_db.py`) populated with admin accounts, demo projects, and tasks.
"""

from typing import List
from v2.agents.database.models import SeedDataSpec


class SeedDataGenerator:

    def generate_default_seeds(self) -> List[SeedDataSpec]:
        return [
            SeedDataSpec(
                table_name="users",
                records=[
                    {"id": "u1", "username": "admin", "email": "admin@aiforge.io", "role": "admin"},
                    {"id": "u2", "username": "developer", "email": "dev@aiforge.io", "role": "user"}
                ]
            ),
            SeedDataSpec(
                table_name="projects",
                records=[
                    {"id": "p1", "user_id": "u1", "name": "AI Resume Analyzer", "complexity_tier": "medium", "status": "active"},
                    {"id": "p2", "user_id": "u1", "name": "E-Commerce Platform", "complexity_tier": "enterprise", "status": "in_progress"}
                ]
            )
        ]


global_seed_generator = SeedDataGenerator()
