"""
AIForge Autonomous Self-Repair Engine
=====================================
Executes bounded self-repair loop:
1. Runs project test suite.
2. If tests pass -> terminates early with PASSED status.
3. If tests fail -> extracts error stack traces & failure evidence.
4. Invokes DebugAgent to generate targeted file repairs.
5. Applies file patches to physical project directory on disk.
6. Re-runs test suite.
7. Repeats up to max_repair_attempts (default 3) to prevent infinite loops.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple

from backend.agents.debug_agent import global_debug_agent
from backend.evaluation.test_runner import global_evaluation_test_runner
from backend.evaluation.models import EvaluationTestSummary

_logger = logging.getLogger("aiforge.evaluation.repair_engine")


class AutonomousSelfRepairEngine:
    """
    Reusable autonomous self-repair engine for AIForge project generation & evaluation.
    """

    def apply_patches_to_disk(self, project_path: str, files_map: Dict[str, str], changes: Dict[str, str]) -> List[str]:
        """Applies targeted file changes to disk and updates files_map in place."""
        if not project_path or not changes:
            return []

        target_dir = Path(project_path).resolve()
        modified_paths = []

        for rel_path, new_content in changes.items():
            clean_rel = rel_path.replace("\\", "/").lstrip("/")
            if clean_rel.startswith("/") or clean_rel.startswith("\\") or "../" in clean_rel or "..\\" in clean_rel:
                _logger.warning(f"Self-Repair path traversal rejected: '{rel_path}'")
                continue

            dest_path = (target_dir / clean_rel).resolve()
            if not str(dest_path).startswith(str(target_dir)):
                _logger.warning(f"Self-Repair path traversal rejected: '{rel_path}'")
                continue

            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_text(new_content, encoding="utf-8")
            files_map[clean_rel] = new_content
            modified_paths.append(clean_rel)

        return modified_paths

    def run_repair_loop(
        self,
        project_path: str,
        user_prompt: str,
        files_map: Dict[str, str],
        max_repair_attempts: int = 3
    ) -> Dict[str, Any]:
        """
        Executes bounded self-repair loop up to max_repair_attempts.
        Returns Dict with:
        - repair_attempts: int
        - repaired_files: List[str]
        - remaining_errors: List[str]
        - test_summary: EvaluationTestSummary
        - final_status: str ("PASSED" / "FAILED")
        - updated_files: Dict[str, str]
        """
        _logger.info(f"AutonomousSelfRepairEngine: Starting repair loop (max_attempts={max_repair_attempts})...")

        attempts = 0
        repaired_files: List[str] = []
        remaining_errors: List[str] = []
        final_summary = EvaluationTestSummary()

        while attempts < max_repair_attempts:
            # 1. Execute empirical tests
            run_res = global_evaluation_test_runner.run_tests(project_path)
            summary: EvaluationTestSummary = run_res["summary"]
            final_summary = summary

            # 2. Check if tests passed
            if summary.success:
                _logger.info(f"Self-Repair: Tests passed on attempt {attempts}/{max_repair_attempts}! Loop complete.")
                remaining_errors = []
                break

            # 3. Handle failure evidence
            failure_msg = run_res["failure_output"] or f"Pytest exit code {run_res['raw_execution'].exit_code}"
            remaining_errors = [failure_msg]
            _logger.info(f"Self-Repair Attempt {attempts + 1}/{max_repair_attempts}: Tests failed. Invoking DebugAgent...")

            # 4. Invoke DebugAgent
            debug_state = {
                "user_prompt": user_prompt,
                "project_path": project_path,
                "files": files_map,
                "execution_results": run_res["raw_execution"].model_dump(),
                "test_results": summary.model_dump(),
                "errors": [failure_msg]
            }

            try:
                debug_res = global_debug_agent.diagnose_and_repair(debug_state)
                changes = getattr(debug_res, "changes", {}) or {}
                if not changes and hasattr(debug_res, "files_to_modify"):
                    # Fallback if changes dict is nested
                    changes = getattr(debug_res, "patch_content", {})

                # 5. Apply patches to disk
                applied = self.apply_patches_to_disk(project_path, files_map, changes)
                for f in applied:
                    if f not in repaired_files:
                        repaired_files.append(f)
            except Exception as e:
                _logger.error(f"DebugAgent invocation error during self-repair: {e}")
                remaining_errors.append(str(e))

            attempts += 1

        # Final check if loop reached max attempts without passing
        if not final_summary.success and attempts >= max_repair_attempts:
            _logger.warning(f"Self-Repair: Reached MAX_ATTEMPTS ({max_repair_attempts}). Terminating with remaining errors.")

        final_status = "PASSED" if final_summary.success else "FAILED"

        return {
            "repair_attempts": attempts,
            "repaired_files": repaired_files,
            "remaining_errors": remaining_errors,
            "test_summary": final_summary,
            "final_status": final_status,
            "updated_files": files_map
        }


global_self_repair_engine = AutonomousSelfRepairEngine()
