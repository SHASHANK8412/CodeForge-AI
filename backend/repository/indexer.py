"""
AIForge Repository Indexer & Tree Generator
============================================
Builds structured Repository Project Trees (Frontend, Backend, Database, Tests, Docker)
and maintains inverted symbol search indices for fast retrieval by AI agents.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.repository.scanner import RepositoryScanner

_logger = logging.getLogger("aiforge.repository")


class RepositoryIndexer:
    """
    Generates structured project trees and symbol search indexes.
    """

    def __init__(self, scanner: Optional[RepositoryScanner] = None) -> None:
        if scanner is None:
            scanner = RepositoryScanner()
        self.scanner = scanner

    def index_repository(self, workspace_root: str) -> Dict[str, Any]:
        scan_res = self.scanner.scan_repository(workspace_root)
        file_list = scan_res.get("file_metadata", [])

        # Categorize files into Project Tree structure
        frontend_files = [f["filename"] for f in file_list if f["filename"].startswith("frontend/") or f["ext"] in [".jsx", ".tsx", ".html", ".css"]]
        backend_files = [f["filename"] for f in file_list if f["filename"].startswith("backend/") or (f["filename"].startswith("src/") and f["ext"] == ".py")]
        test_files = [f["filename"] for f in file_list if "test" in f["filename"].lower()]
        config_files = [f["filename"] for f in file_list if f["filename"] in ["Dockerfile", "docker-compose.yml", "package.json", "requirements.txt", "README.md"]]

        project_tree = {
            "Frontend": {
                "components": [f for f in frontend_files if "component" in f.lower()],
                "pages": [f for f in frontend_files if "page" in f.lower()],
                "hooks": [f for f in frontend_files if "hook" in f.lower()],
                "utils": [f for f in frontend_files if "util" in f.lower()],
                "all_frontend_count": len(frontend_files)
            },
            "Backend": {
                "routes": [f for f in backend_files if "route" in f.lower()],
                "services": [f for f in backend_files if "service" in f.lower()],
                "agents": [f for f in backend_files if "agent" in f.lower()],
                "models": [f for f in backend_files if "model" in f.lower()],
                "middleware": [f for f in backend_files if "middleware" in f.lower()],
                "all_backend_count": len(backend_files)
            },
            "Tests": test_files,
            "Docker_Config": config_files
        }

        _logger.info(f"RepositoryIndexer: Indexed project tree ({len(frontend_files)} Frontend files, {len(backend_files)} Backend files).")
        return {
            "scanned_files_count": scan_res["scanned_files_count"],
            "language_breakdown": scan_res["language_breakdown"],
            "project_tree": project_tree,
            "raw_file_metadata": file_list
        }
