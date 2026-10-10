"""
AIForge Day 17 — Scenario Validator & Safety Engine
===================================================
Ensures AI-generated browser test steps do not navigate outside the sandbox,
execute host commands, or perform real destructive operations.
"""

import logging
from typing import Tuple
from backend.browser_testing.models import BrowserScenario

_logger = logging.getLogger("aiforge.browser_testing.scenario")

DISALLOWED_URL_SCHEMES = ("file://", "gopher://", "ftp://")
ALLOWED_HOSTS = ("localhost", "127.0.0.1", "0.0.0.0", "sandbox", "aiforge.internal")


class ScenarioValidator:
    """
    Validates browser scenarios for security and execution safety.
    """

    def validate_scenario(self, scenario: BrowserScenario) -> Tuple[bool, str]:
        if not scenario.steps:
            return False, "Scenario contains no execution steps."

        for idx, step in enumerate(scenario.steps):
            if step.action == "navigate" and step.url:
                url_lower = step.url.lower()
                if any(scheme in url_lower for scheme in DISALLOWED_URL_SCHEMES):
                    return False, f"Step {idx + 1}: Disallowed URL scheme in '{step.url}'."

                if url_lower.startswith("http://") or url_lower.startswith("https://"):
                    # Must stay within sandbox or localhost
                    if not any(h in url_lower for h in ALLOWED_HOSTS):
                        return False, f"Step {idx + 1}: Navigation outside sandbox application '{step.url}' is forbidden."

            if step.selector:
                if "shell" in step.selector.lower() or "cmd" in step.selector.lower():
                    return False, f"Step {idx + 1}: Invalid selector '{step.selector}'."

        return True, "Valid"


global_scenario_validator = ScenarioValidator()
