import logging
import asyncio
from typing import Dict, Any, Tuple
from backend.monitoring.health_checker import HealthChecker

_logger = logging.getLogger("aiforge.sre")

class RecoveryValidator:
    """
    Validates the effectiveness of executed self-healing recovery actions.
    Executes deep dependency testing, latency checks, and confirms system recovery status.
    """

    def __init__(self, health_checker: HealthChecker) -> None:
        self.health_checker = health_checker

    async def validate_recovery(self) -> Tuple[bool, str]:
        """
        Runs validations and returns (success: bool, validation_report_text: str).
        """
        _logger.info("Executing post-recovery verification tests...")
        
        # 1. Wait briefly for services to finish booting / re-establishing sockets
        await asyncio.sleep(2.0)
        
        # 2. Trigger comprehensive health checks
        check_report = await self.health_checker.run_comprehensive_check()
        health_score = check_report.get("health_score", 0)

        checks = check_report.get("checks", {})
        api_chk = checks.get("api", {})
        db_chk = checks.get("database", {})
        ollama_chk = checks.get("ollama", {})

        report_lines = [
            "Post-Recovery Diagnostics:",
            f"- System Health Score: {health_score}/100",
            f"- API Health: {api_chk.get('status')}",
            f"- Database Health: {db_chk.get('status')}",
            f"- Ollama Engine Health: {ollama_chk.get('status')}"
        ]

        if health_score >= 80:
            success_msg = "Verification SUCCESS: System has returned to normal healthy bounds."
            report_lines.append(success_msg)
            _logger.info(success_msg)
            return True, "\n".join(report_lines)
        
        fail_msg = "Verification FAILURE: Critical system dependencies remain degraded."
        report_lines.append(fail_msg)
        _logger.error(fail_msg)
        return False, "\n".join(report_lines)
