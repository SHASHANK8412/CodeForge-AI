import os
import re
import logging
from pathlib import Path
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.knowledge")

class ProjectExtractor:
    """
    Scrapes built repository layers to build framework metadata indexing.
    """

    def __init__(self) -> None:
        pass

    def extract_metadata(self, workspace_path: str) -> Dict[str, Any]:
        """
        Parses folder layers and indexes files.
        """
        root = Path(workspace_path)
        
        # Scrape technology indicators
        techs = []
        frontend_engine = "Unknown"
        backend_engine = "Unknown"
        db = "SQLite"

        # Check frontend flags
        if (root / "frontend" / "package.json").exists():
            techs.extend(["React", "Vite", "Node.js"])
            frontend_engine = "React"
        elif (root / "frontend").exists():
            techs.extend(["HTML", "Javascript"])
            frontend_engine = "HTML5"

        # Check backend flags
        if (root / "backend" / "main.py").exists() or list(root.glob("**/main.py")):
            techs.append("FastAPI")
            backend_engine = "FastAPI"
            
        # Parse database indicators
        with_sqlite = list(root.glob("**/*.db")) or list(root.glob("**/*.sqlite"))
        if with_sqlite:
            db = "SQLite"
            techs.append("SQLite")
        elif "postgres" in str(list(root.glob("**/*.py"))).lower():
            db = "PostgreSQL"
            techs.append("PostgreSQL")

        # Scan folder layout
        folders = []
        for p in root.glob("*"):
            if p.is_dir() and not p.name.startswith(".") and p.name != "node_modules":
                folders.append(p.name)

        return {
            "name": root.name,
            "type": "Web Application" if frontend_engine != "Unknown" else "API Service",
            "frameworks": techs,
            "frontend": frontend_engine,
            "backend": backend_engine,
            "database": db,
            "auth": "JWT" if "jwt" in str(list(root.glob("**/*.py"))).lower() else "None",
            "folder_structure": folders,
            "deployment": "Docker" if (root / "Dockerfile").exists() else "Native"
        }
