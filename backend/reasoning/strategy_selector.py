"""
AIForge Execution Strategy Selector
===================================
Selects execution strategy (DIRECT, STANDARD, PLANNED, WORKFLOW) based on task complexity,
intent taxonomy, and conversation context.
"""

import logging
from typing import Optional, Any

from backend.reasoning.models import ComplexityResult, ExecutionStrategy, ComplexityLevel

_logger = logging.getLogger("aiforge.reasoning.strategy_selector")


class ExecutionStrategySelector:
    """
    Selects execution strategy for AIForge canonical generation pipeline.
    """

    def select(
        self,
        complexity_result: ComplexityResult,
        intent: str,
        context_result: Optional[Any] = None
    ) -> ExecutionStrategy:
        # Override 1: PROJECT_GENERATION intent -> WORKFLOW
        if intent == "PROJECT_GENERATION" or complexity_result.level == ComplexityLevel.WORKFLOW:
            _logger.info("[StrategySelector] Selecting WORKFLOW strategy for PROJECT_GENERATION intent")
            return ExecutionStrategy.WORKFLOW

        # Override 2: TRIVIAL complexity -> DIRECT
        if complexity_result.level == ComplexityLevel.TRIVIAL:
            _logger.info("[StrategySelector] Selecting DIRECT strategy for TRIVIAL complexity")
            return ExecutionStrategy.DIRECT

        # Override 3: SIMPLE complexity -> STANDARD
        if complexity_result.level == ComplexityLevel.SIMPLE:
            _logger.info("[StrategySelector] Selecting STANDARD strategy for SIMPLE complexity")
            return ExecutionStrategy.STANDARD

        # Override 4: MODERATE / COMPLEX -> PLANNED
        if complexity_result.level in [ComplexityLevel.MODERATE, ComplexityLevel.COMPLEX]:
            _logger.info("[StrategySelector] Selecting PLANNED strategy for MODERATE/COMPLEX task")
            return ExecutionStrategy.PLANNED

        return ExecutionStrategy.STANDARD


global_strategy_selector = ExecutionStrategySelector()
