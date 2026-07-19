import ast
import re
import time
import logging
from pathlib import Path
from backend.validation.models import ValidationResult
from backend.validation.utils import get_all_files

_logger = logging.getLogger("aiforge.performance")

class SyntaxChecker:
    """
    Validates Python file syntax using AST parsing, and JS/JSX/ES6 compatibility.
    """

    def validate(self, project_path: Path) -> ValidationResult:
        start_time = time.perf_counter()
        _logger.info("Syntax Checker Started")

        errors = []
        warnings = []
        files_checked = 0
        files_failed = 0

        # 1. Python Validation
        py_files = list(get_all_files(project_path, [".py"]))
        for file_path in py_files:
            files_checked += 1
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Check for AST syntax validity
                tree = ast.parse(content, filename=str(file_path))
                
                # Scan for missing local imports or syntax-level issues
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module:
                            # If it looks like a local module import, e.g. "backend.main"
                            module_parts = node.module.split(".")
                            # Check if the relative folder/file exists
                            local_path = project_path / "/".join(module_parts)
                            py_local_file = project_path / ("/".join(module_parts) + ".py")
                            init_local_file = project_path / "/".join(module_parts) / "__init__.py"
                            if not (local_path.exists() or py_local_file.exists() or init_local_file.exists()):
                                # Ignore standard libraries or third-party packages
                                # (only check if it starts with project folders like 'backend' or 'frontend')
                                if module_parts[0] in {"backend", "frontend", "src", "database"}:
                                    warnings.append(f"Possible missing local import: '{node.module}' in {file_path.name}")
                                    
                    elif isinstance(node, ast.ClassDef):
                        # Validate class definition has a name
                        if not node.name:
                            errors.append(f"Invalid class definition in {file_path.name}")
                            
            except (SyntaxError, IndentationError) as exc:
                files_failed += 1
                errors.append(f"Syntax error in {file_path.name} at line {exc.lineno}: {exc.msg}")
            except Exception as exc:
                files_failed += 1
                errors.append(f"Error parsing {file_path.name}: {str(exc)}")

        # 2. JavaScript / React JSX Validation
        js_files = list(get_all_files(project_path, [".js", ".jsx", ".ts", ".tsx"]))
        for file_path in js_files:
            files_checked += 1
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Check JSX tag balance
                open_tags = len(re.findall(r"<[a-zA-Z0-9_\-]+[^>]*>", content))
                close_tags = len(re.findall(r"</[a-zA-Z0-9_\-]+>", content))
                self_closing = len(re.findall(r"<[a-zA-Z0-9_\-]+[^>]*/>", content))
                
                if open_tags != (close_tags + self_closing) and abs(open_tags - (close_tags + self_closing)) > 5:
                    errors.append(f"Possible malformed JSX structure in {file_path.name}")
                
                # Check duplicate variables in local file scope (e.g. const x = ... const x = ...)
                const_declarations = re.findall(r"\b(?:const|let|var)\s+([a-zA-Z0-9_]+)\s*=", content)
                seen_vars = set()
                for var in const_declarations:
                    if var in seen_vars:
                        # Warnings instead of breaking error to prevent false-positives in closures
                        warnings.append(f"Variable '{var}' re-declared in file scope in {file_path.name}")
                    seen_vars.add(var)

                # Check missing export warning
                if "export " not in content and "module.exports" not in content and (file_path.suffix in [".jsx", ".tsx"]):
                    warnings.append(f"Component file has no export statements: {file_path.name}")
                    
                # Unexpected token checks (e.g. invalid symbols)
                if "===" in content and "====" in content:
                    errors.append(f"Unexpected token '====' in {file_path.name}")

            except Exception as exc:
                files_failed += 1
                errors.append(f"JS syntax analysis failed for {file_path.name}: {str(exc)}")

        execution_time = round(time.perf_counter() - start_time, 4)
        
        # Calculate score dynamically
        score = 100.0
        if files_failed > 0:
            score -= (files_failed / max(1, files_checked)) * 50
        score -= len(errors) * 10
        score -= len(warnings) * 2
        score = max(0.0, min(100.0, score))
        
        status = "PASS" if score >= 90.0 else "FAIL"

        _logger.info(f"Syntax Checker Finished. Status={status}, Score={score}")
        return ValidationResult(
            validator="Syntax Checker",
            status=status,
            score=score,
            errors=errors,
            warnings=warnings,
            execution_time=execution_time,
            metadata={
                "files_checked": files_checked,
                "files_failed": files_failed
            }
        )
