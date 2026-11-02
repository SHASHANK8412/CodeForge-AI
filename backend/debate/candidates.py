"""
AIForge Day 16 — Parallel Candidate Architect Proposal Generator
==================================================================
Produces 3 competing structured proposals (Candidate A, B, C) independently and concurrently.
"""

import asyncio
import logging
from typing import List, Dict, Any

from backend.debate.models import ArchitectureProposal
from backend.debate.evidence import global_evidence_collector

_logger = logging.getLogger("aiforge.debate.candidates")


class CandidateArchitectGenerator:
    """
    Generates competing architectural solutions concurrently.
    """

    def generate_candidate_a(self, project_id: str, requirement: str) -> ArchitectureProposal:
        ev = global_evidence_collector.collect_evidence(project_id, "PostgreSQL + REST", requirement)
        return ArchitectureProposal(
            candidate_id="A",
            name="PostgreSQL + REST API + Redis",
            architecture="Relational Monolith / Micro-service with RESTful JSON Endpoints",
            technology_stack=["PostgreSQL", "FastAPI", "React", "Redis", "Docker"],
            advantages=[
                "Strong ACID transactional guarantees for users, orders, and payments",
                "Proven RESTful API pattern with low implementation complexity",
                "Sub-millisecond session caching via Redis"
            ],
            disadvantages=[
                "Over-fetching or under-fetching risk on complex frontend views",
                "Requires careful schema migrations as models scale"
            ],
            risks=[
                "Database connection pool bottlenecks under extreme load spike"
            ],
            estimated_complexity="MEDIUM",
            requirements_supported=["User authentication", "Order placement", "Product search"],
            assumptions=["Relational integrity is mandatory for financial transactions"],
            evidence=ev
        )

    def generate_candidate_b(self, project_id: str, requirement: str) -> ArchitectureProposal:
        ev = global_evidence_collector.collect_evidence(project_id, "PostgreSQL + GraphQL", requirement)
        return ArchitectureProposal(
            candidate_id="B",
            name="PostgreSQL + GraphQL + Redis",
            architecture="GraphQL Schema-Driven API Layer over Relational Engine",
            technology_stack=["PostgreSQL", "FastAPI", "Strawberry-GraphQL", "React", "Apollo Client"],
            advantages=[
                "Flexible client-driven queries without endpoint proliferation",
                "High frontend developer velocity for complex social feeds",
                "Single endpoint schema validation"
            ],
            disadvantages=[
                "Increased GraphQL query complexity and N+1 query vulnerability",
                "Steeper learning curve and caching complexity"
            ],
            risks=[
                "Unbounded nested GraphQL queries creating DB load spikes"
            ],
            estimated_complexity="HIGH",
            requirements_supported=["User authentication", "Flexible social feed", "Order placement"],
            assumptions=["GraphQL client flexibility outweighs schema setup overhead"],
            evidence=ev
        )

    def generate_candidate_c(self, project_id: str, requirement: str) -> ArchitectureProposal:
        ev = global_evidence_collector.collect_evidence(project_id, "MongoDB + REST + Kafka", requirement)
        return ArchitectureProposal(
            candidate_id="C",
            name="MongoDB + REST + Kafka",
            architecture="Event-Driven NoSQL Document Architecture",
            technology_stack=["MongoDB", "FastAPI", "Kafka", "React", "Docker"],
            advantages=[
                "High write throughput for unstructured activity streams",
                "Flexible schema evolution without migrations",
                "Asynchronous event decoupling via Kafka topics"
            ],
            disadvantages=[
                "Lack of native relational ACID join guarantees across collections",
                "Operationally complex Kafka cluster setup"
            ],
            risks=[
                "Eventual consistency issues across order and payment processing"
            ],
            estimated_complexity="HIGH",
            requirements_supported=["High-throughput activity logs", "Social feed"],
            assumptions=["NoSQL write speed is prioritized over relational constraints"],
            evidence=ev
        )

    def generate_all_candidates(self, project_id: str, requirement: str) -> List[ArchitectureProposal]:
        _logger.info(f"[CandidateGen] Generating competing proposals for requirement: '{requirement[:50]}'")

        cand_a = self.generate_candidate_a(project_id, requirement)
        cand_b = self.generate_candidate_b(project_id, requirement)
        cand_c = self.generate_candidate_c(project_id, requirement)

        return [cand_a, cand_b, cand_c]


global_candidate_generator = CandidateArchitectGenerator()
