"""
AIForge Repository Context Retriever
====================================
Retrieves targeted, symbol-level and file-level repository context.
Enforces context reduction (DOES NOT SEND THE ENTIRE REPOSITORY TO THE LLM).
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple

from backend.repository.models import RepositoryTask, ImpactAnalysis
from backend.repository.indexer import RepositoryIndex
from backend.repository.scanner import global_repository_scanner

_logger = logging.getLogger("aiforge.repository.retriever")

MAX_RETRIEVED_FILES = 8
MAX_RETRIEVED_CHARS = 12000  # Strict context budget limit


class RepositoryContextRetriever:
    """
    Retrieves targeted, secret-redacted repository context.
    """

    def retrieve_context(
        self,
        index: RepositoryIndex,
        task: RepositoryTask,
        impact: ImpactAnalysis
    ) -> Tuple[str, List[str]]:
        selected_paths: List[str] = []

        # Priority 1: Primary impacted files
        for p in impact.primary_files:
            if len(selected_paths) < MAX_RETRIEVED_FILES:
                selected_paths.append(p)

        # Priority 2: Candidate tests
        for t in impact.candidate_tests:
            if len(selected_paths) < MAX_RETRIEVED_FILES and t not in selected_paths:
                selected_paths.append(t)

        # Priority 3: Dependent files
        for d in impact.dependent_files:
            if len(selected_paths) < MAX_RETRIEVED_FILES and d not in selected_paths:
                selected_paths.append(d)

        # Build concise context block
        context_blocks = []
        if index.repository_map:
            context_blocks.append(f"REPOSITORY STRUCTURE:\n{index.repository_map.tree_text}\n")

        total_chars = 0
        for rel_path in selected_paths:
            full_path = os.path.join(index.info.root_path, rel_path)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    raw = f.read()
                    # Redact secrets
                    clean = global_repository_scanner.redact_secrets(raw)
                    block = f"--- FILE: {rel_path} ---\n{clean}\n"
                    if total_chars + len(block) > MAX_RETRIEVED_CHARS:
                        block = f"--- FILE: {rel_path} (TRUNCATED) ---\n{clean[:2000]}\n"
                    context_blocks.append(block)
                    total_chars += len(block)
                    if total_chars >= MAX_RETRIEVED_CHARS:
                        break
            except Exception as e:
                _logger.debug(f"[RepositoryContextRetriever] Could not read '{rel_path}': {e}")

        context_text = "\n".join(context_blocks)
        _logger.info(f"[RepositoryContextRetriever] Retrieved {len(selected_paths)} targeted files ({total_chars} chars) out of {index.info.file_count} total files")

        return context_text, selected_paths


global_repository_context_retriever = RepositoryContextRetriever()
