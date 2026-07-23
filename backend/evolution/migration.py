"""
AIForge Master Code Evolution Engine
====================================
Orchestrates impact analysis, migration planning, patch generation, rollback creation,
selective testing, and automated documentation synchronization for codebase evolutions.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from backend.evolution.impact import ImpactAnalyzer
from backend.evolution.planner import EvolutionPlanner
from backend.evolution.patch_generator import EvolutionPatchGenerator
from backend.evolution.rollback import RollbackEngine
from backend.evolution.selective_runner import SelectiveTestRunner
from backend.evolution.doc_updater import DocumentationUpdater

_logger = logging.getLogger("aiforge.evolution")


class CodeEvolutionEngine:
    """
    Master Code Evolution Engine.
    """

    def __init__(self) -> None:
        self.impact_analyzer = ImpactAnalyzer()
        self.planner = EvolutionPlanner()
        self.patch_generator = EvolutionPatchGenerator()
        self.rollback_engine = RollbackEngine()
        self.selective_runner = SelectiveTestRunner()
        self.doc_updater = DocumentationUpdater()

    def evolve_codebase(self, proposed_evolution: str, target_symbol: str = "") -> Dict[str, Any]:
        """
        Executes complete Code Evolution pipeline:
        Impact -> Migration Plan -> Patch Gen -> Rollback -> Selective Tests -> Doc Update -> Changelog
        """
        _logger.info(f"CodeEvolutionEngine: Starting evolution workflow for prompt: '{proposed_evolution}'")
        start_time = time.perf_counter()

        # 1. Impact Analysis
        impact_report = self.impact_analyzer.evaluate_impact(proposed_evolution, target_symbol=target_symbol)
        affected_files = impact_report["affected_files"]

        # 2. Migration Planning
        migration_plan = self.planner.create_migration_plan(impact_report)

        # 3. Evolution Patch Generation
        patch_report = self.patch_generator.generate_evolution_patches(migration_plan, affected_files)

        # 4. Rollback Plan Creation
        rollback_plan = self.rollback_engine.generate_rollback_plan(migration_plan, patch_report)

        # 5. Selective Test Runner (Run only impacted tests, skip unaffected)
        test_results = self.selective_runner.run_selective_tests(affected_files)

        # 6. Documentation Synchronization
        doc_results = self.doc_updater.update_documentation({
            "proposed_change": proposed_evolution,
            "files_updated": affected_files
        })

        execution_latency = round(time.perf_counter() - start_time, 3)
        _logger.info(f"CodeEvolutionEngine: Completed evolution in {execution_latency}s. Status: SUCCESS")

        return {
            "status": "success",
            "proposed_evolution": proposed_evolution,
            "impact_analysis": impact_report,
            "migration_plan": migration_plan,
            "patch_report": patch_report,
            "rollback_plan": rollback_plan,
            "selective_test_results": test_results,
            "documentation_updates": doc_results,
            "execution_latency_seconds": execution_latency,
            "changelog": f"Evolution '{proposed_evolution}' completed: {patch_report['total_files_updated']} files updated, {test_results['related_tests_run']} related tests passed ({test_results['unaffected_tests_skipped']} unaffected tests skipped)."
        }


global_evolution_engine = CodeEvolutionEngine()
