"""
AIForge Day 25 — Architecture Migration & ADR Planner
======================================================
Generates 7-phase migration plans and ADR records (persisted to Engineering Memory) upon explicit user approval.
"""

import secrets
import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple

from backend.architecture_simulator.models import ADRRecord, ArchitectureScenario, ComparisonMatrix
from backend.memory.service import global_engineering_memory_service
from backend.memory.models import MemoryType, MemorySource

_logger = logging.getLogger("aiforge.architecture.planner")


class MigrationPlanner:
    """
    Generates 7-phase implementation plans and ADR records upon user approval.
    """

    def create_adr_and_plan(
        self,
        project_id: str,
        scenario: ArchitectureScenario,
        comparison: ComparisonMatrix
    ) -> Tuple[ADRRecord, Dict[str, Any]]:
        _logger.info(f"[MigrationPlanner] Generating ADR & 7-phase plan for '{scenario.name}'")

        adr_id = f"adr_{secrets.token_urlsafe(6)}"
        now_str = datetime.now().isoformat()

        adr = ADRRecord(
            adr_id=adr_id,
            project_id=project_id,
            title=f"ADR: {scenario.name}",
            status="APPROVED",
            decision=comparison.recommendation,
            reason=comparison.rationale,
            alternatives_considered=[o.option_name for o in comparison.proposed_options],
            rejected_reasons={
                comparison.proposed_options[0].option_name: "Higher operational & security complexity relative to performance gains"
            },
            created_at=now_str
        )

        # Store in Engineering Memory
        global_engineering_memory_service.remember(
            project_id=project_id,
            title=f"Architecture Decision Record: {scenario.name}",
            content=f"Decision: {comparison.recommendation}. Rationale: {comparison.rationale}",
            mem_type=MemoryType.ARCHITECTURE_DECISION,
            source=MemorySource.DEBATE
        )

        plan_phases = {
            "phase_1_prepare": "Create snapshot branch & setup migration feature flags",
            "phase_2_implement": "Apply code refactoring on isolated snapshot branch",
            "phase_3_migrate": "Execute database schema migration scripts",
            "phase_4_validate": "Run Unit, Security, Playwright Browser & Readiness Gate tests",
            "phase_5_cutover": "Deploy to staging environment for controlled smoke testing",
            "phase_6_monitor": "Monitor production health and P95 latency metrics",
            "phase_7_rollback": "Automatic rollback to previous version if health checks fail"
        }

        return adr, plan_phases


global_migration_planner = MigrationPlanner()
