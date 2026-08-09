"""
AIForge Response Contract Verification Utility
=============================================
Provides lightweight contract checks ensuring generated agent responses adhere to intent boundaries.
Logs warnings when contract violations (e.g., coding templates in non-code explanations) are detected.
"""

import logging
from typing import Dict, Any

_logger = logging.getLogger("aiforge.response_contract")


def validate_response_contract(intent: str, prompt: str, response: str) -> Dict[str, Any]:
    """
    Validates whether the generated assistant response adheres to the response contract for its Intent.
    Returns: {"valid": bool, "reason": str}
    """
    if not response or not response.strip():
        return {"valid": False, "reason": "Empty response received."}

    p_lower = prompt.lower()
    r_lower = response.lower()
    intent_upper = (intent or "").upper()

    # 1. EXPLANATION & GENERAL_QA CONTRACT
    if intent_upper in ["EXPLANATION", "GENERAL_QA"]:
        # Non-programming explanation topics (e.g. Formula 1, Photosynthesis, Airplanes, General Trivia)
        non_programming = any(topic in p_lower for topic in [
            "formula 1", "f1", "photosynthesis", "airplane", "airplanes", "fly", "cricket",
            "football", "telephone", "france", "everest", "hamlet", "inflation", "gdp"
        ]) or not any(tech in p_lower for tech in [
            "code", "python", "java", "c++", "script", "function", "api", "react", "algorithm", "binary search", "bfs", "dfs", "sort"
        ])

        if non_programming:
            forbidden_coding_markers = [
                "def solve", "problem approach", "algorithmic approach", "time complexity: o(", "space complexity: o("
            ]
            for marker in forbidden_coding_markers:
                if marker in r_lower and marker not in p_lower:
                    _logger.warning(f"[Response Contract Warning] Intent: {intent_upper} | Prompt: '{prompt[:40]}' | Unexpected coding marker detected: '{marker}'")
                    return {
                        "valid": False,
                        "reason": f"Non-programming explanation contains forbidden coding marker: '{marker}'"
                    }

    # 2. DEBUGGING CONTRACT
    elif intent_upper == "DEBUGGING":
        if "def solve_solve_" in r_lower:
            _logger.warning(f"[Response Contract Warning] Intent: DEBUGGING | Prompt: '{prompt[:40]}' | Unexpected fake algorithm solver detected.")
            return {"valid": False, "reason": "Debugging response contains fake algorithm solver."}

    # 3. RESUME CONTRACT
    elif intent_upper == "RESUME":
        if "def solve" in r_lower or "algorithmic approach" in r_lower:
            _logger.warning(f"[Response Contract Warning] Intent: RESUME | Prompt: '{prompt[:40]}' | Unexpected coding template detected in resume response.")
            return {"valid": False, "reason": "Resume response contains coding template."}

    return {"valid": True, "reason": "Contract validation passed cleanly."}
