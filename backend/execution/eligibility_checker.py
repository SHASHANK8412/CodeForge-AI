"""
AIForge Execution Eligibility Checker
======================================
Determines whether a generated candidate response should enter the isolated
sandbox execution pipeline.
"""

import os
import re
import logging
from typing import Optional, Any
from backend.execution.models import ExecutionDecision, ExecutionType

_logger = logging.getLogger("aiforge.execution.eligibility")


class ExecutionEligibilityChecker:
    """
    Evaluates request eligibility for sandbox code execution.
    """

    NON_EXECUTABLE_INTENTS = {"GENERAL_QA", "EXPLANATION", "RAG_QUERY", "RESUME"}

    NON_EXECUTABLE_KEYWORDS = [
        "what is", "explain", "how does", "capital of", "interview advice",
        "resume", "jd", "career", "docker concept", "rest concept"
    ]

    def check_eligibility(
        self,
        intent: str,
        user_prompt: str,
        response_text: str,
        execution_strategy: str = "STANDARD"
    ) -> ExecutionDecision:
        enabled = os.environ.get("AIFORGE_CODE_EXECUTION_ENABLED", "true").lower() in ["true", "1", "yes"]
        if not enabled:
            return ExecutionDecision(should_execute=False, execution_type=ExecutionType.STATIC_ONLY, reason="FEATURE_DISABLED")

        prompt_clean = user_prompt.lower()

        # Rule 1: Non-code intents -> NEVER EXECUTE (0 Sandbox Overhead)
        if intent in self.NON_EXECUTABLE_INTENTS and not any(kw in prompt_clean for kw in ["python code", "write function", "implement algorithm"]):
            return ExecutionDecision(should_execute=False, execution_type=ExecutionType.STATIC_ONLY, reason="NON_CODING_INTENT")

        # Rule 2: Explicit non-coding query patterns & architecture design -> NEVER EXECUTE
        if any(prompt_clean.startswith(kw) for kw in self.NON_EXECUTABLE_KEYWORDS) or any(kw in prompt_clean for kw in ["architecture", "system design", "specifications"]):
            return ExecutionDecision(should_execute=False, execution_type=ExecutionType.STATIC_ONLY, reason="NON_CODING_PROMPT")

        # Rule 3: Detect language & code blocks in response
        has_python = ("def " in response_text or "```python" in response_text or "python" in prompt_clean)
        has_js = ("function " in response_text or "const " in response_text or "```javascript" in response_text or "javascript" in prompt_clean)
        has_java = ("class " in response_text and "public static void main" in response_text) or ("java" in prompt_clean and "class " in response_text)

        if not (has_python or has_js or has_java):
            return ExecutionDecision(should_execute=False, execution_type=ExecutionType.STATIC_ONLY, reason="NO_STANDALONE_CODE")

        lang = "python"
        if has_java:
            lang = "java"
        elif has_js:
            lang = "javascript"

        exec_type = ExecutionType.RUN
        if "test" in prompt_clean or "binary search" in prompt_clean or "lru" in prompt_clean or "palindrome" in prompt_clean:
            exec_type = ExecutionType.TEST

        return ExecutionDecision(
            should_execute=True,
            execution_type=exec_type,
            language=lang,
            reason="EXECUTABLE_CODE"
        )


global_execution_eligibility_checker = ExecutionEligibilityChecker()
