"""
AIForge Repository Search Engine
================================
Provides fast structural, symbol, text, route, and model search over RepositoryIndex.
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional

from backend.repository.models import SymbolRecord, FileRecord
from backend.repository.indexer import RepositoryIndex

_logger = logging.getLogger("aiforge.repository.search")


class RepositorySearch:
    """
    Search engine over a RepositoryIndex.
    """

    def search_symbol(self, index: RepositoryIndex, symbol_query: str) -> List[SymbolRecord]:
        query_clean = symbol_query.strip().lower()
        results: List[SymbolRecord] = []

        if query_clean in index.symbols:
            return index.symbols[query_clean]

        for sym_name, sym_list in index.symbols.items():
            if query_clean in sym_name.lower():
                results.extend(sym_list)

        return results

    def search_files(self, index: RepositoryIndex, path_query: str) -> List[FileRecord]:
        query_clean = path_query.strip().lower()
        results: List[FileRecord] = []

        for fpath, rec in index.file_records.items():
            if query_clean in fpath.lower():
                results.append(rec)

        return results

    def search_routes(self, index: RepositoryIndex) -> List[SymbolRecord]:
        results: List[SymbolRecord] = []
        for sym_list in index.symbols.values():
            for sym in sym_list:
                if sym.kind == "route":
                    results.append(sym)
        return results

    def search_models(self, index: RepositoryIndex) -> List[SymbolRecord]:
        results: List[SymbolRecord] = []
        for sym_list in index.symbols.values():
            for sym in sym_list:
                if sym.kind == "model":
                    results.append(sym)
        return results


global_repository_search = RepositorySearch()
