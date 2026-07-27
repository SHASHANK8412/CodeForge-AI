"""
AIForge Core Architecture Designer
===================================
Selects optimal architectural patterns (Microservices, Modular Monolith, Event-Driven, Serverless, CQRS, Clean Architecture) based on user scale, complexity, and latency requirements.
"""

import logging
from typing import Dict, Any, List, Optional
from backend.architecture.analyzer import global_requirement_analyzer

_logger = logging.getLogger("aiforge.architecture.designer")


class ArchitecturePattern:
    MONOLITH = "Monolith"
    MODULAR_MONOLITH = "Modular Monolith"
    MICROSERVICES = "Microservices"
    EVENT_DRIVEN = "Event-Driven Architecture"
    SERVERLESS = "Serverless"
    CQRS = "CQRS"
    CLEAN_ARCHITECTURE = "Clean Architecture"
    HEXAGONAL = "Hexagonal Architecture"

    ALL_PATTERNS = [
        MONOLITH, MODULAR_MONOLITH, MICROSERVICES, EVENT_DRIVEN,
        SERVERLESS, CQRS, CLEAN_ARCHITECTURE, HEXAGONAL
    ]


class CoreArchitectureDesigner:
    """
    Selects architecture patterns and generates high-level design specifications.
    """

    def select_architecture(self, req_analysis: Dict[str, Any]) -> Dict[str, Any]:
        users = req_analysis.get("expected_users", "")
        concurrency = req_analysis.get("peak_concurrency_target", 250)

        if concurrency >= 10000 or "Million" in users:
            selected_pattern = ArchitecturePattern.MICROSERVICES
            reason = "High user concurrency (>=10,000 req/s) requires independent container scaling, fault isolation, and decoupled microservices."
        elif concurrency >= 1000:
            selected_pattern = ArchitecturePattern.EVENT_DRIVEN
            reason = "Asynchronous workload decoupling using pub/sub event brokers for high throughput event processing."
        else:
            selected_pattern = ArchitecturePattern.MODULAR_MONOLITH
            reason = "Optimal development velocity and clean bounded contexts for initial deployment scaling."

        design = {
            "selected_architecture": selected_pattern,
            "justification": reason,
            "recommended_components": [
                "API Gateway (Nginx / Kong)",
                "Auth Service (OAuth2 / JWT)",
                "Core Application Backend (FastAPI Services)",
                "Database Cluster (PostgreSQL Primary + Read Replicas)",
                "Caching Layer (Redis Cluster)",
                "Async Message Queue (RabbitMQ / Kafka)"
            ],
            "estimated_infrastructure": {
                "backend_nodes": 4 if "Microservices" in selected_pattern else 2,
                "database_replicas": 2,
                "cache_nodes": 2,
                "load_balancers": 1
            }
        }

        _logger.info(f"CoreArchitectureDesigner: Selected '{selected_pattern}' for scale '{users}'")
        return design


global_core_architecture_designer = CoreArchitectureDesigner()
