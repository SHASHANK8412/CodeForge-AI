import re
import logging
from pathlib import Path

_logger = logging.getLogger("aiforge.performance")


class PerformanceChecker:
    """
    Analyzes project source files to detect performance issues such as nested loops,
    blocking sleep operations in async functions, repeated LLM calls, and missing caches.
    """

    def __init__(self) -> None:
        pass

    def check_project(self, project_path: Path) -> list[dict]:
        """
        Scans code files for performance issues.
        """
        _logger.info("INFO Starting performance checking...")
        findings = []

        python_files = list(project_path.glob("**/*.py"))
        js_files = list(project_path.glob("**/*.js")) + list(project_path.glob("**/*.jsx"))

        # Check Python files
        for file_path in python_files:
            try:
                rel_file = str(file_path.relative_to(project_path))
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                content = "".join(lines)

                # 1. Check blocking time.sleep in async functions
                in_async_def = False
                for line_no, line in enumerate(lines, 1):
                    if re.match(r"^\s*async\s+def\b", line):
                        in_async_def = True
                    elif re.match(r"^\s*def\b", line):
                        in_async_def = False

                    if in_async_def and "time.sleep(" in line:
                        findings.append({
                            "severity": "warning",
                            "file": rel_file,
                            "line": line_no,
                            "issue": "Blocking 'time.sleep' call inside an async function definition",
                            "recommendation": "Use 'await asyncio.sleep()' instead of synchronous time.sleep()"
                        })

                # 2. Check nested loops (basic check: two indented 'for' statements)
                for line_no, line in enumerate(lines, 1):
                    # Match a line containing 'for' and check if the next non-empty line has 'for' at a deeper indentation
                    if "for " in line and line_no < len(lines):
                        match_current = re.match(r"^(\s*)for\b", line)
                        if match_current:
                            current_indent = len(match_current.group(1))
                            # Check next few lines for nested loop
                            for offset in range(1, 4):
                                next_idx = line_no + offset - 1
                                if next_idx < len(lines):
                                    next_line = lines[next_idx]
                                    match_next = re.match(r"^(\s*)for\b", next_line)
                                    if match_next:
                                        next_indent = len(match_next.group(1))
                                        if next_indent > current_indent:
                                            findings.append({
                                                "severity": "info",
                                                "file": rel_file,
                                                "line": line_no,
                                                "issue": "Nested loop structure detected",
                                                "recommendation": "Verify complexity; if traversing large lists, consider hash maps or lookup sets"
                                            })
                                            break

                # 3. Check for repeated LLM calls inside loops
                # Look for loop statements followed by chat/generate calls
                in_loop = False
                loop_indent = 0
                for line_no, line in enumerate(lines, 1):
                    loop_match = re.match(r"^(\s*)(?:for|while)\b", line)
                    if loop_match:
                        in_loop = True
                        loop_indent = len(loop_match.group(1))
                    elif in_loop:
                        current_indent_match = re.match(r"^(\s*)\S", line)
                        if current_indent_match:
                            current_indent = len(current_indent_match.group(1))
                            if current_indent <= loop_indent:
                                in_loop = False
                        
                        if in_loop and re.search(r"\b(?:chat|generate|generate_text|ainvoke|invoke)\b", line):
                            findings.append({
                                "severity": "warning",
                                "file": rel_file,
                                "line": line_no,
                                "issue": "LLM API invocation inside a loop detected",
                                "recommendation": "Batch inputs together or process requests concurrently to minimize queuing times"
                            })

                # 4. Check candidates for LRU Caching
                # If a function has multiple recursive calls or computes complex items and has no decorator, suggest cache
                for line_no, line in enumerate(lines, 1):
                    # Basic check: a def statement not preceded by @lru_cache or @cache
                    if re.match(r"^\s*def\b", line):
                        # Look at the previous line for decorator
                        prev_line = lines[line_no - 2] if line_no > 1 else ""
                        if "cache" not in prev_line and "lru_cache" not in prev_line:
                            func_name = re.search(r"\bdef\s+(\w+)\b", line)
                            if func_name:
                                name = func_name.group(1)
                                # Check if function name is called recursively inside it
                                # Simple search in subsequent lines of function block
                                is_recursive = False
                                for offset in range(1, 30):
                                    idx = line_no + offset - 1
                                    if idx < len(lines):
                                        ln = lines[idx]
                                        if re.match(r"^\s*def\b", ln) or re.match(r"^\S", ln):
                                            break # End of function
                                        if f"{name}(" in ln:
                                            is_recursive = True
                                            break
                                if is_recursive:
                                    findings.append({
                                        "severity": "info",
                                        "file": rel_file,
                                        "line": line_no,
                                        "issue": f"Recursive function '{name}' lacks caching decoration",
                                        "recommendation": "Decorate with @lru_cache or @cache to optimize repeated recursive computations"
                                    })

            except Exception as exc:
                _logger.warning(f"Failed to check performance items for {file_path}: {exc}")

        # Check JS/JSX files
        for file_path in js_files:
            try:
                rel_file = str(file_path.relative_to(project_path))
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                # Basic check for nested loops in JS/JSX
                for line_no, line in enumerate(lines, 1):
                    if "for (" in line and line_no < len(lines):
                        match_current = re.match(r"^(\s*)for\b", line)
                        if match_current:
                            current_indent = len(match_current.group(1))
                            for offset in range(1, 4):
                                next_idx = line_no + offset - 1
                                if next_idx < len(lines):
                                    next_line = lines[next_idx]
                                    match_next = re.match(r"^(\s*)for\b", next_line)
                                    if match_next:
                                        next_indent = len(match_next.group(1))
                                        if next_indent > current_indent:
                                            findings.append({
                                                "severity": "info",
                                                "file": rel_file,
                                                "line": line_no,
                                                "issue": "Nested loop structure detected in Javascript file",
                                                "recommendation": "Verify loop complexity to prevent thread-blocking calculations on client browser"
                                            })
                                            break
            except Exception as exc:
                _logger.warning(f"Failed to check performance items for JS file {file_path}: {exc}")

        _logger.info("INFO Performance checking completed")
        return findings
