import re
import logging
from pathlib import Path

_logger = logging.getLogger("aiforge.performance")


class ArchitectureChecker:
    """
    Statically analyzes project files to detect structural and naming issues,
    unused imports, oversized files, missing documentation, and potential circular dependencies.
    """

    def __init__(self) -> None:
        pass

    def check_project(self, project_path: Path) -> list[dict]:
        """
        Runs structural validations on the generated project path.
        """
        _logger.info("INFO Starting architecture checking...")
        findings = []

        # Find all code files
        python_files = list(project_path.glob("**/*.py"))
        js_files = list(project_path.glob("**/*.js")) + list(project_path.glob("**/*.jsx"))
        all_code_files = python_files + js_files

        # 1. Check oversized files (> 500 lines) and missing documentation
        for file_path in all_code_files:
            try:
                rel_file = str(file_path.relative_to(project_path))
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                lines = content.splitlines()
                if len(lines) > 500:
                    findings.append({
                        "severity": "warning",
                        "file": rel_file,
                        "line": 1,
                        "issue": f"Oversized file detected ({len(lines)} lines)",
                        "recommendation": "Refactor logic into smaller modules/components"
                    })

                # Check missing documentation (docstrings or headers)
                if file_path.suffix == ".py":
                    if '"""' not in content and "'''" not in content:
                        findings.append({
                            "severity": "info",
                            "file": rel_file,
                            "line": 1,
                            "issue": "Missing module docstring",
                            "recommendation": "Add a descriptive docstring at the top of the file"
                        })
                else:
                    if "/*" not in content and "//" not in content:
                        findings.append({
                            "severity": "info",
                            "file": rel_file,
                            "line": 1,
                            "issue": "Missing documentation comments",
                            "recommendation": "Add comments describing the component responsibilities"
                        })

            except Exception as exc:
                _logger.warning(f"Failed to check file size/documentation for {file_path}: {exc}")

        # 2. Check naming inconsistencies
        for file_path in all_code_files:
            rel_file = str(file_path.relative_to(project_path))
            name_without_suffix = file_path.stem
            
            # Python files must be snake_case
            if file_path.suffix == ".py":
                if not re.match(r"^[a-z_][a-z0-9_]*$", name_without_suffix):
                    findings.append({
                        "severity": "warning",
                        "file": rel_file,
                        "line": 1,
                        "issue": f"Inconsistent file naming: '{name_without_suffix}' is not snake_case",
                        "recommendation": "Rename file to snake_case"
                    })
            # React components should be PascalCase or camelCase
            elif file_path.suffix == ".jsx":
                if not re.match(r"^[A-Z][a-zA-Z0-9]*$", name_without_suffix):
                    findings.append({
                        "severity": "info",
                        "file": rel_file,
                        "line": 1,
                        "issue": f"Inconsistent React file naming: '{name_without_suffix}' should be PascalCase",
                        "recommendation": "Rename component file to PascalCase"
                    })

        # 3. Detect duplicate modules (files with the same name in different sub-folders)
        module_names = {}
        for file_path in all_code_files:
            rel_file = str(file_path.relative_to(project_path))
            name = file_path.name
            if name in module_names:
                findings.append({
                    "severity": "warning",
                    "file": rel_file,
                    "line": 1,
                    "issue": f"Duplicate module name detected: '{name}' matches {module_names[name]}",
                    "recommendation": "Consolidate logic or rename one of the files to avoid namespace pollution"
                })
            else:
                module_names[name] = rel_file

        # 4. Check basic unused imports in Python files
        # A simple check: if an import line imports a name, is it referenced elsewhere in the code?
        for file_path in python_files:
            try:
                rel_file = str(file_path.relative_to(project_path))
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                content = "".join(lines)
                for line_no, line in enumerate(lines, 1):
                    # Match: "import name" or "from module import name"
                    import_match = re.match(r"^\s*(?:import|from\s+\S+\s+import)\s+([a-zA-Z0-9_, ]+)", line)
                    if import_match:
                        imported_names = [n.strip() for n in import_match.group(1).split(",")]
                        for name in imported_names:
                            # Skip wildcards
                            if name == "*":
                                continue
                            # Count occurrences of the imported name
                            occurrences = len(re.findall(rf"\b{name}\b", content))
                            # If occurrence count is 1, it only appears on the import line!
                            if occurrences <= 1:
                                findings.append({
                                    "severity": "info",
                                    "file": rel_file,
                                    "line": line_no,
                                    "issue": f"Unused import detected: '{name}'",
                                    "recommendation": "Remove unused import statements"
                                })
            except Exception as exc:
                _logger.warning(f"Unused import check failed for {file_path}: {exc}")

        # 5. Check for circular imports in Python files
        # We perform a basic parsing of imports to build a dependency graph and check for cycles
        dep_graph = {}
        for file_path in python_files:
            try:
                rel_file = str(file_path.relative_to(project_path))
                mod_name = file_path.stem
                dep_graph[mod_name] = []
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        # E.g. "from backend.auth import xyz" -> "auth"
                        from_match = re.search(r"^\s*from\s+[\w\.]*\.([\w]+)\s+import", line)
                        if from_match:
                            dep_graph[mod_name].append(from_match.group(1))
                        # E.g. "import backend.auth" -> "auth"
                        import_match = re.search(r"^\s*import\s+[\w\.]*\.([\w]+)", line)
                        if import_match:
                            dep_graph[mod_name].append(import_match.group(1))
            except Exception:
                pass

        # Detect cycles in dep_graph using DFS
        visited = {}
        path = []

        def find_cycle(node):
            visited[node] = True
            path.append(node)
            for neighbor in dep_graph.get(node, []):
                if neighbor not in visited:
                    if find_cycle(neighbor):
                        return True
                elif neighbor in path:
                    # Found a cycle!
                    cycle_path = " -> ".join(path[path.index(neighbor):] + [neighbor])
                    findings.append({
                        "severity": "critical",
                        "file": f"backend/{node}.py",
                        "line": 1,
                        "issue": f"Circular dependency cycle detected: {cycle_path}",
                        "recommendation": "Refactor dependencies or extract shared logic to a common helper module"
                    })
                    return True
            path.pop()
            return False

        for node in list(dep_graph.keys()):
            if node not in visited:
                find_cycle(node)

        _logger.info("INFO Architecture checking completed")
        return findings
