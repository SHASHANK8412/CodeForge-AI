"""
AIForge Retry Manager & Escalation Engine
==========================================
Manages configurable retry limits for autonomous self-healing execution and escalates unresolvable failures to human review.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from backend.self_healing.error_monitor import global_error_monitor
from backend.self_healing.root_cause import global_root_cause_analyzer
from backend.self_healing.fix_generator import global_fix_generator
from backend.self_healing.learning_store import global_learning_store
from backend.approvals.approval_manager import global_approval_manager

_logger = logging.getLogger("aiforge.self_healing.retry")


class RetryManager:
    """
    Manages retry loops and escalation policies.
    """

    def __init__(self, max_retries: int = 3) -> None:
        self.max_retries = max_retries
        self.retry_records: Dict[str, Dict[str, Any]] = {}

    def execute_self_healing_attempt(self, error_report: Dict[str, Any]) -> Dict[str, Any]:
        error_id = error_report.get("error_id", f"err_{int(time.time())}")
        
        if error_id not in self.retry_records:
            self.retry_records[error_id] = {
                "error_id": error_id,
                "attempts": 0,
                "max_retries": self.max_retries,
                "history": [],
                "status": "IN_PROGRESS"
            }

        rec = self.retry_records[error_id]
        rec["attempts"] += 1
        attempt_num = rec["attempts"]

        _logger.info(f"RetryManager: Attempt {attempt_num}/{self.max_retries} for error '{error_id}'")

        if attempt_num <= self.max_retries:
            # 1. Perform Root Cause Analysis
            rca = global_root_cause_analyzer.analyze(error_report)

            # 2. Generate and apply fix
            fix = global_fix_generator.generate_and_apply_fix(rca)

            # 3. Store lesson in knowledge base
            lesson = global_learning_store.record_lesson(
                problem=error_report.get("message", "Failure"),
                root_cause=rca["root_cause"],
                solution=rca["recommended_fix"],
                was_successful=fix["validation_status"] == "SUCCESS"
            )

            rec["status"] = "RESOLVED"
            global_error_monitor.update_error_status(error_id, "RESOLVED")

            attempt_result = {
                "attempt": attempt_num,
                "status": "SUCCESS",
                "rca": rca,
                "fix": fix,
                "lesson": lesson
            }
            rec["history"].append(attempt_result)
            return {
                "error_id": error_id,
                "status": "RESOLVED",
                "attempt": attempt_num,
                "escalated": False,
                "result": attempt_result
            }
        else:
            # Escalate to human review
            rec["status"] = "ESCALATED"
            global_error_monitor.update_error_status(error_id, "ESCALATED")

            appr_req = global_approval_manager.create_approval_request(
                title=f"Human Review Required: Unresolved Error in {error_report.get('file', 'code')}",
                reason=f"Self-healing failed after {self.max_retries} retry attempts: {error_report.get('message')}",
                affected_files=[error_report.get('file', 'main.py')],
                risk="High",
                requested_by="Self-Healing RetryManager"
            )

            _logger.warning(f"RetryManager: Escalated error '{error_id}' to human review after {attempt_num} attempts.")

            return {
                "error_id": error_id,
                "status": "ESCALATED",
                "attempt": attempt_num,
                "escalated": True,
                "approval_request": appr_req
            }

    def get_self_healing_dashboard(self) -> Dict[str, Any]:
        errors = global_error_monitor.get_errors()
        lessons = global_learning_store.get_all_lessons()
        resolved_count = len([e for e in errors if e.get("status") == "RESOLVED"])
        total_errors = len(errors)
        success_rate = round((resolved_count / max(1, total_errors)) * 100, 1)

        return {
            "timestamp": time.time(),
            "metrics": {
                "total_errors_detected": total_errors,
                "automatically_resolved": resolved_count,
                "success_rate_percentage": success_rate,
                "total_lessons_learned": len(lessons)
            },
            "active_errors": errors,
            "reusable_lessons": lessons,
            "retry_records": list(self.retry_records.values())
        }


global_retry_manager = RetryManager()
