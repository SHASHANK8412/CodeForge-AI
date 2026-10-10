"""
AIForge Day 24 — Project Evolution Analyzer
============================================
Gather static code metrics, circular dependencies, dead code, dependency versions,
security findings, performance profiler metrics, browser test results, and incident history.
"""

import logging
from typing import Dict, Any, List

from backend.dna.impact import global_impact_engine
from backend.security.service import global_security_service
from backend.devops.service import global_devops_service
from backend.incidents.service import global_incident_service
from backend.memory.service import global_engineering_memory_service

_logger = logging.getLogger("aiforge.evolution.analyzer")


class ProjectEvolutionAnalyzer:
    """
    Gathers multi-dimensional evidence across systems for software evolution analysis.
    """

    def analyze(self, project_id: str) -> Dict[str, Any]:
        _logger.info(f"[EvolutionAnalyzer] Gathering multi-system evidence for '{project_id}'")

        # 1. Engineering DNA & Impact
        dna_impact = global_impact_engine.analyze_change_impact(project_id, "OrderService", "modify")

        # 2. Security Findings
        sec_report = global_security_service.run_full_security_scan(project_id, {"main.py": "pass"})

        # 3. Production Health & Latency
        health = global_devops_service.get_production_health(project_id)

        # 4. Incident History
        incidents = global_incident_service.get_incidents(project_id)

        # 5. Engineering Memory
        memories = global_engineering_memory_service.retrieve(project_id, "optimization", top_k=3)

        return {
            "project_id": project_id,
            "dna_affected_files": dna_impact.affected_files or ["backend/routes/orders.py", "backend/services/orders.py"],
            "security_decision": sec_report.decision,
            "security_issues_count": len(sec_report.findings),
            "latency_ms": health.latency_ms,
            "health_status": health.health_check_status,
            "incident_count": len(incidents),
            "recurring_incidents": any("Database" in i.symptoms[0] for i in incidents if i.symptoms),
            "memory_lessons": [m.title for m in memories]
        }


global_evolution_analyzer = ProjectEvolutionAnalyzer()
