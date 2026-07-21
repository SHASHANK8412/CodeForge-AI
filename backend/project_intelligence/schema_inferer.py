import re
import logging
from pathlib import Path
from typing import List, Dict, Any

_logger = logging.getLogger("aiforge.project_intelligence")

class SchemaInferer:
    """
    Parses SQLAlchemy models definition code to map database tables schemas relationships.
    """

    def __init__(self) -> None:
        self.tablename_pattern = re.compile(r'__tablename__\s*=\s*["\']([^"\']+)["\']')
        self.foreignkey_pattern = re.compile(r'ForeignKey\(["\']([^"\']+)["\']\)')

    def infer_relationships(self, workspace_path: str) -> Dict[str, Any]:
        import os
        root = Path(workspace_path)
        tables = []
        relationships = []
        ignored_dirs = {".git", ".venv", "venv", "node_modules", ".gemini", "dist", "__pycache__", "build", ".pytest_cache", ".vscode", "generated_projects"}

        for r_dir, dirs, files in os.walk(workspace_path):
            dirs[:] = [d for d in dirs if d not in ignored_dirs]
            for file in files:
                file_path = Path(r_dir) / file
                if file_path.suffix == ".py":
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()

                        # Find tables
                        tablenames = self.tablename_pattern.findall(content)
                        for tablename in tablenames:
                            tables.append({"table": tablename, "file": file_path.name})
                            
                            # Look for foreign keys linking to this table
                            fk_matches = self.foreignkey_pattern.findall(content)
                            for fk in fk_matches:
                                target_table = fk.split(".")[0]
                                relationships.append({
                                    "source_table": tablename,
                                    "target_table": target_table,
                                    "relation": "Many-to-One"
                                })
                    except Exception as e:
                        _logger.error(f"Failed to infer schemas of {file_path.name}: {str(e)}")

        return {
            "tables": tables,
            "relationships": relationships
        }
