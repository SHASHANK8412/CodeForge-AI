"""
AIForge Response Cleaner Utility
================================
Runs ONLY after output validation passes.
Performs safe, lightweight formatting cleanup without modifying substantive response content.
"""

import re


class ResponseCleaner:
    """
    Lightweight deterministic response cleaner.
    """

    def clean(self, response: str) -> str:
        """
        Cleans accepted response string safely:
        1. Trims leading/trailing whitespace.
        2. Normalizes excessive consecutive blank lines (>2 to 2).
        3. Safely balances unclosed code fences if missing trailing ```.
        4. Preserves Markdown and code formatting.
        """
        if not response:
            return ""

        cleaned = response.strip()

        # 1. Normalize 3+ newlines to max 2 newlines (preserve paragraph spacing)
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

        # 2. Check balanced code fences safely
        # Count non-escaped triple backtick occurrences
        backtick_matches = re.findall(r'```', cleaned)
        if len(backtick_matches) % 2 != 0:
            # Unclosed code block detected - safely append closing code fence
            cleaned += "\n```"

        return cleaned


global_response_cleaner = ResponseCleaner()
