"""
AIForge Day 25 — Architecture Scenario Builder
==============================================
Creates architecture simulation scenarios (Add Redis, Migrate DB, Microservices, 10x Traffic, Component Failure).
"""

import secrets
import logging
from datetime import datetime
from typing import Dict, Any, List

from backend.architecture_simulator.models import ArchitectureScenario

_logger = logging.getLogger("aiforge.architecture.scenarios")


class ArchitectureScenarioBuilder:
    """
    Constructs isolated architecture scenarios for simulation.
    """

    def create_scenario(self, project_id: str, prompt: str) -> ArchitectureScenario:
        _logger.info(f"[ScenarioBuilder] Creating scenario for '{project_id}': '{prompt}'")
        p_lower = prompt.lower()
        scen_id = f"scen_{secrets.token_urlsafe(6)}"
        now_str = datetime.now().isoformat()

        if "redis" in p_lower:
            return ArchitectureScenario(
                id=scen_id,
                project_id=project_id,
                name="Introduce Redis Caching Layer",
                description="Introduce Redis cache between FastAPI Gateway and PostgreSQL DB for read caching.",
                changes=["Add Redis node (redis:7-alpine)", "Interpose Redis cache lookup in OrderService.get_orders()"],
                assumptions=["High read-to-write ratio on order queries", "Cache invalidation on order mutations"],
                status="SIMULATION_ONLY",
                created_at=now_str
            )

        if "mongo" in p_lower or "postgres" in p_lower:
            return ArchitectureScenario(
                id=scen_id,
                project_id=project_id,
                name="Migrate Database to PostgreSQL",
                description="Replace document schema with relational PostgreSQL tables and transactional constraints.",
                changes=["Migrate schemas to SQLAlchemy models", "Rewrite raw queries to psycopg2 parameterized SQL"],
                assumptions=["Relational integrity required for payments", "Database migration tool (Alembic) configured"],
                status="SIMULATION_ONLY",
                created_at=now_str
            )

        if "traffic" in p_lower or "scale" in p_lower:
            return ArchitectureScenario(
                id=scen_id,
                project_id=project_id,
                name="Simulate 10x Traffic Load",
                description="Simulate 10x concurrent requests on Order & Checkout APIs.",
                changes=["Increase API worker concurrency from 4 to 40", "Simulate PostgreSQL connection pool pressure"],
                assumptions=["Hardware resource limits remain 512MB RAM / 1 CPU per container"],
                status="SIMULATION_ONLY",
                created_at=now_str
            )

        return ArchitectureScenario(
            id=scen_id,
            project_id=project_id,
            name=f"Custom Scenario: {prompt[:30]}",
            description=f"Architecture simulation for user query: '{prompt}'",
            changes=["Refactor component boundaries", "Add load balancer"],
            assumptions=["Read-only simulation sandbox"],
            status="SIMULATION_ONLY",
            created_at=now_str
        )


global_architecture_scenario_builder = ArchitectureScenarioBuilder()
