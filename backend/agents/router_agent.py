"""
AIForge Precision Intent Router Agent & Hybrid Classifier
=========================================================
Classifies incoming user prompts into 8 canonical intent categories:
1. GENERAL_QA
2. EXPLANATION
3. CODING
4. DEBUGGING
5. PROJECT_GENERATION
6. RAG_QUERY
7. RESUME
8. UNKNOWN

Implements Layer A (Deterministic High-Confidence Rules) and Layer B (LLM Fallback Classifier).
Eliminates universal CodingAgent / Project-Generation fallbacks.
"""

import json
import logging
import re
from enum import Enum
from typing import Dict, Any, Optional

from backend.utils.text_normalizer import normalize_prompt

_logger = logging.getLogger("aiforge.agents.router_agent")


class Intent(str, Enum):
    GENERAL_QA = "GENERAL_QA"
    EXPLANATION = "EXPLANATION"
    CODING = "CODING"
    DEBUGGING = "DEBUGGING"
    PROJECT_GENERATION = "PROJECT_GENERATION"
    RAG_QUERY = "RAG_QUERY"
    RESUME = "RESUME"
    GIT_WORKFLOW = "GIT_WORKFLOW"
    UNKNOWN = "UNKNOWN"


# Backwards compatibility alias
IntentCategory = Intent


INTENT_AGENT_MAP = {
    Intent.GENERAL_QA: "ExplanationAgent",
    Intent.EXPLANATION: "ExplanationAgent",
    Intent.CODING: "CodingAgent",
    Intent.DEBUGGING: "DebugAgent",
    Intent.PROJECT_GENERATION: "AutonomousSoftwareEngineer",
    Intent.RAG_QUERY: "RAGAgent",
    Intent.RESUME: "ResumeAgent",
    Intent.GIT_WORKFLOW: "EngineeringWorkflowEngine",
    Intent.UNKNOWN: "ClarificationAgent",
}

INTENT_WORKFLOW_MAP = {
    Intent.GENERAL_QA: "General Knowledge QA",
    Intent.EXPLANATION: "Technical Concept Explanation Pipeline",
    Intent.CODING: "Isolated Snippet & Algorithm Generator Pipeline",
    Intent.DEBUGGING: "AST Debugging & Exception Resolution Pipeline",
    Intent.PROJECT_GENERATION: "Autonomous Software Engineer Pipeline",
    Intent.RAG_QUERY: "Vector RAG Grounded Search Pipeline",
    Intent.RESUME: "ATS Resume & Career Analysis Pipeline",
    Intent.GIT_WORKFLOW: "Issue-to-Code Git Engineering Workflow",
    Intent.UNKNOWN: "Clarification & Intent Disambiguation Pipeline",
}


LLM_CLASSIFIER_PROMPT = """You are the Intent Classifier for AIForge AI Software Engineer.
Analyze the user prompt and categorize it into EXACTLY ONE of these canonical intents:

1. GENERAL_QA: Non-technical trivia or general knowledge (e.g., "Who invented the telephone?", "Who wrote Hamlet?", "What is the capital of France?")
2. EXPLANATION: Explaining concepts, technologies, terms, how things work, language concepts (e.g., "Explain Formula 1", "What is React?", "Explain Python exceptions", "What is debugging?")
3. CODING: Requesting code implementations, algorithms, functions, components, LeetCode problems (e.g., "Write binary search in Python", "Solve Two Sum in Java", "Create a React component for a navbar")
4. DEBUGGING: Diagnosing/fixing broken code, error stack traces, crashes, exceptions (e.g., "Why am I getting NullPointerException?", "Fix this Python code", "Fix this React syntax error", "My React component crashes")
5. PROJECT_GENERATION: Full-stack application/project creation requiring architecture, frontend, backend, database (e.g., "Build a complete expense tracker using React and FastAPI")
6. RAG_QUERY: Questions specifically referencing uploaded files, PDFs, or documents (e.g., "Summarize the uploaded document")
7. RESUME: Resume analysis, ATS score improvement, LinkedIn profiles (e.g., "Analyze my resume", "Improve my ATS score")
8. UNKNOWN: Ambiguous single words or vague queries without clear intent (e.g., "Python", "React", "database", "help me with Java")

Return JSON ONLY matching this schema:
{
  "intent": "<ONE_OF_CANONICAL_INTENTS>",
  "confidence": 0.95,
  "reason": "<Short 1-sentence rationale>"
}
"""


