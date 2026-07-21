import re
import logging
from pathlib import Path
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.project_intelligence")

class ComponentMapper:
    """
    Statically analyzes JSX rendering blocks to build React component hierarchies.
    """

    def __init__(self) -> None:
        # Regex to locate capital-letter custom elements e.g. <Sidebar ... /> or <ChatBox>
        self.component_use_pattern = re.compile(r'<([A-Z][a-zA-Z0-9_]+)(?:\s|>)')

    def build_tree(self, workspace_path: str) -> Dict[str, Any]:
        import os
        root = Path(workspace_path)
        hierarchy: Dict[str, List[str]] = {}
        ignored_dirs = {".git", ".venv", "venv", "node_modules", ".gemini", "dist", "__pycache__", "build", ".pytest_cache", ".vscode", "generated_projects"}

        for r_dir, dirs, files in os.walk(workspace_path):
            dirs[:] = [d for d in dirs if d not in ignored_dirs]
            for file in files:
                file_path = Path(r_dir) / file
                if file_path.suffix in (".js", ".jsx", ".ts", ".tsx"):
                    comp_name = file_path.stem
                    # Ensure it starts with uppercase (React component naming standard)
                    if not comp_name[0].isupper():
                        continue

                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()

                        nested = self.component_use_pattern.findall(content)
                        # Deduplicate and exclude self references
                        unique_nested = list(set([n for n in nested if n != comp_name]))
                        hierarchy[comp_name] = unique_nested
                    except Exception as e:
                        _logger.error(f"Failed to build tree for {comp_name}: {str(e)}")

        return {
            "root_components": [k for k in hierarchy if k == "App"],
            "component_hierarchy": hierarchy
        }
