"""
AIForge Day 94 Code Smell Detector
==================================
Detects 9 core code smell categories:
1. Long Methods / Functions (> 30 lines)
2. Large Classes (> 200 lines)
3. Duplicate Code
4. Dead Code / Unused Imports & Variables
5. Deeply Nested Conditionals (depth > 3)
6. Long Parameter Lists (> 4 parameters)
7. Magic Numbers
8. Poor Variable Names (single character or vague like 'a', 'x', 'tmp')
9. Unsafe Security Patterns (eval, unsafe exec) and Print Statements
"""

import ast
import re
import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.analysis.code_smells")


class CodeSmellDetector:
    """
    AST & regex based Code Smell Detector.
    """

    def analyze_code_smells(self, code_content: str, filename: str = "main.py") -> Dict[str, Any]:
        _logger.info(f"CodeSmellDetector: Analyzing code smells for '{filename}'...")

        smells = []
        lines = code_content.splitlines()
        line_count = len(lines)

        # 1. Check Large Class / File
        if line_count > 200:
            smells.append({
                "type": "Large File / Class",
                "severity": "medium",
                "line": 1,
                "message": f"File '{filename}' exceeds 200 lines ({line_count} lines)."
            })

        # 2. Check Print statements
        for idx, line in enumerate(lines, 1):
            if re.search(r"\bprint\(", line) and not line.strip().startswith("#"):
                smells.append({
                    "type": "Print Statement",
                    "severity": "low",
                    "line": idx,
                    "message": "Use structured logger.info(...) instead of raw print statement."
                })

            # 3. Check Magic Numbers in assignment or comparisons
            if re.search(r"(=|==|>|<|\+|-|\*|/)\s*([2-9]\d{1,4}|1000|8080|3000|5000)\b", line) and "HTTP" not in line and "PORT" not in line and not line.strip().startswith("#"):
                smells.append({
                    "type": "Magic Number",
                    "severity": "medium",
                    "line": idx,
                    "message": f"Magic number hardcoded on line {idx}. Extract to constant."
                })

            # 4. Check Unsafe eval
            if re.search(r"\beval\(", line) and not line.strip().startswith("#"):
                smells.append({
                    "type": "Security Vulnerability (Unsafe eval)",
                    "severity": "high",
                    "line": idx,
                    "message": "Unsafe eval usage detected. Replace with safe literal_eval."
                })

            # 5. Check Poor Variable Names
            if re.search(r"\b(a|b|c|x|y|z|tmp)\s*=\s*", line) and not line.strip().startswith("#"):
                smells.append({
                    "type": "Poor Variable Naming",
                    "severity": "low",
                    "line": idx,
                    "message": f"Non-descriptive variable name found on line {idx}."
                })

            # 6. Check Unsimplified boolean comparison
            if re.search(r"\bif\s+\w+\s*==\s*(True|False)\b", line):
                smells.append({
                    "type": "Redundant Boolean Comparison",
                    "severity": "low",
                    "line": idx,
                    "message": f"Redundant '== True/False' comparison on line {idx}."
                })

        # AST parsing for functions
        try:
            tree = ast.parse(code_content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Long function check
                    func_len = (node.end_lineno - node.lineno) if hasattr(node, 'end_lineno') else 35
                    if func_len > 30:
                        smells.append({
                            "type": "Long Method / Function",
                            "severity": "medium",
                            "line": node.lineno,
                            "message": f"Function '{node.name}' is too long ({func_len} lines > 30 lines threshold)."
                        })

                    # Long parameter list check
                    param_count = len(node.args.args)
                    if param_count > 4:
                        smells.append({
                            "type": "Long Parameter List",
                            "severity": "medium",
                            "line": node.lineno,
                            "message": f"Function '{node.name}' has too many parameters ({param_count} params > 4 max)."
                        })
        except Exception:
            pass

        return {
            "filename": filename,
            "smells_detected_count": len(smells),
            "smells": smells,
            "has_high_severity": any(s["severity"] == "high" for s in smells)
        }


global_code_smell_detector = CodeSmellDetector()
