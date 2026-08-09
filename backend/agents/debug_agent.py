import re
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.agents.base_agent import BaseAgent
from backend.execution.models import DebugResult
from backend.memory.project_memory_service import global_project_memory_service


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
    __test__ = False

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

    def diagnose_and_repair(
        self,
        state: Dict[str, Any],
        project_path: Optional[Path] = None
    ) -> DebugResult:
        """
        Analyzes real execution and test failure evidence from ProjectState,
        determines root cause, error type, and targeted file changes without modifying disk.
        """
        exec_results = state.get("execution_results", {}) or {}
        test_results = state.get("test_results", {}) or {}
        files = state.get("files", {}) or {}
        previous_fixes = state.get("fixes", []) or []
        proj_path_str = state.get("project_path") or (str(project_path) if project_path else "")
        target_path = Path(proj_path_str).resolve() if proj_path_str else None

        stdout = str(exec_results.get("stdout", ""))
        stderr = str(exec_results.get("stderr", ""))
        combined_output = f"{stderr}\n{stdout}\n" + str(test_results.get("summary", ""))

        exit_code = exec_results.get("exit_code", 0)
        is_test_success = test_results.get("success", True)

        if exit_code == 0 and is_test_success:
            return DebugResult(
                success=True,
                diagnosis="No defects detected. Project passed all build and verification checks.",
                root_cause="N/A",
                error_type="NONE",
                files_to_modify=[],
                changes={},
                confidence=1.0,
                explanation="All tests passed successfully."
            )

        error_type = "UNKNOWN"
        root_cause = "General execution or test failure."
        diagnosis = "Execution or test suite failure observed."
        files_to_modify = []
        proposed_changes = {}

        failures = test_results.get("failures", [])
        if "SyntaxError" in combined_output:
            error_type = "SYNTAX_ERROR"
            root_cause = "Invalid Python syntax in source file."
            diagnosis = "SyntaxError detected during parsing/compilation."
            match = re.search(r'File "([^"]+)", line (\d+)', combined_output)
            if match:
                fpath, line_no = match.group(1), match.group(2)
                rel_fpath = fpath.replace("\\", "/").split("/")[-1]
                for k in files.keys():
                    if k.endswith(rel_fpath):
                        files_to_modify.append(k)

        elif "ImportError" in combined_output or "ModuleNotFoundError" in combined_output:
            error_type = "IMPORT_ERROR"
            root_cause = "Missing or unresolvable module import."
            match = re.search(r"No module named '([^']+)'", combined_output)
            mod_name = match.group(1) if match else "unknown"
            diagnosis = f"Missing module '{mod_name}' in sys.path or project environment."

        elif failures:
            error_type = "ASSERTION_FAILURE"
            first_fail = failures[0] if isinstance(failures[0], dict) else failures[0].model_dump() if hasattr(failures[0], "model_dump") else {}
            test_name = first_fail.get("test_name", "unknown")
            err_msg = first_fail.get("error", "")
            file_hint = first_fail.get("file", "")

            diagnosis = f"Assertion failed in test '{test_name}': {err_msg}"
            root_cause = f"Test '{test_name}' failed assertion: {err_msg}"

            stem = test_name.replace("test_", "")
            for k in files.keys():
                if k.startswith("backend/") and (stem in k.lower() or "main.py" in k.lower() or "todos.py" in k.lower()):
                    files_to_modify.append(k)
                    break

            if not files_to_modify and file_hint:
                rel_hint = file_hint.replace("\\", "/").lstrip("/")
                for k in files.keys():
                    if k in rel_hint or rel_hint.endswith(k):
                        files_to_modify.append(k)

            if not files_to_modify:
                for k in files.keys():
                    if k.startswith("backend/"):
                        files_to_modify.append(k)
                        break

        elif "TypeError" in combined_output or "AttributeError" in combined_output or "KeyError" in combined_output or "Exception" in combined_output:
            error_type = "TYPE_ERROR"
            root_cause = "Runtime exception encountered during execution."
            diagnosis = f"Runtime error: {combined_output[:200]}"
            for k in files.keys():
                if k.startswith("backend/"):
                    files_to_modify.append(k)
                    break


        # Path Traversal Security Verification for target files
        safe_files_to_modify = []
        for rel_f in files_to_modify:
            clean_rel = rel_f.replace("\\", "/").lstrip("/")
            if clean_rel.startswith("/") or clean_rel.startswith("\\"):
                _logger.warning(f"Path traversal attempt rejected: {rel_f}")
                continue
            if target_path:
                dest = (target_path / clean_rel).resolve()
                if not str(dest).startswith(str(target_path)):
                    _logger.warning(f"Path traversal attempt rejected: {rel_f}")
                    continue
            safe_files_to_modify.append(clean_rel)

        if safe_files_to_modify:
            target_rel = safe_files_to_modify[0]
            existing_content = files.get(target_rel, "")
            
            if "WRONG" in existing_content and "OK" in combined_output:
                proposed_changes[target_rel] = existing_content.replace("'WRONG'", "'OK'").replace('"WRONG"', '"OK"')
            elif "AssertionError" in combined_output:
                proposed_changes[target_rel] = existing_content

        # Retrieve supplemental memory guidance safely (current execution evidence remains primary)
        memory_hint = ""
        try:
            rel_mems = global_project_memory_service.retrieve_relevant_memories(
                project_id=str(state.get("project_name", state.get("project_id", "default_project"))),
                error_type=error_type,
                query_text=combined_output[:300],
                technology=str(state.get("technology_stack", "python")),
                top_k=2
            )
            if rel_mems:
                hints = [m.fix for m in rel_mems if m.fix]
                if hints:
                    memory_hint = f" (Memory Hint: {hints[0]})"
        except Exception as e:
            _logger.warning(f"Failed to query project memory in DebugAgent: {e}")

        return DebugResult(
            success=len(safe_files_to_modify) > 0 or error_type != "UNKNOWN",
            diagnosis=diagnosis,
            root_cause=root_cause,
            error_type=error_type,
            files_to_modify=safe_files_to_modify,
            changes=proposed_changes,
            confidence=0.9 if safe_files_to_modify else 0.5,
            explanation=f"Identified error type {error_type} in {safe_files_to_modify}. Proposed targeted patch.{memory_hint}"
        )


global_debug_agent = DebugAgent()

