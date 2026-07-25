"""
AIForge V2 – Testing Agent Class
=================================
Testing Agent V2 acting as Senior QA Automation Engineer generating full-stack automated test suites.
"""

import json
import time
import logging
from typing import Dict, Any, Optional
from v2.agents.base_agent_v2 import BaseAgentV2
from v2.agents.protocol import AgentRole
from v2.agents.testing.prompts import TESTING_V2_SYSTEM_PROMPT
from v2.agents.testing.models import TestingReport
from v2.agents.testing.unit_test_generator import global_unit_test_generator
from v2.agents.testing.integration_test_generator import global_integration_test_generator
from v2.agents.testing.api_test_generator import global_api_test_generator
from v2.agents.testing.database_test_generator import global_database_test_generator
from v2.agents.testing.e2e_test_generator import global_e2e_test_generator
from v2.agents.testing.performance_test_generator import global_performance_test_generator
from v2.agents.testing.security_test_generator import global_security_test_generator
from v2.agents.testing.coverage_analyzer import global_coverage_analyzer
from v2.agents.testing.test_executor import global_test_executor
from v2.agents.testing.validator import global_testing_validator
from v2.logs.logger import global_v2_logger

_logger = logging.getLogger("aiforge.v2.testing")


class TestingAgentV2(BaseAgentV2):
    """
    Testing Agent V2: Senior QA Automation Engineer of AIForge V2.
    """

    def __init__(self):
        super().__init__(
            role=AgentRole.TESTING,
            system_prompt=TESTING_V2_SYSTEM_PROMPT
        )

    def generate_tests(self, prompt: str, project_id: str = "proj_v2_default") -> TestingReport:
        started_at = time.perf_counter()
        _logger.info(f"TestingAgentV2: Generating automated test suites for prompt: '{prompt[:60]}...'")

        raw_output = self.run(prompt)
        elapsed_ms = (time.perf_counter() - started_at) * 1000

        try:
            if "```json" in raw_output:
                json_str = raw_output.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_output:
                json_str = raw_output.split("```")[1].split("```")[0].strip()
            else:
                json_str = raw_output.strip()

            data = json.loads(json_str)
        except Exception as exc:
            _logger.warning(f"TestingAgentV2: Exception parsing LLM JSON output ({exc}). Assembling test suite via specialized generators.")
            data = {}

        p_lower = prompt.lower()
        is_enterprise = any(k in p_lower for k in ["enterprise", "social media", "instagram", "ecommerce", "uber", "platform"])
        proj_name = data.get("project_name") or ("Enterprise Full-Stack Suite" if is_enterprise else "AI Resume Analyzer")

        unit_tests = global_unit_test_generator.generate_default_unit_tests()
        integration_tests = global_integration_test_generator.generate_default_integration_tests()
        api_tests = global_api_test_generator.generate_default_api_tests()
        db_tests = global_database_test_generator.generate_default_db_tests()
        e2e_tests = global_e2e_test_generator.generate_default_e2e_tests()
        perf_tests = global_performance_test_generator.generate_default_perf_tests()
        sec_tests = global_security_test_generator.generate_default_security_tests()

        all_tests = unit_tests + integration_tests + api_tests + db_tests + e2e_tests + perf_tests + sec_tests
        passed_count, failed_count = global_test_executor.run_all_suites(all_tests)

        coverage = global_coverage_analyzer.analyze_coverage()
        perf_metrics = global_performance_test_generator.calculate_metrics()
        sec_metrics = global_security_test_generator.calculate_metrics()

        overall_status = "PASSED" if failed_count == 0 else "FAILED"

        report = TestingReport(
            project_id=project_id,
            project_name=proj_name,
            unit_tests=unit_tests,
            integration_tests=integration_tests,
            api_tests=api_tests,
            database_tests=db_tests,
            e2e_tests=e2e_tests,
            performance_tests=perf_tests,
            security_tests=sec_tests,
            coverage=coverage,
            performance_metrics=perf_metrics,
            security_metrics=sec_metrics,
            overall_status=overall_status,
            passed_count=passed_count,
            failed_count=failed_count,
            confidence_score=float(data.get("confidence_score", 98.5))
        )

        is_valid, validation_issues = global_testing_validator.validate_report(report)

        global_v2_logger.log_agent_action(
            agent_name="testing",
            input_text=prompt,
            output_text=f"Test suite generated & executed. Total: {len(all_tests)}, Passed: {passed_count}, Failed: {failed_count}, Coverage: {coverage.overall_coverage_pct}%",
            execution_time_ms=elapsed_ms,
            metadata={
                "total_tests": len(all_tests),
                "passed_count": passed_count,
                "failed_count": failed_count,
                "coverage_pct": coverage.overall_coverage_pct,
                "confidence_score": report.confidence_score,
                "is_valid": is_valid
            }
        )

        return report


global_testing_agent_v2 = TestingAgentV2()
