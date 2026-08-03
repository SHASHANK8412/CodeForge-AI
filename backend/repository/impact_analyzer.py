"""
AIForge Impact Analyzer
=======================
Performs dependency graph traversal and symbol matching to identify primary
impacted files, dependent files, candidate tests, and risk level.
"""

import os
import logging
from typing import List, Dict, Set, Optional

from backend.repository.models import RepositoryTask, ImpactAnalysis
from backend.repository.indexer import RepositoryIndex
from backend.repository.search import global_repository_search

_logger = logging.getLogger("aiforge.repository.impact")


class ImpactAnalyzer:
    """
    Analyzes repository impact for a proposed task.
    """

    def analyze_impact(self, task: RepositoryTask, index: RepositoryIndex) -> ImpactAnalysis:
        primary_files: Set[str] = set()
        dependent_files: Set[str] = set()
        candidate_tests: Set[str] = set()
        reasons: List[str] = []

        # 1. Match primary files by symbols & target features
        for sym_name in task.target_symbols:
            matched_syms = global_repository_search.search_symbol(index, sym_name)
            for sym in matched_syms:
                primary_files.add(sym.file)
                reasons.append(f"Matched target symbol '{sym.name}' in '{sym.file}'")

        for feat in task.target_features:
            feat_term = "auth" if "auth" in feat else feat
            matched_files = global_repository_search.search_files(index, feat_term)
            for rec in matched_files:
                if rec.purpose != "TEST":
                    primary_files.add(rec.path)
                    reasons.append(f"Matched target feature keyword '{feat}' in '{rec.path}'")

        # 2. Traverse dependency graph for reverse dependencies
        for pfile in list(primary_files):
            rev_deps = index.get_reverse_dependencies(pfile)
            for rdep in rev_deps:
                rec = index.file_records.get(rdep)
                if rec and rec.purpose == "TEST":
                    candidate_tests.add(rdep)
                elif rdep not in primary_files:
                    dependent_files.add(rdep)

        # 3. Collect test files related to primary files
        for pfile in primary_files:
            stem = os.path.splitext(os.path.basename(pfile))[0]
            for fpath, rec in index.file_records.items():
                if rec.purpose == "TEST" and (stem in fpath or fpath.endswith(f"test_{stem}.py") or fpath.endswith(f"{stem}.test.js")):
                    candidate_tests.add(fpath)

        # Classify risk level
        risk = "LOW"
        if len(primary_files) > 3 or any("auth" in p or "db" in p for p in primary_files):
            risk = "HIGH"
        elif len(primary_files) > 1:
            risk = "MEDIUM"

        return ImpactAnalysis(
            primary_files=sorted(list(primary_files)),
            dependent_files=sorted(list(dependent_files)),
            candidate_tests=sorted(list(candidate_tests)),
            risk_level=risk,
            reason_labels=reasons
        )


global_impact_analyzer = ImpactAnalyzer()
