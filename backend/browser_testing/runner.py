"""
AIForge Day 17 — Scenario Execution Runner
==========================================
Orchestrates test scenarios inside isolated environment and collects results.
"""

import logging
from typing import List

from backend.browser_testing.models import BrowserScenario, BrowserTestResult
from backend.browser_testing.browser_manager import global_browser_manager

_logger = logging.getLogger("aiforge.browser_testing.runner")


class BrowserTestRunner:
    """
    Executes a list of scenarios sequentially or in parallel inside Docker sandbox.
    """

    def run_scenarios(
        self,
        project_id: str,
        scenarios: List[BrowserScenario],
        base_url: str = "http://localhost:3000"
    ) -> List[BrowserTestResult]:
        results: List[BrowserTestResult] = []
        for scen in scenarios:
            res = global_browser_manager.execute_scenario(project_id, scen, base_url)
            results.append(res)
        return results


global_test_runner = BrowserTestRunner()
