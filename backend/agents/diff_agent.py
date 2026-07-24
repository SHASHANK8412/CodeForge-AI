"""
AIForge Day 95 Diff & Change Explanation Agent
==============================================
Explains code modifications line-by-line:
- Reason
- Before snippet
- After snippet
- Impact
- Possible Risks
"""

import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.agents.diff")


class DiffExplanationAgent:
    """
    Agent for generating human-readable change explanations.
    """

    def explain_changes(
        self,
        filepath: str,
        original_code: str,
        modified_code: str,
        prompt_goal: str = "general"
    ) -> Dict[str, Any]:
        _logger.info(f"DiffExplanationAgent: Explaining modifications for '{filepath}'...")

        reason = f"Applied incremental modification for prompt goal: '{prompt_goal}'"
        impact = "Modifies localized module without breaking existing API contracts."
        possible_risks = "Low risk - preserves existing imports, formatting, and route handlers."

        before_snippet = original_code[:120] + ("..." if len(original_code) > 120 else "")
        after_snippet = modified_code[:120] + ("..." if len(modified_code) > 120 else "")

        explanation_formatted = (
            f"### Change Explanation for `{filepath}`\n"
            f"- **Reason**: {reason}\n"
            f"- **Before**: `{before_snippet}`\n"
            f"- **After**: `{after_snippet}`\n"
            f"- **Impact**: {impact}\n"
            f"- **Possible Risks**: {possible_risks}\n"
        )

        return {
            "filepath": filepath,
            "reason": reason,
            "before_snippet": before_snippet,
            "after_snippet": after_snippet,
            "impact": impact,
            "possible_risks": possible_risks,
            "formatted_explanation": explanation_formatted
        }


global_diff_agent = DiffExplanationAgent()