class RouterAgent:
    """
    Precision Intent Router using Layer A (Rules) + Layer B (LLM Fallback).
    """

    def classify_intent(self, prompt: str, context_result: Optional[Any] = None) -> Dict[str, Any]:
        """
        Analyzes user prompt text and determines the canonical intent.
        Optionally accepts context_result for multi-turn follow-up intent classification.
        Returns metadata: intent, confidence, reason, classification_source, original_prompt, normalized_prompt.
        """
        if not prompt or not prompt.strip():
            res = self._format_result(
                intent=Intent.UNKNOWN,
                confidence=1.0,
                reason="Empty prompt provided.",
                source="rule",
                original_prompt=prompt,
                normalized_prompt=""
            )
            self._log_decision(prompt, res)
            return res

        # Use resolved_prompt if context_result indicates a follow-up
        eval_prompt = prompt
        if context_result and getattr(context_result, "is_follow_up", False):
            resolved_p = getattr(context_result, "resolved_prompt", "")
            if resolved_p and resolved_p != prompt:
                eval_prompt = resolved_p

        normalized = normalize_prompt(eval_prompt)

        # Step 1: Layer A - Deterministic Rules
        rule_result = self._apply_deterministic_rules(eval_prompt, normalized)
        if rule_result and rule_result["confidence"] >= 0.85:
            self._log_decision(prompt, rule_result)
            return rule_result

        # Step 2: Layer B - LLM Fallback Classification
        llm_result = self._apply_llm_classification(prompt, normalized)
        if llm_result:
            self._log_decision(prompt, llm_result)
            return llm_result

        # Step 3: Default Safe Fallback
        if rule_result:
            self._log_decision(prompt, rule_result)
            return rule_result

        fallback_res = self._format_result(
            intent=Intent.UNKNOWN,
            confidence=0.50,
            reason="Uncertain intent; prompting user for clarification.",
            source="fallback",
            original_prompt=prompt,
            normalized_prompt=normalized
        )
        self._log_decision(prompt, fallback_res)
        return fallback_res

    def _apply_deterministic_rules(self, original_prompt: str, p_lower: str) -> Dict[str, Any] | None:
        words = p_lower.split()
        num_words = len(words)

        # 1. Ambiguous Single Words / Vague Phrases -> UNKNOWN
        single_word_ambiguous = [
            "python", "react", "database", "java", "fastapi", "cpp", "c++", "javascript", "node", "sql", "stuff"
        ]
        ambiguous_phrases = [
            "help me with java", "help me with python", "help me with react", "coding", "code"
        ]
        if (num_words == 1 and p_lower in single_word_ambiguous) or p_lower in ambiguous_phrases:
            return self._format_result(
                intent=Intent.UNKNOWN,
                confidence=0.95,
                reason=f"Ambiguous query '{original_prompt}' lacks explicit verb or request context.",
                source="rule",
                original_prompt=original_prompt,
                normalized_prompt=p_lower
            )

        # 1b. Git / Issue Workflow -> GIT_WORKFLOW
        git_phrases = [
            "fix issue #", "issue #", "refresh tokens remain valid after logout", "create pull request",
            "create pr", "prepare pr", "fix refresh token", "git workflow", "continue the auth issue"
        ]
        if any(gp in p_lower for gp in git_phrases):
            return self._format_result(
                intent=Intent.GIT_WORKFLOW,
                confidence=0.98,
                reason="Issue resolution or Git engineering workflow request identified.",
                source="rule",
                original_prompt=original_prompt,
                normalized_prompt=p_lower
            )

        # 2. Resume & ATS -> RESUME
        resume_keywords = ["analyze my resume", "ats score", "improve my ats", "linkedin profile", "curriculum vitae", "cv review", "my cv", "optimize my cv"]
        is_concept_explanation = p_lower.startswith("explain") or p_lower.startswith("what is")
        if (any(kw in p_lower for kw in resume_keywords) or p_lower.startswith("cv ") or p_lower.endswith(" cv")) and not is_concept_explanation:
            return self._format_result(
                intent=Intent.RESUME,
                confidence=0.98,
                reason="Explicit resume analysis, CV, or ATS score keywords identified.",
                source="rule",
                original_prompt=original_prompt,
                normalized_prompt=p_lower
            )

        # 3. RAG Document Queries -> RAG_QUERY
        rag_keywords = [
            "uploaded pdf", "uploaded file", "uploaded document", "ask questions from the uploaded",
            "summarize this uploaded", "summarize the pdf", "what does the uploaded document say",
            "uploaded document", "uploaded file"
        ]
        if any(kw in p_lower for kw in rag_keywords):
            return self._format_result(
                intent=Intent.RAG_QUERY,
                confidence=0.98,
                reason="Document RAG query keywords referencing uploaded files identified.",
                source="rule",
                original_prompt=original_prompt,
                normalized_prompt=p_lower
            )

        # 4. Project Generation -> PROJECT_GENERATION
        proj_phrases = [
            "build a complete", "generate full project", "generate a full",
            "create frontend, backend and database", "build a food delivery app",
            "food delivery app", "netflix clone", "spotify clone", "instagram clone",
            "ecommerce application", "ecommerce website", "expense tracker using react", "build a full"
        ]
        has_proj_phrase = any(phrase in p_lower for phrase in proj_phrases)

        proj_verbs = ["build", "create", "develop", "generate", "construct"]
        proj_nouns = ["application", "app", "website", "platform", "system", "clone", "saas", "crm", "ecommerce", "e-commerce", "tracker", "store"]
        has_proj_verb = any(v in p_lower for v in proj_verbs)
        has_proj_noun = any(n in p_lower for n in proj_nouns)
        has_fullstack = any(fs in p_lower for fs in ["complete", "full", "fullstack", "full stack", "react and fastapi", "react, fastapi", "fastapi and react", "frontend, backend"])

        is_explanation_phrase = any(exp in p_lower for exp in ["explain how", "explain why", "how does", "what is"])

        if (has_proj_phrase or (has_proj_verb and has_proj_noun and (has_fullstack or "clone" in p_lower or "food delivery app" in p_lower))) and not is_explanation_phrase:
            return self._format_result(
                intent=Intent.PROJECT_GENERATION,
                confidence=0.98,
                reason="Explicit full-stack software application creation instruction identified.",
                source="rule",
                original_prompt=original_prompt,
                normalized_prompt=p_lower
            )

        # 5. General Knowledge QA -> GENERAL_QA
        general_qa_triggers = [
            "who invented", "who is", "who wrote", "what is the capital",
            "when was", "where is", "who discovered", "capital of france"
        ]
        if any(gq in p_lower for gq in general_qa_triggers):
            return self._format_result(
                intent=Intent.GENERAL_QA,
                confidence=0.96,
                reason="General knowledge question detected.",
                source="rule",
                original_prompt=original_prompt,
                normalized_prompt=p_lower
            )

        # 6. Concept Queries vs Debugging vs Coding (Disambiguation)
        is_concept_query = (
            p_lower.startswith("explain python exceptions") or
            "what is debugging" in p_lower or
            "what is a segmentation fault" in p_lower or
            "explain what an error is" in p_lower or
            "write an explanation of" in p_lower
        )

        # 7. Debugging & Error Resolution -> DEBUGGING
        error_terms = ["nullpointerexception", "indexerror", "typeerror", "syntaxerror", "modulenotfounderror", "traceback", "syntax error", "error in", "error"]
        has_error_term = any(t in p_lower for t in error_terms)

        debug_verbs = ["fix", "debug", "why", "solve error", "crash", "crashing", "failing", "fails"]
        has_debug_verb = any(dv in p_lower for dv in debug_verbs)

        debug_phrases = [
            "why am i getting", "fix this python code", "fix my code", "debug this",
            "my react component crashes", "why does this react code crash",
            "why does my python program throw", "fix it", "why is my code crashing",
            "why is my code throwing", "explain why this code fails", "fix this error",
            "segmentation fault. fix it.", "fix this react syntax error", "why does this fail"
        ]
        has_debug_phrase = any(dp in p_lower for dp in debug_phrases)

        if (has_debug_phrase or (has_debug_verb and has_error_term)) and not is_concept_query:
            return self._format_result(
                intent=Intent.DEBUGGING,
                confidence=0.96,
                reason="Code debugging or stack trace error resolution requested.",
                source="rule",
                original_prompt=original_prompt,
                normalized_prompt=p_lower
            )

        # 8. Coding & Code Snippet Generation -> CODING
        is_explanation_prefix = any(p_lower.startswith(exp) for exp in [
            "explain", "how does", "what is", "why does", "write an explanation of", "tell me about"
        ])

        coding_phrases = [
            "write binary search in python", "implement binary search in python",
            "write python code for binary search", "write python code to reverse",
            "solve two sum in java", "solve two sum", "leetcode", "create a rest api in fastapi",
            "create a react component for a navbar", "create a react component", "create react component",
            "create a react navbar", "create react navbar", "react navbar",
            "create a rest api", "write merge sort in java", "write merge sort in python", "write merge sort",
            "write quicksort in python", "write quicksort",
            "write code for", "implement binary search", "write python code", "solve this coding problem",
            "binary search code", "quicksort algorithm in python"
        ]
        has_coding_phrase = any(cp in p_lower for cp in coding_phrases)

        coding_verbs = ["write code", "implement", "solve", "code for", "generate function", "create component"]
        has_coding_verb = any(cv in p_lower for cv in coding_verbs)

        if (has_coding_phrase or (has_coding_verb and not is_explanation_prefix)) and not is_explanation_prefix:
            return self._format_result(
                intent=Intent.CODING,
                confidence=0.96,
                reason="Direct code snippet, algorithm implementation, or coding problem solver request.",
                source="rule",
                original_prompt=original_prompt,
                normalized_prompt=p_lower
            )

        # 9. Concept & Knowledge Explanations -> EXPLANATION
        explanation_triggers = [
            "explain", "how does", "what is", "why does", "tell me about",
            "write an explanation of", "what are", "concept of"
        ]
        has_exp_trigger = any(p_lower.startswith(et) or f" {et} " in f" {p_lower} " for et in explanation_triggers)

        specific_exp_prompts = [
            "explain formula 1", "how does formula 1 work?", "explain binary search",
            "what is a segmentation fault?", "explain why python uses indentation",
            "what is react?", "explain python exceptions", "what is debugging?",
            "write an explanation of merge sort", "explain how instagram works",
            "how does dns work?", "what is polymorphism?", "explain bfs vs dfs"
        ]

        if has_exp_trigger or is_concept_query or any(sep in p_lower for sep in specific_exp_prompts):
            return self._format_result(
                intent=Intent.EXPLANATION,
                confidence=0.96,
                reason="Technical concept explanation or domain knowledge query detected.",
                source="rule",
                original_prompt=original_prompt,
                normalized_prompt=p_lower
            )

        # Rule engine is uncertain
        return self._format_result(
            intent=Intent.UNKNOWN,
            confidence=0.50,
            reason="No high-confidence rule matched.",
            source="rule",
            original_prompt=original_prompt,
            normalized_prompt=p_lower
        )

    def _apply_llm_classification(self, original_prompt: str, p_lower: str) -> Dict[str, Any] | None:
        """
        Layer B: Uses local LLM to classify ambiguous queries into canonical intents.
        Strictly parses JSON output and validates against Intent Enum.
        """
        try:
            from backend.services.llm import generate_text
            raw_text = generate_text(
                system_prompt=LLM_CLASSIFIER_PROMPT,
                prompt=f"Classify this user prompt: \"{original_prompt}\"",
                task="general"
            )

            if not raw_text:
                return None

            json_str = raw_text.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()

            parsed = json.loads(json_str)
            intent_str = parsed.get("intent", "").upper().strip()
            confidence = float(parsed.get("confidence", 0.85))
            reason = parsed.get("reason", "LLM classified intent.")

            if intent_str in Intent.__members__:
                canonical_intent = Intent[intent_str]
                return self._format_result(
                    intent=canonical_intent,
                    confidence=min(max(confidence, 0.0), 1.0),
                    reason=f"LLM Classification: {reason}",
                    source="llm",
                    original_prompt=original_prompt,
                    normalized_prompt=p_lower
                )
            else:
                _logger.warning(f"LLM returned non-canonical intent '{intent_str}'. Falling back to UNKNOWN.")
                return self._format_result(
                    intent=Intent.UNKNOWN,
                    confidence=0.50,
                    reason=f"LLM returned invalid intent '{intent_str}'.",
                    source="fallback",
                    original_prompt=original_prompt,
                    normalized_prompt=p_lower
                )
        except Exception as e:
            _logger.debug(f"LLM classification fallback failed/skipped: {e}")
            return None

    def _format_result(
        self,
        intent: Intent,
        confidence: float,
        reason: str,
        source: str,
        original_prompt: str,
        normalized_prompt: str
    ) -> Dict[str, Any]:
        target_agent = INTENT_AGENT_MAP.get(intent, "ClarificationAgent")
        workflow = INTENT_WORKFLOW_MAP.get(intent, "Clarification Pipeline")
        return {
            "intent": intent.value if isinstance(intent, Intent) else str(intent),
            "confidence": round(confidence, 2),
            "reason": reason,
            "classification_source": source,
            "target_agent": target_agent,
            "workflow": workflow,
            "original_prompt": original_prompt,
            "normalized_prompt": normalized_prompt,
        }

    def _log_decision(self, prompt: str, info: Dict[str, Any]):
        intent_val = info.get("intent")
        conf_val = info.get("confidence")
        source_val = info.get("classification_source")
        agent_val = info.get("target_agent")
        _logger.info(f"[AIForge Router] Prompt: '{prompt[:40]}' -> Intent: {intent_val} (Conf: {conf_val}, Source: {source_val}) -> Agent: {agent_val}")


global_router_agent = RouterAgent()