import re
import time
import logging
from pathlib import Path
from backend.validation.models import ValidationResult
from backend.validation.utils import get_all_files

_logger = logging.getLogger("aiforge.performance")

class FrontendChecker:
    """
    Validates React frontend files, components, routing, custom hooks, circular imports, and hook rules.
    """

    def validate(self, project_path: Path) -> ValidationResult:
        start_time = time.perf_counter()
        _logger.info("Frontend Checker Started")

        errors = []
        warnings = []
        
        js_files = list(get_all_files(project_path, [".js", ".jsx", ".ts", ".tsx"]))
        
        # 1. Broken imports check
        for file_path in js_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Match relative imports like: import X from './Y' or from '../Z'
                imports = re.findall(r"\bfrom\s+['\"](\.\.?\/[^'\"]*)['\"]", content)
                for imp in imports:
                    # Resolve relative file path
                    resolved_path = (file_path.parent / imp).resolve()
                    # Check with extensions
                    possible_extensions = ["", ".jsx", ".js", ".tsx", ".ts", "/index.js", "/index.jsx"]
                    exists = False
                    for ext in possible_extensions:
                        # Convert to Path and check existence
                        p = Path(str(resolved_path) + ext)
                        if p.exists() or (resolved_path / "index.js").exists() or (resolved_path / "index.jsx").exists():
                            exists = True
                            break
                    if not exists:
                        errors.append(f"Broken import reference '{imp}' found in {file_path.name}")
            except Exception as exc:
                warnings.append(f"Failed to scan imports in {file_path.name}: {exc}")

        # 2. Hook usage validation (Rules of Hooks)
        for file_path in js_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Find if a hook is defined inside a loop or conditional block
                # Search for: if (...) { ... useSomething(...) ... } or for (...) { ... useSomething(...) ... }
                # Simulating with simple nested block regexes
                conditional_hook = re.findall(r"\b(?:if|for|while)\s*\([^\)]*\)\s*\{[^}]*\b(use[A-Z][a-zA-Z0-9_]*)\(", content)
                for hook in conditional_hook:
                    errors.append(f"Invalid hook call '{hook}' inside conditional or loop in {file_path.name}")
            except Exception:
                pass

        # 3. Routing check
        for file_path in js_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                if "<Route " in content:
                    # Validate Route declarations
                    route_declarations = re.findall(r"<Route\s+([^>]*)/?>", content)
                    for r_dec in route_declarations:
                        if "path=" not in r_dec:
                            warnings.append(f"React Route missing 'path' attribute in {file_path.name}")
                        if "element=" not in r_dec:
                            warnings.append(f"React Route missing 'element' component mapping in {file_path.name}")
            except Exception:
                pass

        # 4. Circular Import check (simple 2-file circular import check)
        import_maps = {}
        for file_path in js_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                imports = re.findall(r"\bfrom\s+['\"](\.\.?\/[^'\"]*)['\"]", content)
                import_maps[file_path.name] = []
                for imp in imports:
                    target_name = imp.split("/")[-1]
                    # Try matching with extensions
                    for ext in ["", ".jsx", ".js", ".tsx", ".ts"]:
                        if (file_path.parent / (imp + ext)).name in import_maps:
                            import_maps[file_path.name].append((file_path.parent / (imp + ext)).name)
            except Exception:
                pass

        for file_a, imports_a in import_maps.items():
            for file_b in imports_a:
                if file_b in import_maps and file_a in import_maps[file_b]:
                    warnings.append(f"Circular import dependency detected between: '{file_a}' <-> '{file_b}'")

        execution_time = round(time.perf_counter() - start_time, 4)
        
        score = 100.0
        score -= len(errors) * 15
        score -= len(warnings) * 2
        score = max(0.0, min(100.0, score))
        
        status = "PASS" if score >= 90.0 else "FAIL"
        
        _logger.info(f"Frontend Checker Finished. Status={status}, Score={score}")
        return ValidationResult(
            validator="Frontend Checker",
            status=status,
            score=score,
            errors=errors,
            warnings=warnings,
            execution_time=execution_time,
            metadata={
                "js_files_scanned": len(js_files)
            }
        )
