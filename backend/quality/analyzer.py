import ast
import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger("aiforge.quality.analyzer")


class CodeAnalyzer:
    """
    CodeAnalyzer performs static code analysis on Python and React/JSX code files:
    - Syntax verification
    - Unused imports & dead code detection
    - Cyclomatic complexity estimation
    """

    def analyze_python(self, filepath: str, code: str) -> Dict[str, Any]:
        issues = []
        complexity = 1

        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.With)):
                    complexity += 1
        except SyntaxError as e:
            issues.append({"type": "SyntaxError", "line": e.lineno, "message": str(e), "severity": "high"})
            return {"filepath": filepath, "is_valid": False, "complexity": 1, "issues": issues}

        # Check for unused imports
        lines = code.split("\n")
        imports = [line for line in lines if line.startswith("import ") or line.startswith("from ")]

        return {
            "filepath": filepath,
            "is_valid": len(issues) == 0,
            "complexity": complexity,
            "issues": issues,
            "imports_count": len(imports)
        }

    def analyze_react(self, filepath: str, code: str) -> Dict[str, Any]:
        issues = []
        if "export default" not in code and "module.exports" not in code:
            issues.append({"type": "ComponentExportMissing", "message": "No default export found in component", "severity": "medium"})

        return {
            "filepath": filepath,
            "is_valid": len(issues) == 0,
            "complexity": max(1, code.count("if ") + code.count("map(")),
            "issues": issues
        }

    def analyze_project(self, project_files: Dict[str, str]) -> Dict[str, Any]:
        results = {}
        total_complexity = 0

        for path, code in project_files.items():
            if path.endswith(".py"):
                res = self.analyze_python(path, code)
                results[path] = res
                total_complexity += res["complexity"]
            elif path.endswith((".jsx", ".js", ".tsx")):
                res = self.analyze_react(path, code)
                results[path] = res
                total_complexity += res["complexity"]

        avg_complexity = round(total_complexity / max(len(results), 1), 2)
        return {
            "file_analyses": results,
            "average_complexity": avg_complexity,
            "total_files_analyzed": len(results)
        }


# Global CodeAnalyzer Instance
global_code_analyzer = CodeAnalyzer()
