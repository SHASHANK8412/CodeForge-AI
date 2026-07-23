"""
AIForge Repository Memory & Prompt Context Upgrader
===================================================
Persists repository intelligence memory (architecture, naming conventions, coding style, design decisions).
Upgrades LLM system/user prompts by injecting Repository Summary, Architecture, Existing Components,
APIs, and Coding Style guidelines to guarantee newly generated code matches codebase conventions.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.repository.indexer import RepositoryIndexer
from backend.repository.symbol_table import RepositorySymbolTable

_logger = logging.getLogger("aiforge.repository")


class RepositoryMemory:
    """
    Manages persistent repository context and upgrades agent prompts.
    """

    def __init__(self, memory_dir: Optional[str] = None) -> None:
        if memory_dir is None:
            memory_dir = str(Path(__file__).resolve().parents[1] / "memory")
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.file_path = self.memory_dir / "repository_memory.json"
        self.indexer = RepositoryIndexer()
        self.symbol_table = RepositorySymbolTable()

    def build_repository_memory(self, workspace_root: str) -> Dict[str, Any]:
        index_res = self.indexer.index_repository(workspace_root)
        file_meta = index_res.get("raw_file_metadata", [])
        symbols = self.symbol_table.build_symbol_table(file_meta)

        repo_memory = {
            "workspace_root": workspace_root,
            "total_files": index_res["scanned_files_count"],
            "language_breakdown": index_res["language_breakdown"],
            "project_tree": index_res["project_tree"],
            "total_symbols": symbols["total_symbols"],
            "architecture": "FastAPI + React Clean Modular Architecture",
            "coding_style": "PEP8 / ESLint with Async Handlers & SOLID Principles",
            "existing_apis_sample": list(symbols["routes"].keys())[:10],
            "existing_components_sample": list(symbols["components"].keys())[:10]
        }

        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(repo_memory, f, indent=2)
            _logger.info(f"RepositoryMemory: Saved memory index to '{self.file_path}'")
        except Exception as e:
            _logger.error(f"Failed to save repository_memory.json: {e}")

        return repo_memory

    def get_upgraded_prompt(self, base_user_prompt: str, workspace_root: Optional[str] = None) -> str:
        """
        Upgrades agent prompts with Repository Summary, Architecture, Existing Components,
        Existing APIs, and Coding Style guidelines.
        """
        if not self.file_path.exists() and workspace_root:
            self.build_repository_memory(workspace_root)

        memory_data = {}
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    memory_data = json.load(f)
            except Exception:
                pass

        arch = memory_data.get("architecture", "FastAPI + React Clean Architecture")
        style = memory_data.get("coding_style", "PEP8, Async Handlers & SOLID Principles")
        components = ", ".join(memory_data.get("existing_components_sample", ["Button", "Header", "Sidebar"]))
        apis = ", ".join(memory_data.get("existing_apis_sample", ["GET /api/v1/auth", "POST /api/v1/projects"]))

        upgraded_prompt = f"""
======================================================================
 REPOSITORY INTELLIGENCE CONTEXT
======================================================================
Architecture: {arch}
Coding Style: {style}
Existing Components: {components}
Existing APIs: {apis}

======================================================================
 USER FEATURE REQUEST
======================================================================
{base_user_prompt}

DIRECTIVE: Generate implementation strictly consistent with existing repository architecture, conventions, and style.
""".strip()

        _logger.info(f"RepositoryMemory: Upgraded user prompt for feature: '{base_user_prompt}'")
        return upgraded_prompt
