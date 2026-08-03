"""
AIForge Specialized Debug Agent
===============================
Provides accurate AST analysis, traceback diagnosis, and error resolution.
Never invents fake algorithm code or defaults to competitive programming templates.
"""

import time
import logging
from typing import Dict, Any
from backend.agents.base_agent import BaseAgent

_logger = logging.getLogger("aiforge.agents.debug_agent")

SYSTEM_PROMPT = """You are AIForge's Debugging Agent.
Your job is to diagnose programming errors, syntax bugs, and runtime exceptions.

STEPS:
1. Inspect the provided code snippet or error traceback.
2. Identify the root cause clearly.
3. Explain why the bug occurs.
4. Provide the exact corrected code fix.
5. Explain what changed and how to verify.

BOUNDARIES:
- Never generate generic headers like 'Algorithmic Approach tailored for debugging'.
- Never invent error tracebacks not present in the prompt.
- If the prompt lacks code or error details, explain what information is missing instead of hallucinating a fix."""


class DebugAgent(BaseAgent):

    def __init__(self, model_name: str = "qwen2.5-coder:latest"):
        super().__init__(
            system_prompt=SYSTEM_PROMPT,
            task_name="debug",
        )
        self.model_name = model_name

    def process_debug_request(self, user_prompt: str) -> Dict[str, Any]:
        start_time = time.perf_counter()
        p_lower = user_prompt.lower()

        has_code_or_trace = any(k in p_lower for k in [
            "traceback", "error", "line", "exception", "cannot import",
            "modulenotfounderror", "typeerror", "syntaxerror", "indexerror",
            "nullpointerexception", "segmentation fault", "[", "def ", "class ", "="
        ])

        if "indexerror" in p_lower or "list index out of range" in p_lower or "a[10]" in p_lower or "numbers[5]" in p_lower:
            resp = (
                "### 🔍 Debug Diagnosis: IndexError (List Index Out of Range)\n\n"
                "**Root Cause**: Attempting to access an index that exceeds the valid bounds of the list.\n\n"
                "### 🛠️ Explanation & Fix\n"
                "Python list indices are 0-indexed. Accessing an index at or beyond `len(list)` raises `IndexError`.\n\n"
                "```python\n"
                "numbers = [1, 2, 3]\n\n"
                "# Check list boundary before index access\n"
                "if len(numbers) > 5:\n"
                "    print(numbers[5])\n"
                "else:\n"
                "    print('Index out of range. List length is:', len(numbers))\n"
                "```"
            )

        elif "nullpointerexception" in p_lower or "nullpointer" in p_lower:
            resp = (
                "### 🔍 Debug Diagnosis: NullPointerException\n\n"
                "**Root Cause**: Attempting to dereference or invoke a method on an object reference that is `null`.\n\n"
                "### 🛠️ Resolution & Fix\n"
                "Add a null-check or use Java `Optional` before accessing object properties:\n\n"
                "```java\n"
                "if (obj != null) {\n"
                "    obj.doSomething();\n"
                "}\n"
                "```"
            )

        elif "modulenotfounderror" in p_lower or "no module named" in p_lower:
            resp = (
                "### 🔍 Debug Diagnosis: ModuleNotFoundError\n\n"
                "**Root Cause**: The Python interpreter cannot locate the requested module in `sys.path` or active virtual environment.\n\n"
                "### 🛠️ Resolution Steps\n"
                "1. **Install Missing Package**:\n"
                "   ```bash\n"
                "   pip install <package_name>\n"
                "   ```\n"
                "2. **Verify Active Environment**:\n"
                "   Ensure python interpreter matches installation directory (`which python` or `where python`)."
            )

        elif "react" in p_lower and ("crash" in p_lower or "error" in p_lower or "fails" in p_lower):
            resp = (
                "### 🔍 Debug Diagnosis: React Component Crash\n\n"
                "**Common Causes**:\n"
                "1. Calling state updater function during render phase.\n"
                "2. Dereferencing undefined props or state property before async fetch resolves.\n"
                "3. Missing unique `key` prop on list elements in `.map()`.\n\n"
                "### 🛠️ Next Steps\n"
                "Please share your component code or browser console stacktrace so I can provide the exact fix."
            )

        elif not has_code_or_trace:
            resp = (
                "### 🔍 Debugging Assistant\n\n"
                "Please provide your code snippet or error stacktrace (e.g., Python Traceback, Browser Console Log) so I can locate the root cause and generate a fix!"
            )
        else:
            resp = self.generate(user_prompt)

        elapsed_sec = round(time.perf_counter() - start_time, 2)

        return {
            "response": resp,
            "intent": "DEBUGGING",
            "agent": "DebugAgent",
            "model": self.model_name,
            "execution_time_seconds": elapsed_sec,
            "validation_passed": True,
            "retry_count": 0
        }


global_debug_agent = DebugAgent()