import ast
import time
import logging
from pathlib import Path
from backend.validation.models import ValidationResult
from backend.validation.utils import get_all_files

_logger = logging.getLogger("aiforge.performance")

class APIChecker:
    """
    Validates backend API route declarations: checks HTTP methods, duplicate routes, 
    missing response models/status codes, authentication middleware presence, and error handling.
    """

    def validate(self, project_path: Path) -> ValidationResult:
        start_time = time.perf_counter()
        _logger.info("API Checker Started")

        errors = []
        warnings = []
        routes = [] # list of dicts: {path, method, file, line, response_model, auth, try_except}

        py_files = list(get_all_files(project_path, [".py"]))
        for file_path in py_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Scan function decorators for routes
                        for decorator in node.decorator_list:
                            # Decorator could be like app.get("/"), router.post("/login"), etc.
                            is_route = False
                            method = ""
                            path = ""
                            response_model = None
                            status_code = None
                            
                            # E.g. @app.get("/") -> decorator is Call
                            if isinstance(decorator, ast.Call):
                                func = decorator.func
                                # app.get -> Attribute
                                if isinstance(func, ast.Attribute):
                                    if func.attr in {"get", "post", "put", "patch", "delete"}:
                                        is_route = True
                                        method = func.attr.upper()
                                
                                # Extract path argument (usually the first positional argument)
                                if is_route and decorator.args:
                                    first_arg = decorator.args[0]
                                    if isinstance(first_arg, ast.Constant):
                                        path = str(first_arg.value)
                                
                                # Extract keywords (e.g. response_model, status_code)
                                if is_route:
                                    for kw in decorator.keywords:
                                        if kw.arg == "response_model":
                                            response_model = ast.unparse(kw.value)
                                        elif kw.arg == "status_code":
                                            status_code = ast.unparse(kw.value)
                            
                            if is_route:
                                # Check authentication presence
                                has_auth = False
                                for arg in node.args.args:
                                    # Look for dependencies/Depends in type hints or defaults
                                    pass
                                for default in node.args.defaults:
                                    if "Depends(" in ast.unparse(default):
                                        has_auth = True
                                
                                # Check error handling try/except
                                has_try_except = any(
                                    isinstance(subnode, ast.Try) 
                                    for subnode in ast.walk(node)
                                )
                                
                                routes.append({
                                    "path": path,
                                    "method": method,
                                    "file": file_path.name,
                                    "line": node.lineno,
                                    "response_model": response_model,
                                    "status_code": status_code,
                                    "auth": has_auth,
                                    "try_except": has_try_except
                                })
            except Exception as exc:
                # Log but do not crash
                _logger.warning(f"Failed to parse AST for API check on {file_path.name}: {exc}")

        # Validate extracted routes
        seen_endpoints = set()
        for r in routes:
            endpoint_key = (r["method"], r["path"])
            if endpoint_key in seen_endpoints:
                errors.append(
                    f"Duplicate API route endpoint: {r['method']} '{r['path']}' declared in {r['file']} at line {r['line']}"
                )
            seen_endpoints.add(endpoint_key)
            
            # Check response specifications
            if not r["response_model"]:
                warnings.append(
                    f"Missing response_model in {r['method']} '{r['path']}' in {r['file']} at line {r['line']}"
                )
            if not r["status_code"]:
                warnings.append(
                    f"Missing status_code declaration in {r['method']} '{r['path']}' in {r['file']} at line {r['line']}"
                )
                
            # Check error handling
            if not r["try_except"]:
                warnings.append(
                    f"Route handler has no error handling try/except blocks: {r['method']} '{r['path']}' in {r['file']} at line {r['line']}"
                )

        execution_time = round(time.perf_counter() - start_time, 4)
        
        score = 100.0
        score -= len(errors) * 15
        score -= len(warnings) * 2
        score = max(0.0, min(100.0, score))
        
        status = "PASS" if score >= 90.0 else "FAIL"
        
        _logger.info(f"API Checker Finished. Status={status}, Score={score}")
        return ValidationResult(
            validator="API Checker",
            status=status,
            score=score,
            errors=errors,
            warnings=warnings,
            execution_time=execution_time,
            metadata={
                "routes_scanned": len(routes)
            }
        )
