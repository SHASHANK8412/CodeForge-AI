"""
AIForge Complexity Analyzer
===========================
Fast deterministic task complexity analyzer.
Analyzes user prompts, intent taxonomy, conversation context, and active project state
to compute a normalized complexity score and categorical level.
"""

import re
import logging
from typing import Dict, Any, List, Optional

from backend.reasoning.models import ComplexityLevel, ExecutionStrategy, ComplexityResult

_logger = logging.getLogger("aiforge.reasoning.complexity_analyzer")


class ComplexityAnalyzer:
    """
    Precision Task Complexity Analyzer.
    Determines task difficulty and determines whether planning or full workflow is required.
    """

    SCORE_THRESHOLDS = [
        (0.20, ComplexityLevel.TRIVIAL, ExecutionStrategy.DIRECT),
        (0.45, ComplexityLevel.SIMPLE, ExecutionStrategy.STANDARD),
        (0.89, ComplexityLevel.COMPLEX, ExecutionStrategy.PLANNED),
        (1.00, ComplexityLevel.WORKFLOW, ExecutionStrategy.WORKFLOW),
    ]

    ARCHITECTURE_KEYWORDS = [
        "architecture", "design", "schema", "microservice", "microservices",
        "distributed", "kafka", "redis", "postgres", "postgresql", "jwt",
        "refactor", "migration", "system design", "data model", "scaling",
        "compare", "recommendation", "scalability", "auth", "authentication",
        "caching", "specification", "specifications", "ats", "preparation"
    ]

    TECH_PATTERNS = [
        r"\bfastapi\b", r"\breact\b", r"\bpostgressql\b|\bpostgres\b", r"\bredis\b",
        r"\bkafka\b", r"\bdocker\b", r"\bkubernetes\b|\bk8s\b", r"\bmongodb\b",
        r"\bgraphql\b", r"\brest\b", r"\bjwt\b", r"\bnext\.?js\b", r"\bvue\b"
    ]

    BRIEF_PATTERNS = [
        r"\bbriefly\b", r"\bjust give the answer\b", r"\bno explanation\b",
        r"\bshort answer\b", r"\bin one sentence\b", r"\bquick answer\b"
    ]

    DEPTH_PATTERNS = [
        r"\bin depth\b", r"\bcomprehensively\b", r"\bstep by step\b",
        r"\bdetailed plan\b", r"\bdeeply analyze\b", r"\bfull analysis\b"
    ]

    TRIVIAL_PROMPTS = [
        "what is python", "what is rest", "capital of japan", "what is sql",
        "what does cpu stand for", "explain git", "reverse a string in python",
        "reverse string in python", "what is docker", "what is recursion",
        "what is postgresql", "what does api stand for", "what is http",
        "explain formula 1"
    ]

    def analyze(
        self,
        prompt: str,
        intent: str,
        context_result: Optional[Any] = None,
        task_metadata: Optional[Dict[str, Any]] = None
    ) -> ComplexityResult:
        if not prompt or not prompt.strip():
            return ComplexityResult(
                level=ComplexityLevel.TRIVIAL,
                score=0.10,
                strategy=ExecutionStrategy.DIRECT,
                signals=["empty_prompt"],
                confidence=1.0,
                requires_planning=False,
                requires_workflow=False
            )

        prompt_clean = prompt.strip().lower()
        signals: List[str] = []

        # Rule 1: CRITICAL INTENT OVERRIDE — PROJECT_GENERATION ALWAYS ACTIVATES WORKFLOW
        if intent == "PROJECT_GENERATION" or any(p in prompt_clean for p in ["build a complete", "create a complete", "generate a react", "build an ecommerce"]):
            _logger.info(f"[ComplexityAnalyzer] Override Applied: PROJECT_GENERATION intent -> WORKFLOW")
            return ComplexityResult(
                level=ComplexityLevel.WORKFLOW,
                score=1.00,
                strategy=ExecutionStrategy.WORKFLOW,
                signals=["project_generation_intent", "multi_agent_workflow_required"],
                confidence=1.0,
                requires_planning=True,
                requires_workflow=True,
                override_applied="PROJECT_GENERATION_WORKFLOW"
            )

        # Rule 2: Explicit Trivial Short Prompt Check
        if prompt_clean.rstrip("?").strip() in [p.lower() for p in self.TRIVIAL_PROMPTS]:
            return ComplexityResult(
                level=ComplexityLevel.TRIVIAL,
                score=0.10,
                strategy=ExecutionStrategy.DIRECT,
                signals=["known_trivial_fact_query"],
                confidence=0.95,
                requires_planning=False,
                requires_workflow=False
            )

        base_score = 0.25  # Start at simple base

        # Signal 1: Prompt Length
        word_count = len(prompt_clean.split())
        if word_count > 40:
            base_score += 0.15
            signals.append("long_prompt")
        elif word_count > 20:
            base_score += 0.05

        # Signal 2: Multiple Technology Mentions
        tech_count = sum(1 for pat in self.TECH_PATTERNS if re.search(pat, prompt_clean))
        if tech_count >= 3:
            base_score += 0.30
            signals.append("multi_technology_stack")
        elif tech_count == 2:
            base_score += 0.15
            signals.append("dual_technology_stack")

        # Signal 3: Architecture & Design Language
        arch_matches = sum(1 for kw in self.ARCHITECTURE_KEYWORDS if kw in prompt_clean)
        if arch_matches >= 3:
            base_score += 0.25
            signals.append("architecture_design_language")
        elif arch_matches >= 1:
            base_score += 0.10
            signals.append("design_keyword")

        # Signal 4: Multi-Requirement Clauses ("and", "with", comma lists)
        requirements_count = len(re.split(r",|\band\b|\bwith\b|\bplus\b", prompt_clean)) - 1
        if requirements_count >= 3:
            base_score += 0.15
            signals.append("multiple_requirements")

        # Signal 5: Explicit Depth Requests ("step by step", "in depth")
        if any(re.search(pat, prompt_clean) for pat in self.DEPTH_PATTERNS):
            base_score += 0.15
            signals.append("explicit_depth_request")

        # Signal 6: User Briefness Instruction ("briefly", "just answer")
        if any(re.search(pat, prompt_clean) for pat in self.BRIEF_PATTERNS):
            base_score -= 0.15
            signals.append("briefness_requested")

        # Signal 7: Conversation Context & Active Project Follow-Up (Day 7 Integration)
        if context_result and getattr(context_result, "is_follow_up", False) and not getattr(context_result, "topic_shift", False):
            if any(term in prompt_clean for term in ["add", "modify", "refactor", "change", "now", "also", "rotation", "revocation"]):
                base_score += 0.25
                signals.append("active_context_modification_followup")

        # Intent-Based Caps & Normalizations
        if intent in ["GENERAL_QA", "EXPLANATION", "RAG_QUERY", "RESUME"] and not any(kw in prompt_clean for kw in ["architecture", "kubernetes", "microservices", "system design", "compare", "specifications", "analyze complete"]):
            # Cap simple queries at 0.40 (SIMPLE / DIRECT / STANDARD)
            base_score = min(base_score, 0.40)
            signals.append("intent_simple_cap")

        # Clamp normalized score to [0.0, 1.0]
        final_score = round(max(0.0, min(1.0, base_score)), 2)

        # Map final score to categorical level & strategy
        level = ComplexityLevel.SIMPLE
        strategy = ExecutionStrategy.STANDARD

        for threshold, lvl, strat in self.SCORE_THRESHOLDS:
            if final_score <= threshold:
                level = lvl
                strategy = strat
                break

        requires_plan = level in [ComplexityLevel.MODERATE, ComplexityLevel.COMPLEX, ComplexityLevel.WORKFLOW]
        requires_wf = (level == ComplexityLevel.WORKFLOW)

        _logger.info(
            f"[ComplexityAnalyzer] Prompt: '{prompt[:40]}' | Intent: {intent} | "
            f"Score: {final_score} | Level: {level.value} | Strategy: {strategy.value} | Signals: {signals}"
        )

        return ComplexityResult(
            level=level,
            score=final_score,
            strategy=strategy,
            signals=signals,
            confidence=0.90,
            requires_planning=requires_plan,
            requires_workflow=requires_wf
        )


global_complexity_analyzer = ComplexityAnalyzer()
