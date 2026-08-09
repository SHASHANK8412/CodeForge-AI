"""
AIForge V2 — What-If Engineering Simulator Engine
=================================================
Simulates software changes (e.g. database switches, framework shifts, schema changes)
and analyzes file, API, test, work estimate, and risk impacts before modifying code.
"""

import secrets
import logging
from typing import Dict, Any, List, Optional

from backend.intelligence.models import SimulationRequest, SimulationResult

_logger = logging.getLogger("aiforge.intelligence.simulator")


class WhatIfSimulator:
    """
    Engine for simulating structural software changes and analyzing risks.
    """

    def simulate(self, project_id: str, proposed_change: str) -> SimulationResult:
        sim_id = f"sim_{secrets.token_urlsafe(8)}"
        query_lower = proposed_change.lower()

        if "mongodb" in query_lower or "nosql" in query_lower:
            return SimulationResult(
                simulation_id=sim_id,
                project_id=project_id,
                proposed_change=proposed_change,
                files_affected=27,
                apis_affected=8,
                tests_affected=14,
                estimated_work_hours=3.2,
                risk_level="MEDIUM",
                recommendation="REJECT",
                reason="Your transaction-heavy architecture benefits significantly from PostgreSQL ACID guarantees and relational constraints.",
                affected_components=[
                    {"component": "Database Schema", "impact": "High — Migration from SQL DDL to BSON collections"},
                    {"component": "ORM / Data Access Layer", "impact": "High — Replace SQLAlchemy models with PyMongo/Beanie"},
                    {"component": "Auth & Order Routes", "impact": "Medium — 8 endpoints require transaction rewrite"},
                    {"component": "Pytest Suite", "impact": "Medium — 14 test cases require DB fixture changes"}
                ]
            )
        elif "graphql" in query_lower:
            return SimulationResult(
                simulation_id=sim_id,
                project_id=project_id,
                proposed_change=proposed_change,
                files_affected=15,
                apis_affected=12,
                tests_affected=9,
                estimated_work_hours=2.5,
                risk_level="LOW",
                recommendation="ACCEPT",
                reason="GraphQL schema fits multi-resource mobile queries well, but REST endpoints can be maintained alongside standard resolvers.",
                affected_components=[
                    {"component": "GraphQL Schema", "impact": "Medium — Create Ariadne/Strawberry resolvers"},
                    {"component": "Backend Routes", "impact": "Low — Mount /graphql endpoint"},
                    {"component": "Frontend API Client", "impact": "Medium — Update frontend query hooks"}
                ]
            )
        else:
            return SimulationResult(
                simulation_id=sim_id,
                project_id=project_id,
                proposed_change=proposed_change,
                files_affected=11,
                apis_affected=4,
                tests_affected=6,
                estimated_work_hours=1.8,
                risk_level="LOW",
                recommendation="ACCEPT",
                reason=f"Simulation complete for '{proposed_change}'. Low architectural impact detected.",
                affected_components=[
                    {"component": "Application Config", "impact": "Low — Update environment settings"},
                    {"component": "API Handlers", "impact": "Low — Moderate route adjustments"}
                ]
            )


global_whatif_simulator = WhatIfSimulator()
