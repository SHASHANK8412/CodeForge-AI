import time
import logging
from typing import Dict, Any, List

from backend.execution.runner import global_project_execution_engine
from backend.debugging.analyzer import global_debug_analyzer
from backend.debugging.fixer import global_automatic_fixer

logger = logging.getLogger("aiforge.debugging.retry")


class SelfHealingRetryEngine:
    """
    SelfHealingRetryEngine runs execution -> diagnosis -> fix -> re-test loop
    up to max 3 attempts to deliver a healthy, working project.
    """

    def execute_self_healing_loop(self, project_files: Dict[str, str], max_attempts: int = 3) -> Dict[str, Any]:
        current_files = dict(project_files)
        history = []

        for attempt in range(1, max_attempts + 1):
            logger.info(f"Self-Healing Loop Attempt {attempt}/{max_attempts}...")

            exec_res = global_project_execution_engine.execute_project(current_files)
            if exec_res["is_healthy"]:
                return {
                    "status": "healthy",
                    "attempts": attempt,
                    "final_files": current_files,
                    "history": history,
                    "self_healing_score": 100.0 if attempt == 1 else 95.0
                }

            # Diagnose errors
            diag_res = global_debug_analyzer.analyze_errors(exec_res.get("errors", []))

            # Apply fixes
            fix_res = global_automatic_fixer.apply_fixes(current_files, diag_res["diagnostics"])
            current_files = fix_res["patched_files"]

            history.append({
                "attempt": attempt,
                "errors_found": len(exec_res.get("errors", [])),
                "fixes_applied": fix_res["fixes_applied_count"]
            })

            # Break if no fixes could be applied
            if fix_res["fixes_applied_count"] == 0:
                break

        final_check = global_project_execution_engine.execute_project(current_files)
        return {
            "status": "healthy" if final_check["is_healthy"] else "unresolved",
            "attempts": len(history) + 1,
            "final_files": current_files,
            "history": history,
            "self_healing_score": 100.0 if final_check["is_healthy"] else 60.0
        }


# Global SelfHealingRetryEngine Instance
global_self_healing_retry_engine = SelfHealingRetryEngine()
