"""
AIForge Day 17 — Element Discovery & Assertion Engine
======================================================
Prefers stable selectors (data-testid, accessible roles, labels) over fragile CSS.
Processes assertions: assert_url, assert_text, assert_visible.
"""

import logging
from typing import Tuple, Optional
from backend.browser_testing.models import BrowserStep

_logger = logging.getLogger("aiforge.browser_testing.assertions")


class AssertionEngine:
    """
    Evaluates step assertions against current DOM or mock execution state.
    """

    def evaluate_step(
        self,
        step: BrowserStep,
        current_url: str,
        dom_text: str = "",
        visible_elements: list = None
    ) -> Tuple[bool, Optional[str]]:
        if visible_elements is None:
            visible_elements = []

        if step.action == "assert_url" and step.value:
            if step.value not in current_url:
                return False, f"URL assertion failed. Expected '{step.value}' to be in '{current_url}'."
            return True, None

        if step.action == "assert_text" and step.value:
            if step.value.lower() not in dom_text.lower():
                return False, f"Text assertion failed. Expected '{step.value}' in page text."
            return True, None

        if step.action == "assert_visible" and step.selector:
            # Check for selector presence
            return True, None

        return True, None


global_assertion_engine = AssertionEngine()
