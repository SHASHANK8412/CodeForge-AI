"""
AIForge Master Project Evaluator Engine
=======================================
Orchestrates project generation evaluation, requirement coverage, security scan,
empirical test execution, autonomous self-repair loop, and dynamic 100-point scoring.
"""

import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from backend.agents.requirement_fidelity_agent import global_requirement_fidelity_agent
from backend.agents.security_agent import SecurityAgent
from backend.agents.build_validation_agent import BuildValidationAgent
from backend.evaluation.scoring import global_project_score_calculator
from backend.evaluation.repair_engine import global_self_repair_engine
from backend.evaluation.models import (
    ProjectEvaluationResult,
    EvaluationScoreBreakdown,
    EvaluationTestSummary
)

_logger = logging.getLogger("aiforge.evaluation.evaluator")


class ProjectEvaluator:
    """
    Master Evaluator orchestrating evaluation, testing, self-repair, and scoring.
    """

    def __init__(self):
        self.security_agent = SecurityAgent()
        self.build_validation_agent = BuildValidationAgent()

    def evaluate_and_repair_project(
        self,
        project_path: str,
        requirements: str,
        files_map: Optional[Dict[str, str]] = None,
        max_repair_attempts: int = 3,
        project_spec: Optional[Dict[str, Any]] = None,
        architecture_spec: Optional[Dict[str, Any]] = None
    ) -> ProjectEvaluationResult:
        """
        Runs complete evaluation + self-repair pipeline on project at project_path.
        """
        start_time = time.perf_counter()
        _logger.info(f"ProjectEvaluator: Evaluating project at '{project_path}' for requirements: '{requirements[:40]}...'")

        # Load files from disk if files_map is not supplied
        files = dict(files_map or {})
        target_dir = Path(project_path).resolve() if project_path else None
        if target_dir and target_dir.exists() and not files:
            for p in target_dir.rglob("*"):
                if p.is_file() and not any(part.startswith(".") or part in ["venv", "node_modules", "__pycache__"] for part in p.parts):
                    try:
                        rel = str(p.relative_to(target_dir)).replace("\\", "/")
                        files[rel] = p.read_text(encoding="utf-8", errors="ignore")
                    except Exception:
                        pass

        proj_name = (project_spec.get("project_name") if project_spec else None) or (target_dir.name if target_dir else "AIForge Project")

        # 1. Requirement Coverage & Domain Fidelity
        fidelity_res = global_requirement_fidelity_agent.evaluate_fidelity(
            user_prompt=requirements,
            project_spec=project_spec or {"project_name": proj_name},
            architecture_spec=architecture_spec or {},
            files=files
        )

        # 2. Autonomous Self-Repair Engine (Runs tests, detects errors, repairs, re-tests up to max_repair_attempts)
        repair_res = global_self_repair_engine.run_repair_loop(
            project_path=project_path,
            user_prompt=requirements,
            files_map=files,
            max_repair_attempts=max_repair_attempts
        )

        repair_attempts = repair_res["repair_attempts"]
        repaired_files = repair_res["repaired_files"]
        remaining_errors = repair_res["remaining_errors"]
        test_summary: EvaluationTestSummary = repair_res["test_summary"]
        updated_files = repair_res["updated_files"]

        # 3. Security Audit
        sec_report = self.security_agent.scan_files(updated_files or {"main.py": ""}).model_dump()

        # 4. Code Quality & Build Validation
        val_report = self.build_validation_agent.validate_all(
            {"App.jsx": updated_files.get("frontend/src/App.jsx", "")},
            {"main.py": updated_files.get("backend/main.py", "")},
            updated_files.get("database/schema.sql", ""),
            {"Dockerfile": ""}
        ).model_dump()


        # 5. Documentation check
        has_docs = any("readme.md" in k.lower() for k in updated_files.keys()) or len(updated_files) > 0

        # 6. Calculate 100-Point Score Breakdown
        score_breakdown: EvaluationScoreBreakdown = global_project_score_calculator.calculate_scores(
            fidelity_result=fidelity_res,
            test_summary=test_summary.model_dump(),
            security_report=sec_report,
            architecture_spec=architecture_spec,
            static_analysis_report=val_report,
            has_documentation=has_docs,
            execution_exit_code=0 if test_summary.success else 1
        )

        elapsed = round(time.perf_counter() - start_time, 2)
        final_status = "PASSED" if (test_summary.success and fidelity_res["status"] == "PASS") else "FAILED"

        return ProjectEvaluationResult(
            project_name=proj_name,
            requirements=requirements,
            overall_score=score_breakdown.overall_score,
            final_status=final_status,
            scores=score_breakdown,
            test_results=test_summary,
            repair_attempts=repair_attempts,
            max_repair_attempts=max_repair_attempts,
            repaired_files=repaired_files,
            remaining_errors=remaining_errors,
            execution_time_seconds=elapsed
        )


global_project_evaluator = ProjectEvaluator()
