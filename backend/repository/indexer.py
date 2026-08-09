"""
AIForge Repository Indexer
==========================
Constructs machine-readable RepositoryIndex, DependencyGraph, and RepositoryMap.
Supports incremental re-indexing and hash-based cache invalidation.
"""

import os
import hashlib
import logging
from typing import Dict, List, Set, Tuple, Optional

from backend.repository.models import (
    RepositoryInfo,
    FileRecord,
    SymbolRecord,
    RepositoryMap
)
from backend.repository.scanner import global_repository_scanner
from backend.repository.symbol_extractor import global_symbol_extractor

_logger = logging.getLogger("aiforge.repository.indexer")

REPOSITORY_INDEX_VERSION = "2.0.0"


class RepositoryIndex:
    """
    Complete in-memory index of a scanned repository.
    """

    def __init__(self, info: RepositoryInfo, file_records: List[FileRecord]):
        self.info = info
        self.version = REPOSITORY_INDEX_VERSION
        self.file_records: Dict[str, FileRecord] = {f.path: f for f in file_records}
        self.symbols: Dict[str, List[SymbolRecord]] = {}
        self.import_map: Dict[str, List[str]] = {}
        self.reverse_import_map: Dict[str, List[str]] = {}
        self.repository_map: Optional[RepositoryMap] = None

    def get_reverse_dependencies(self, file_path: str) -> List[str]:
        """Returns list of files that import file_path."""
        return self.reverse_import_map.get(file_path, [])


class RepositoryIndexer:
    """
    Builds and updates RepositoryIndex.
    """

    def __init__(self):
        self._index_cache: Dict[str, RepositoryIndex] = {}

    def index_repository(self, root_path: str, force_reindex: bool = False) -> RepositoryIndex:
        abs_root = os.path.abspath(root_path)
        repo_id = hashlib.md5(abs_root.encode("utf-8")).hexdigest()[:10]

        if not force_reindex and repo_id in self._index_cache:
            _logger.info(f"[RepositoryIndexer] Cache hit for repository ID '{repo_id}'")
            return self._index_cache[repo_id]

        info, file_records = global_repository_scanner.scan_repository(abs_root)

        _logger.info(f"[RepositoryIndexer] Indexing repository '{info.name}' ({info.file_count} files)...")
        index = RepositoryIndex(info, file_records)

        # Build symbol index & import graph
        all_symbol_names = set()
        for fpath, record in index.file_records.items():
            if record.is_binary or record.size_bytes == 0 or record.purpose not in ["SOURCE", "TEST", "CONFIG"]:
                continue

            full_fpath = os.path.join(abs_root, fpath)
            try:
                with open(full_fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    symbols, imports = global_symbol_extractor.extract_symbols(fpath, content, record.language)
                    record.symbols = symbols
                    record.imports = imports

                    for sym in symbols:
                        if sym.name not in index.symbols:
                            index.symbols[sym.name] = []
                        index.symbols[sym.name].append(sym)
                        all_symbol_names.add(sym.name)

                    index.import_map[fpath] = imports
            except Exception as e:
                _logger.debug(f"[RepositoryIndexer] Error parsing symbols for '{fpath}': {e}")

        # Build reverse import dependency map via fast O(1) stem map
        stem_map = {os.path.splitext(os.path.basename(p))[0]: p for p in index.file_records.keys()}
        for fpath, imports in index.import_map.items():
            for imp in imports:
                if not imp:
                    continue
                target_stem = imp.split(".")[-1]
                target_path = stem_map.get(target_stem) or stem_map.get(imp)
                if target_path:
                    if target_path not in index.reverse_import_map:
                        index.reverse_import_map[target_path] = []
                    if fpath not in index.reverse_import_map[target_path]:
                        index.reverse_import_map[target_path].append(fpath)

        # Build RepositoryMap representation
        index.repository_map = self._build_repository_map(index)

        self._index_cache[repo_id] = index
        return index

    def _build_repository_map(self, index: RepositoryIndex) -> RepositoryMap:
        tree_lines = [f"Repository: {index.info.name} ({index.info.file_count} files)"]
        important: Dict[str, str] = {}

        for fpath, rec in sorted(index.file_records.items()):
            fname = os.path.basename(fpath)
            fname_lower = fname.lower()

            role = ""
            if fname_lower in ["main.py", "app.py", "index.js", "server.js", "application.java"]:
                role = "ENTRY_POINT"
            elif "route" in fpath.lower() or "controller" in fpath.lower() or "api" in fpath.lower():
                role = "ROUTE"
            elif "model" in fpath.lower() or "schema" in fpath.lower() or "entity" in fpath.lower():
                role = "MODEL"
            elif "service" in fpath.lower() or "logic" in fpath.lower():
                role = "SERVICE"
            elif rec.purpose == "TEST":
                role = "TEST"
            elif rec.purpose == "CONFIG":
                role = "CONFIG"

            if role:
                important[fpath] = role
                tree_lines.append(f"  ├── {fpath} [{role}]")
            elif index.info.file_count <= 50:
                tree_lines.append(f"  ├── {fpath}")

        return RepositoryMap(tree_text="\n".join(tree_lines), important_files=important)


global_repository_indexer = RepositoryIndexer()
