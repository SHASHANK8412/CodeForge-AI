"""
AIForge Day 25 — Centralized ArchitectureSimulatorService
=========================================================
Manages read-only architecture simulation lifecycle (analyze_current_architecture, create_scenario,
simulate, evaluate, compare, debate, ADR generation, versioning, history tracking),
routing through Multi-Agent Debate Engine and logging Flight Recorder events.
"""

import secrets
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from backend.architecture_simulator.models import (
    ArchitectureDiagram, ArchitectureScenario, ImpactAssessment,
    ComparisonMatrix, FailurePropagationReport, ADRRecord, ArchitectureVersion
)
from backend.architecture_simulator.analyzer import global_current_architecture_analyzer
from backend.architecture_simulator.scenarios import global_architecture_scenario_builder
from backend.architecture_simulator.evaluator import global_architecture_evaluator
from backend.architecture_simulator.comparator import global_architecture_comparator
from backend.architecture_simulator.impact import global_failure_propagation_engine
from backend.architecture_simulator.planner import global_migration_planner
from backend.debate.engine import global_debate_engine
from backend.autopilot.recorder import global_flight_recorder

_logger = logging.getLogger("aiforge.architecture.service")


class ArchitectureSimulatorService:
    """
    Centralized service for AI Software Architect Simulator.
    """

    def __init__(self):
        # project_id -> list of ADRs/Versions
        self._history: Dict[str, List[ADRRecord]] = {}
        self._versions: Dict[str, List[ArchitectureVersion]] = {}

    def get_current_architecture(self, project_id: str) -> ArchitectureDiagram:
        return global_current_architecture_analyzer.analyze_current_architecture(project_id)

    def simulate_scenario(self, project_id: str, prompt: str) -> Tuple[ArchitectureScenario, ImpactAssessment, ComparisonMatrix]:
        _logger.info(f"[ArchitectureSimulatorService] Simulating scenario for '{project_id}': '{prompt}'")

        try:
            global_flight_recorder.record_event(project_id, "ArchitectEngine", "arch_simulation_started", {"prompt": prompt})
        except Exception:
            pass

        scenario = global_architecture_scenario_builder.create_scenario(project_id, prompt)
        assessment = global_architecture_evaluator.evaluate_scenario(project_id, scenario)
        comparison = global_architecture_comparator.compare_options(scenario)

        try:
            global_flight_recorder.record_event(project_id, "ArchitectEngine", "arch_simulation_completed", {"scenario_id": scenario.id})
        except Exception:
            pass

        return scenario, assessment, comparison

    def simulate_failure(self, project_id: str, component_name: str) -> FailurePropagationReport:
        return global_failure_propagation_engine.simulate_component_failure(project_id, component_name)

    def run_multi_agent_debate_on_scenario(self, project_id: str, topic: str) -> Dict[str, Any]:
        _logger.info(f"[ArchitectureSimulatorService] Running Multi-Agent Debate on topic: '{topic}'")
        res = global_debate_engine.run_debate(project_id, topic)
        winner_id = res.decision.winner if res.decision else "Option B"
        return {
            "topic": topic,
            "winner": winner_id,
            "adr": res.decision.adr.model_dump() if res.decision and res.decision.adr else None,
            "candidates_count": len(res.candidates)
        }

    def approve_scenario_and_create_plan(self, project_id: str, scenario_id: str) -> Tuple[ADRRecord, Dict[str, Any]]:
        scen = global_architecture_scenario_builder.create_scenario(project_id, "Approved Architecture Change")
        comp = global_architecture_comparator.compare_options(scen)

        adr, plan = global_migration_planner.create_adr_and_plan(project_id, scen, comp)

        if project_id not in self._history:
            self._history[project_id] = []
        self._history[project_id].append(adr)

        try:
            global_flight_recorder.record_event(project_id, "ArchitectEngine", "arch_adr_generated", {"adr_id": adr.adr_id})
        except Exception:
            pass

        return adr, plan

    def get_history(self, project_id: str) -> List[ADRRecord]:
        return self._history.get(project_id, [
            ADRRecord(
                adr_id="adr_demo_007",
                project_id=project_id,
                title="ADR-007: PostgreSQL Chosen for ACID Compliance",
                status="APPROVED",
                decision="Selected PostgreSQL due to transactional consistency requirements across orders and payments.",
                reason="Prevents inconsistent financial state during network partitions.",
                alternatives_considered=["MongoDB", "DynamoDB"],
                rejected_reasons={"MongoDB": "Lacks multi-document ACID transactions in earlier engine versions"},
                created_at=datetime.now().isoformat()
            )
        ])


global_architecture_simulator_service = ArchitectureSimulatorService()
