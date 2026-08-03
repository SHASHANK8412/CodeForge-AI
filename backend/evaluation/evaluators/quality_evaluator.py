"""
AIForge Quality Evaluator
=========================
Evaluates response quality, contract compliance, required element presence,
forbidden element absence, code language matching, and deterministic RAG facts.
"""

import re
from typing import Dict, Any, List
from backend.quality.output_validator import global_output_validator
from backend.evaluation.models import GoldenTestCase


class QualityEvaluator:
    """
    Quality Evaluator leveraging Day 4 OutputValidator + Golden Test expectations.
    """

    def evaluate_quality(
        self,
        case: GoldenTestCase,
        response: str,
        actual_intent: str,
        actual_agent: str
    ) -> Dict[str, Any]:
        val_res = global_output_validator.validate(
            user_prompt=case.prompt,
            response=response,
            intent=actual_intent,
            agent=actual_agent,
            profile=actual_intent
        )

        r_lower = response.lower()

        # 1. Required Elements Check
        missing_required = []
        for req in case.required_elements:
            if req.lower() not in r_lower:
                missing_required.append(req)
        required_pass = (len(missing_required) == 0)

        # 2. Forbidden Elements Check
        found_forbidden = []
        for forb in case.forbidden_elements:
            if forb.lower() in r_lower:
                found_forbidden.append(forb)
        forbidden_pass = (len(found_forbidden) == 0)

        # 3. Code Language Match
        lang_pass = True
        if case.requires_code and case.expected_language:
            expected_lang = case.expected_language.lower()
            lang_pass = (f"```{expected_lang}" in r_lower or expected_lang in r_lower or "def " in r_lower or "function" in r_lower or "public class" in r_lower)

        # 4. RAG Facts Check
        rag_facts_pass = True
        missing_facts = []
        if case.requires_rag and case.expected_facts:
            for fact in case.expected_facts:
                if fact.lower() not in r_lower:
                    missing_facts.append(fact)
            rag_facts_pass = (len(missing_facts) == 0)

        # Combine checks into overall quality pass
        contract_pass = val_res.is_valid and forbidden_pass
        overall_pass = val_res.is_valid and required_pass and forbidden_pass and lang_pass and rag_facts_pass

        issues = list(val_res.issues)
        if missing_required:
            issues.append(f"Missing required elements: {missing_required}")
        if found_forbidden:
            issues.append(f"Found forbidden elements: {found_forbidden}")
        if not lang_pass:
            issues.append(f"Expected code language '{case.expected_language}' not detected.")
        if missing_facts:
            issues.append(f"Missing expected RAG facts: {missing_facts}")

        score = val_res.score * 100.0
        if not required_pass:
            score = max(0.0, score - 15.0)
        if not forbidden_pass:
            score = max(0.0, score - 30.0)

        return {
            "quality_score": round(score, 1),
            "contract_pass": contract_pass,
            "required_elements_pass": required_pass,
            "forbidden_elements_pass": forbidden_pass,
            "language_match_pass": lang_pass,
            "rag_facts_pass": rag_facts_pass,
            "overall_quality_pass": overall_pass,
            "issues": issues,
            "validation_result": val_res
        }


global_quality_evaluator = QualityEvaluator()
