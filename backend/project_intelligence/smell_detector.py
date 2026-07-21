import re
import logging
from pathlib import Path
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.project_intelligence")

class SmellDetector:
    """
    Checks code quality metrics (large files, god classes, unused structures, mixed concerns).
    """

    def __init__(self) -> None:
        pass

    def scan_smells(self, workspace_path: str) -> Dict[str, Any]:
        import os
        root = Path(workspace_path)
        large_files = []
        dead_imports = []
        god_classes = []
        ignored_dirs = {".git", ".venv", "venv", "node_modules", ".gemini", "dist", "__pycache__", "build", ".pytest_cache", ".vscode", "generated_projects"}

        for r_dir, dirs, files in os.walk(workspace_path):
            dirs[:] = [d for d in dirs if d not in ignored_dirs]
            for file in files:
                file_path = Path(r_dir) / file
                if file_path.suffix in (".py", ".js", ".jsx", ".ts", ".tsx"):
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            lines = f.readlines()

                        # Large file check (>500 lines)
                        if len(lines) > 500:
                            large_files.append({
                                "file": file_path.name,
                                "line_count": len(lines)
                            })

                        # God class or component methods density
                        class_methods_count = 0
                        for line in lines:
                            if "def " in line or "class " in line or "function " in line:
                                class_methods_count += 1
                        if class_methods_count > 25:
                            god_classes.append({
                                "file": file_path.name,
                                "method_count": class_methods_count
                            })

                        # Unused imports simple sweep
                        content = "".join(lines)
                        for line in lines:
                            if "import " in line:
                                # Scan import words
                                words = re.findall(r'([a-zA-Z0-9_]+)', line)
                                for w in words:
                                    if w not in ("import", "from", "as", "default", "react", "fastapi") and content.count(w) == 1:
                                        dead_imports.append({
                                            "file": file_path.name,
                                            "symbol": w
                                        })
                    except Exception as e:
                        _logger.error(f"Failed to scan smells for {file_path.name}: {str(e)}")

        return {
            "large_files_detected": large_files,
            "god_classes_detected": god_classes,
            "unused_imports_detected": dead_imports
        }
