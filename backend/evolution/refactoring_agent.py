import re
import logging
from pathlib import Path
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.evolution")

class RefactoringAgent:
    """
    Safely refactors duplicate logic, unused imports, formatting and dead code.
    """

    def __init__(self) -> None:
        pass

    def refactor_unused_imports(self, file_path: str) -> bool:
        """
        Scans a Python file, detects imports of libraries that are never referenced
        further in the code, and removes them.
        """
        path = Path(file_path)
        if not path.exists():
            return False

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            lines = content.splitlines()
            modified = False
            new_lines = []

            # 1. Identify standard packages imported
            import_regex = re.compile(r'^\s*import\s+([a-zA-Z0-9_]+)\s*$')
            from_import_regex = re.compile(r'^\s*from\s+([a-zA-Z0-9_\.]+)\s+import\s+([a-zA-Z0-9_]+)\s*$')

            for idx, line in enumerate(lines):
                # Check import name
                m1 = import_regex.match(line)
                m2 = from_import_regex.match(line)

                if m1:
                    lib_name = m1.group(1)
                    # Check if referenced anywhere else in the file
                    references = len(re.findall(r'\b' + re.escape(lib_name) + r'\b', content))
                    if references == 1:
                        # Only referenced in import line itself -> unused!
                        modified = True
                        _logger.info(f"[REFACTOR] Removing unused import '{lib_name}' in {path.name}")
                        continue  # Skip/delete this line

                elif m2:
                    lib_name = m2.group(2)
                    references = len(re.findall(r'\b' + re.escape(lib_name) + r'\b', content))
                    if references == 1:
                        modified = True
                        _logger.info(f"[REFACTOR] Removing unused from-import '{lib_name}' in {path.name}")
                        continue

                new_lines.append(line)

            if modified:
                with open(path, "w", encoding="utf-8") as f:
                    f.write("\n".join(new_lines) + "\n")
                return True

        except Exception as e:
            _logger.error(f"Failed to refactor imports in {path.name}: {str(e)}")

        return False
