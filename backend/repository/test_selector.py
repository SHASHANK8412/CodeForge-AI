"""
AIForge Test Selector
=====================
Selects targeted, affected, and full test suites for post-modification verification.
"""

import logging
from typing import List, Dict, Any, Optional

from backend.repository.models import ImpactAnalysis
from backend.repository.indexer import RepositoryIndex

_logger = logging.getLogger("aiforge.repository.test_selector")


class TestSelector:
    """
    Selects test suites based on dependency impact analysis.
    """

    def select_tests(self, impact: ImpactAnalysis, index: RepositoryIndex, level: str = "TARGETED") -> List[str]:
        if level == "TARGETED":
            return impact.candidate_tests

        selected = set(impact.candidate_tests)

        if level in ["AFFECTED", "FULL"]:
            for fpath in impact.dependent_files:
                for tfpath, rec in index.file_records.items():
                    if rec.purpose == "TEST" and fpath.replace("/", "_") in tfpath.replace("/", "_"):
                        selected.add(tfpath)

        if level == "FULL" or not selected:
            for fpath, rec in index.file_records.items():
                if rec.purpose == "TEST":
                    selected.add(fpath)

        return sorted(list(selected))


global_test_selector = TestSelector()
