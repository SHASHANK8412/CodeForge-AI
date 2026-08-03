"""
AIForge Change Planner
======================
Constructs a structured ChangePlan for proposed repository modifications.
"""

import logging
from typing import List, Dict, Any, Optional

from backend.repository.models import RepositoryTask, ImpactAnalysis, ChangePlan
from backend.repository.indexer import RepositoryIndex

_logger = logging.getLogger("aiforge.repository.change_planner")


class ChangePlanner:
    """
    Builds structured ChangePlans with file modification justifications.
    """

    def create_plan(
        self,
        user_prompt: str,
        task: RepositoryTask,
        impact: ImpactAnalysis,
        index: RepositoryIndex
    ) -> ChangePlan:
        reasons: Dict[str, str] = {}
        files_to_modify: List[str] = []
        files_to_create: List[str] = []

        for pfile in impact.primary_files:
            files_to_modify.append(pfile)
            reasons[pfile] = "Primary target for requested feature/fix"

        # If user explicitly asks for new file
        if "add new file" in user_prompt.lower() or "create" in user_prompt.lower():
            if not files_to_modify:
                new_f = "backend/services/new_feature.py"
                files_to_create.append(new_f)
                reasons[new_f] = "New implementation file"

        steps = [
            f"1. Modify target files ({', '.join(files_to_modify or files_to_create)})",
            "2. Update or add corresponding tests",
            "3. Run test verification suite in sandbox"
        ]

        return ChangePlan(
            goal=user_prompt,
            files_to_modify=files_to_modify,
            files_to_create=files_to_create,
            tests_to_run=impact.candidate_tests,
            steps=steps,
            risk=impact.risk_level,
            reasons=reasons
        )


global_change_planner = ChangePlanner()
