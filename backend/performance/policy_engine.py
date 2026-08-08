"""
AIForge Quality Recovery Day 14 — Execution Policy Engine & Path Routing
========================================================================
Determines WHEN NOT TO USE AIForge's features.
Evaluates request signals deterministically first, then constructs a typed
ExecutionPlan short-circuiting unnecessary pipeline stages.
"""

import re
import logging
from typing import Optional, Dict, Any

from backend.performance.models import ExecutionPlan, PipelinePath, RequestBudget
from backend.performance.config import global_performance_config

logger = logging.getLogger("aiforge.performance.policy_engine")


class ExecutionPolicyEngine:
    """
    Analyzes prompt signals, repository state, and request requirements to output
    a deterministic ExecutionPlan.
    """

    def analyze(
        self,
        prompt: str,
        has_documents: bool = False,
        active_repo_files: Optional[list] = None,
        has_active_repo: bool = False,
        intent_override: Optional[str] = None
    ) -> ExecutionPlan:
        """
        Main entry point for determining the minimal required pipeline execution plan.
        """
        p_lower = prompt.lower().strip()

        # 1. Check Engineering Workflow Path (Issue fix, PR preparation, multi-file code editing)
        is_issue_task = bool(re.search(r"\b(?:issue\s*#?\d+|fix\s+bug|pr\s+preparation|refactor\s+service)\b", p_lower))
        if is_issue_task or intent_override in ("GIT_WORKFLOW", "MULTI_FILE_EDIT", "ISSUE_TO_CODE"):
            return ExecutionPlan(
                path=PipelinePath.ENGINEERING_WORKFLOW,
                use_planner=True,
                use_rag=True,
                use_repository=True,
                use_review=True,
                use_execution=True,
                use_tests=True,
                use_grounding=True,
                use_git=True,
                allow_parallel=True,
                model_tier="strong",
                budgets=RequestBudget(
                    max_total_ms=global_performance_config.WORKFLOW_TIMEOUT_SECONDS * 1000.0,
                    max_model_calls=global_performance_config.MAX_MODEL_CALLS_WORKFLOW,
                    max_tool_calls=20,
                    max_retries=3,
                    max_review_cycles=2,
                    max_debug_cycles=2
                ),
                reasoning="Engineering workflow required for repository modification / issue fix."
            )

        # 2. Check Document Retrieval Path (Explicit document reference or uploaded doc)
        if has_documents or re.search(r"\b(?:according to|document|pdf|spec sheet|uploaded|file)\b", p_lower):
            if not is_issue_task and not has_active_repo:
                return ExecutionPlan(
                    path=PipelinePath.RETRIEVAL,
                    use_planner=False,
                    use_rag=True,
                    use_repository=False,
                    use_review=False,
                    use_execution=False,
                    use_tests=False,
                    use_grounding=True,
                    use_git=False,
                    allow_parallel=True,
                    model_tier="standard",
                    budgets=RequestBudget(
                        max_total_ms=30000.0,
                        max_model_calls=2,
                        max_tool_calls=5,
                        max_retries=2,
                        max_review_cycles=0,
                        max_debug_cycles=0
                    ),
                    reasoning="Retrieval path selected for document-based question."
                )

        # 3. Check Repository Read-Only Path
        has_file_path = bool(re.search(r"\b[\w_\-\/]+\.(?:py|js|ts|json|md|html|css|txt)\b", p_lower))
        if (has_active_repo or active_repo_files or has_file_path) and re.search(r"\b(?:where|explain|how|search|find|located|implemented|dependencies|architecture)\b", p_lower):
            return ExecutionPlan(
                path=PipelinePath.REPOSITORY,
                use_planner=False,
                use_rag=True,
                use_repository=True,
                use_review=False,
                use_execution=False,
                use_tests=False,
                use_grounding=True,
                use_git=False,
                allow_parallel=True,
                model_tier="standard",
                budgets=RequestBudget(
                    max_total_ms=30000.0,
                    max_model_calls=2,
                    max_tool_calls=5,
                    max_retries=2,
                    max_review_cycles=0,
                    max_debug_cycles=0
                ),
                reasoning="Repository read-only path selected for codebase query."
            )

        # 4. Check FAST Explanation Path
        is_generic_explanation = bool(re.search(r"^(?:explain|what is|how does|define|summarize|tell me about)\s+(?!.*(?:this repo|codebase|file|document|bug|issue))", p_lower))
        is_formula1 = "formula 1" in p_lower or "f1" in p_lower
        if (is_generic_explanation or is_formula1) and not has_documents and not has_active_repo:
            return ExecutionPlan(
                path=PipelinePath.FAST,
                use_planner=False,
                use_rag=False,
                use_repository=False,
                use_review=False,
                use_execution=False,
                use_tests=False,
                use_grounding=False,
                use_git=False,
                allow_parallel=False,
                model_tier="fast",
                budgets=RequestBudget(
                    max_total_ms=15000.0,
                    max_model_calls=global_performance_config.MAX_MODEL_CALLS_FAST,
                    max_tool_calls=0,
                    max_retries=1,
                    max_review_cycles=0,
                    max_debug_cycles=0
                ),
                reasoning="FAST path selected for standalone conceptual explanation."
            )

        # 5. Check FAST Coding Path
        is_simple_coding = bool(re.search(r"^(?:write|create|implement|code|generate)\s+(?:a\s+)?(?:python|javascript|java|c\+\+|ts|script|function|program|algorithm|binary search|palindrome|factorial|fibonacci|reverse|sort)", p_lower))
        if is_simple_coding and not has_documents and not has_active_repo:
            return ExecutionPlan(
                path=PipelinePath.FAST_CODING,
                use_planner=False,
                use_rag=False,
                use_repository=False,
                use_review=False,
                use_execution=True,  # Lightweight execution for validation
                use_tests=False,
                use_grounding=False,
                use_git=False,
                allow_parallel=False,
                model_tier="standard",
                budgets=RequestBudget(
                    max_total_ms=20000.0,
                    max_model_calls=global_performance_config.MAX_MODEL_CALLS_FAST,
                    max_tool_calls=1,
                    max_retries=1,
                    max_review_cycles=0,
                    max_debug_cycles=0
                ),
                reasoning="FAST_CODING path selected for simple standalone algorithm."
            )

        # 6. Default Standard Path
        return ExecutionPlan(
            path=PipelinePath.STANDARD,
            use_planner=False,
            use_rag=False,
            use_repository=False,
            use_review=True,
            use_execution=True,
            use_tests=False,
            use_grounding=False,
            use_git=False,
            allow_parallel=True,
            model_tier="standard",
            budgets=RequestBudget(
                max_total_ms=40000.0,
                max_model_calls=global_performance_config.MAX_MODEL_CALLS_STANDARD,
                max_tool_calls=5,
                max_retries=2,
                max_review_cycles=1,
                max_debug_cycles=1
            ),
            reasoning="Standard execution path selected."
        )


global_execution_policy_engine = ExecutionPolicyEngine()
