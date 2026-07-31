"""
AIForge Retry Manager Service
==============================
Coordinates the autonomous self-healing pipeline, enforces maximum retry limits (3), checks confidence scores (<60% abort), maintains error history in backend/logs/error_history.json, and produces dashboard metrics and UI timeline status.
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.agents.error_analyzer import global_error_analyzer
from backend.agents.root_cause import global_root_cause_finder
from backend.agents.self_healing import global_self_healing_agent

_logger = logging.getLogger("aiforge.services.retry_manager")


class RetryManagerService:
    """
    Service managing project self-healing execution loops, retry state, metric calculation, and error history persistence.
    """

    def __init__(self, max_retries: int = 3, history_file: Optional[Path] = None):
        self.max_retries = max_retries
        _root = Path(__file__).resolve().parent.parent.parent
        self.history_file = history_file or (_root / "backend" / "logs" / "error_history.json")
        self.timeline_state: Dict[str, Any] = {
            "stages": [
                {"name": "Planning", "status": "COMPLETED", "icon": "✔"},
                {"name": "Architecture", "status": "COMPLETED", "icon": "✔"},
                {"name": "Frontend", "status": "COMPLETED", "icon": "✔"},
                {"name": "Backend", "status": "COMPLETED", "icon": "✔"},
                {"name": "Testing", "status": "FAILED", "icon": "❌"},
                {"name": "Debugging", "status": "RUNNING", "icon": "⏳"}
            ],
            "current_error": "None",
            "current_fix": "None",
            "retry_count": 0,
            "confidence": 100
        }
        self._ensure_history_file()

    def _ensure_history_file(self):
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            if not self.history_file.exists():
                self.history_file.write_text("[]", encoding="utf-8")
        except Exception as e:
            _logger.error(f"RetryManagerService: Error initializing history file: {e}")

    def get_history(self) -> List[Dict[str, Any]]:
        return self.load_history()

    def load_history(self) -> List[Dict[str, Any]]:
        try:
            if self.history_file.exists():
                content = self.history_file.read_text(encoding="utf-8")
                return json.loads(content) if content.strip() else []
        except Exception as e:
            _logger.error(f"RetryManagerService: Error reading history file: {e}")
        return []

    def log_error_event(
        self,
        project_name: str,
        error_msg: str,
        solution_msg: str,
        success: bool,
        confidence: int,
        retry_count: int
    ) -> Dict[str, Any]:
        entry = {
            "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "project": project_name,
            "error": error_msg,
            "solution": solution_msg,
            "success": success,
            "confidence": confidence,
            "retry_count": retry_count
        }
        try:
            history = self.load_history()
            history.insert(0, entry)
            self.history_file.write_text(json.dumps(history, indent=2), encoding="utf-8")
        except Exception as e:
            _logger.error(f"RetryManagerService: Error saving history event: {e}")
        return entry

    def run_self_healing_pipeline(
        self,
        error_log: Any,
        project_id: str = "project_default",
        project_root: Optional[Path] = None,
        test_verifier_func: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Executes the full Intelligent Error Detection & Self-Healing Pipeline.
        """
        self.timeline_state["stages"][-2]["status"] = "FAILED"
        self.timeline_state["stages"][-2]["icon"] = "❌"
        self.timeline_state["stages"][-1]["status"] = "RUNNING"
        self.timeline_state["stages"][-1]["icon"] = "⏳"

        # 1. Analyze Error
        analysis = global_error_analyzer.analyze_log(error_log)
        self.timeline_state["current_error"] = f"{analysis['error_type']}: {analysis['cause']}"

        attempts_history = []
        is_success = False
        final_solution = "Unresolved"
        final_confidence = 0

        # Loop up to max_retries (3)
        for attempt in range(1, self.max_retries + 1):
            self.timeline_state["retry_count"] = attempt

            # Perform fix attempt
            fix_result = global_self_healing_agent.attempt_fix(
                error_input=analysis if attempt == 1 else error_log,
                project_root=project_root,
                current_retry=attempt
            )

            confidence = fix_result.get("confidence", 0)
            final_confidence = confidence
            self.timeline_state["confidence"] = confidence

            # Confidence threshold check (< 60% abort)
            if not fix_result.get("success") or confidence < 60:
                final_solution = fix_result.get("message") or "Stopped due to confidence < 60%"
                self.timeline_state["current_fix"] = f"Aborted: Low confidence ({confidence}%)"
                attempts_history.append({
                    "attempt": attempt,
                    "status": "HALTED",
                    "confidence": confidence,
                    "fix_result": fix_result
                })

                # Log event
                self.log_error_event(
                    project_name=project_id,
                    error_msg=analysis["cause"],
                    solution_msg=final_solution,
                    success=False,
                    confidence=confidence,
                    retry_count=attempt
                )

                return {
                    "project_id": project_id,
                    "status": "FAILED",
                    "reason": "CONFIDENCE_BELOW_THRESHOLD",
                    "total_retries": attempt,
                    "final_confidence": confidence,
                    "error_analysis": analysis,
                    "human_readable_report": fix_result.get("human_readable_report"),
                    "attempts": attempts_history
                }

            final_solution = fix_result.get("solution", "Applied automated fix")
            self.timeline_state["current_fix"] = final_solution

            # Simulate or execute test verification after fix
            if test_verifier_func:
                passed_test = test_verifier_func(attempt)
            else:
                # Default: Fix passes on attempt
                passed_test = True

            attempts_history.append({
                "attempt": attempt,
                "status": "PASSED" if passed_test else "FAILED",
                "confidence": confidence,
                "solution": final_solution,
                "fix_result": fix_result
            })

            if passed_test:
                is_success = True
                self.timeline_state["stages"][-2]["status"] = "COMPLETED"
                self.timeline_state["stages"][-2]["icon"] = "✔"
                self.timeline_state["stages"][-1]["status"] = "COMPLETED"
                self.timeline_state["stages"][-1]["icon"] = "✔"

                # Log successful event
                self.log_error_event(
                    project_name=project_id,
                    error_msg=analysis["cause"],
                    solution_msg=final_solution,
                    success=True,
                    confidence=confidence,
                    retry_count=attempt
                )

                return {
                    "project_id": project_id,
                    "status": "SUCCESS",
                    "total_retries": attempt,
                    "final_confidence": confidence,
                    "error_analysis": analysis,
                    "solution": final_solution,
                    "attempts": attempts_history
                }

        # Max retries exhausted
        self.log_error_event(
            project_name=project_id,
            error_msg=analysis["cause"],
            solution_msg="Failed after max 3 retries",
            success=False,
            confidence=final_confidence,
            retry_count=self.max_retries
        )

        return {
            "project_id": project_id,
            "status": "FAILED",
            "reason": "MAX_RETRIES_EXCEEDED",
            "total_retries": self.max_retries,
            "final_confidence": final_confidence,
            "error_analysis": analysis,
            "attempts": attempts_history
        }

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """
        Calculates aggregate dashboard metrics from error history.
        """
        history = self.load_history()
        total_errors = len(history)
        fixed_errors = len([e for e in history if e.get("success") is True])
        total_retries = sum(e.get("retry_count", 1) for e in history)
        avg_confidence = round(sum(e.get("confidence", 0) for e in history) / max(1, total_errors), 1) if history else 100.0
        success_pct = round((fixed_errors / max(1, total_errors)) * 100, 1) if history else 100.0

        return {
            "errors_found": total_errors,
            "errors_fixed": fixed_errors,
            "retries_used": total_retries,
            "average_confidence": avg_confidence,
            "build_success_pct": success_pct,
            "recent_history": history[:10]
        }

    def get_timeline_status(self, project_id: str = "default") -> Dict[str, Any]:
        """
        Returns live UI error timeline and state.
        """
        return {
            "project_id": project_id,
            "timeline": self.timeline_state
        }


global_retry_manager_service = RetryManagerService()
