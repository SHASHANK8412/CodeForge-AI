import json
import re
import time
import sys
import logging
from pathlib import Path
from backend.validation.models import ValidationResult
from backend.validation.utils import get_all_files

_logger = logging.getLogger("aiforge.performance")

# Standard library module list to prevent false positive missing dependencies
STD_LIBS = {
    "os", "sys", "time", "re", "json", "math", "random", "datetime", "hashlib",
    "typing", "collections", "abc", "pathlib", "subprocess", "shutil", "logging",
    "unittest", "pytest", "asyncio", "argparse", "uuid", "sqlite3", "csv", "tempfile"
}

class DependencyChecker:
    """
    Validates project dependencies in requirements.txt and package.json.
    Verifies that all imports correspond to declared packages, and checks for unused/duplicate modules.
    """

    def validate(self, project_path: Path) -> ValidationResult:
        start_time = time.perf_counter()
        _logger.info("Dependency Checker Started")

        errors = []
        warnings = []
        suggestions = []
        
        # 1. Python Dependencies Checker
        req_file = project_path / "backend/requirements.txt"
        declared_py_pkgs = {}
        duplicate_py_pkgs = set()
        
        if req_file.exists():
            try:
                with open(req_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    # Parse package name, ignoring version constraints (e.g. fastapi>=0.95.0 -> fastapi)
                    parts = re.split(r"[=<>~!]", line)
                    pkg_name = parts[0].strip().lower().replace("-", "_")
                    if pkg_name in declared_py_pkgs:
                        duplicate_py_pkgs.add(pkg_name)
                    declared_py_pkgs[pkg_name] = line.strip()
            except Exception as exc:
                errors.append(f"Failed to read requirements.txt: {str(exc)}")
        else:
            warnings.append("backend/requirements.txt is missing from project layout")

        for dup in duplicate_py_pkgs:
            errors.append(f"Duplicate dependency declared in requirements.txt: '{dup}'")
            suggestions.append(f"Remove duplicate references to '{dup}' in backend/requirements.txt")

        # Scan python imports
        imported_py_pkgs = set()
        py_files = list(get_all_files(project_path, [".py"]))
        for file_path in py_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                # Find imports
                for line in content.splitlines():
                    # Match "import x" or "from x import y"
                    match_imp = re.match(r"^\s*import\s+([a-zA-Z0-9_\-]+)", line)
                    match_from = re.match(r"^\s*from\s+([a-zA-Z0-9_\-]+)", line)
                    imp_name = None
                    if match_imp:
                        imp_name = match_imp.group(1).lower().replace("-", "_")
                    elif match_from:
                        imp_name = match_from.group(1).lower().replace("-", "_")
                    
                    if imp_name and imp_name not in STD_LIBS:
                        # Ignore local project module imports
                        if imp_name not in {"backend", "frontend", "src", "database"}:
                            imported_py_pkgs.add(imp_name)
            except Exception:
                pass

        # Identify missing Python dependencies
        for imp in imported_py_pkgs:
            # Quick check if import or its root module is in declared packages
            found = False
            for pkg in declared_py_pkgs:
                if pkg == imp or imp.startswith(pkg):
                    found = True
                    break
            if not found:
                errors.append(f"Missing dependency in requirements.txt for imported package: '{imp}'")
                suggestions.append(f"Add '{imp}' package definition to backend/requirements.txt")

        # Identify unused Python dependencies
        for pkg in declared_py_pkgs:
            # Check if used
            used = False
            for imp in imported_py_pkgs:
                if imp == pkg or imp.startswith(pkg):
                    used = True
                    break
            if not used and pkg not in {"pytest", "uvicorn", "black", "flake8", "psycopg2_binary", "pytest_asyncio"}:
                warnings.append(f"Unused dependency declared in requirements.txt: '{pkg}'")
                suggestions.append(f"Consider removing unused package '{pkg}' from backend/requirements.txt")


        # 2. Node JS / React Dependencies Checker
        package_json = project_path / "frontend/package.json"
        declared_js_pkgs = {}
        
        if package_json.exists():
            try:
                with open(package_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                deps = data.get("dependencies", {})
                dev_deps = data.get("devDependencies", {})
                
                # Check duplicates between dependencies and devDependencies
                for k, v in deps.items():
                    declared_js_pkgs[k.lower()] = v
                for k, v in dev_deps.items():
                    if k.lower() in declared_js_pkgs:
                        errors.append(f"Duplicate dependency declared in package.json (both deps and devDeps): '{k}'")
                    declared_js_pkgs[k.lower()] = v
            except Exception as exc:
                errors.append(f"Failed to read package.json: {str(exc)}")
        else:
            warnings.append("frontend/package.json is missing from project layout")

        # Scan JS/JSX imports
        imported_js_pkgs = set()
        js_files = list(get_all_files(project_path, [".js", ".jsx", ".ts", ".tsx"]))
        for file_path in js_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                # Match import statements: import x from 'y'
                matches = re.findall(r"\bfrom\s+['\"]([^'\".\/][^'\"]*)['\"]", content)
                for m in matches:
                    # Resolve package name (e.g. '@mui/material/Button' -> '@mui/material' or 'react-router-dom/dist' -> 'react-router-dom')
                    parts = m.split("/")
                    if m.startswith("@") and len(parts) > 1:
                        pkg_name = f"{parts[0]}/{parts[1]}"
                    else:
                        pkg_name = parts[0]
                    imported_js_pkgs.add(pkg_name.lower())
            except Exception:
                pass

        # Identify missing JS packages
        for imp in imported_js_pkgs:
            if imp not in declared_js_pkgs and imp not in {"react", "react-dom"}:
                # Ignore absolute path shortcuts or local modules starts with src/
                if not imp.startswith("src") and not imp.startswith("components") and not imp.startswith("hooks"):
                    errors.append(f"Missing dependency in package.json for imported package: '{imp}'")
                    suggestions.append(f"Add '{imp}' package definition to package.json")

        execution_time = round(time.perf_counter() - start_time, 4)
        
        score = 100.0
        score -= len(errors) * 15
        score -= len(warnings) * 3
        score = max(0.0, min(100.0, score))
        
        status = "PASS" if score >= 90.0 else "FAIL"
        
        _logger.info(f"Dependency Checker Finished. Status={status}, Score={score}")
        return ValidationResult(
            validator="Dependency Checker",
            status=status,
            score=score,
            errors=errors,
            warnings=warnings,
            execution_time=execution_time,
            metadata={
                "suggestions": suggestions
            }
        )
