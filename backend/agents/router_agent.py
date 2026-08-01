"""
AIForge Precision Intent Router Agent
======================================
Classifies incoming user prompts into 9 precise intent categories:
1. PROJECT_GENERATION
2. DSA_PROBLEM
3. CODE_GENERATION
4. DEBUGGING
5. EXPLANATION
6. DOCUMENTATION
7. RAG_QUERY
8. GENERAL_CHAT
9. AMBIGUOUS

Eliminates universal CodingAgent fallbacks. Arbitrary standalone topics/nouns like "Formula 1" or "Cricket"
are classified as AMBIGUOUS to ask clarifying questions instead of generating algorithms.
"""

import re
import logging
from typing import Dict, Any

_logger = logging.getLogger("aiforge.agents.router_agent")


class IntentCategory:
    PROJECT_GENERATION = "PROJECT_GENERATION"
    DSA_PROBLEM = "DSA_PROBLEM"
    CODE_GENERATION = "CODE_GENERATION"
    DEBUGGING = "DEBUGGING"
    EXPLANATION = "EXPLANATION"
    DOCUMENTATION = "DOCUMENTATION"
    RAG_QUERY = "RAG_QUERY"
    GENERAL_CHAT = "GENERAL_CHAT"
    AMBIGUOUS = "AMBIGUOUS"


class RouterAgent:
    """
    Precision prompt classification agent routing requests to specialized handlers.
    """

    def classify_intent(self, prompt: str) -> Dict[str, Any]:
        """
        Analyzes user prompt text and determines the optimal agent intent category.
        Prints decision trace:
        User Prompt -> Detected Intent -> Confidence -> Selected Workflow -> Selected Agent -> Reason
        """
        p_lower = prompt.strip().lower()
        words = p_lower.split()
        num_words = len(words)

        # 1. Standalone Single/Double Word Nouns without verbs -> AMBIGUOUS
        # (e.g., "Formula 1", "Cricket", "Hospital", "Netflix", "Python")
        common_topics = ["formula 1", "f1", "cricket", "hospital", "netflix", "spotify", "uber", "zomato", "swiggy", "amazon"]
        has_verbs = any(w in p_lower for w in ["develop", "build", "create", "generate", "make", "solve", "explain", "debug", "fix", "how", "what", "why", "write", "code"])

        if (num_words <= 2 and not has_verbs) or p_lower in common_topics:
            res = {
                "intent": IntentCategory.AMBIGUOUS,
                "confidence": 0.95,
                "workflow": "Clarification & Intent Disambiguation",
                "target_agent": "ClarificationAgent",
                "model": "qwen2.5-coder:latest",
                "reason": f"Standalone topic query '{prompt}' without explicit software creation, algorithm, or explanation instruction."
            }
            self._log_decision(prompt, res)
            return res

        # 2. DSA & Algorithmic Problem Keywords -> DSA_PROBLEM
        dsa_keywords = [
            "solve two sum", "leetcode", "two sum", "reverse linked list", "binary search tree",
            "merge sort", "quicksort algorithm", "heap sort", "graph bfs", "graph dfs", "dijkstra",
            "dynamic programming", "time complexity", "space complexity", "solve this array problem"
        ]
        if any(kw in p_lower for kw in dsa_keywords) or (("solve" in p_lower or "algorithm" in p_lower) and any(w in p_lower for w in ["array", "list", "tree", "graph", "dp", "problem"])):
            res = {
                "intent": IntentCategory.DSA_PROBLEM,
                "confidence": 0.98,
                "workflow": "Algorithmic Problem Solver Pipeline",
                "target_agent": "DSASolverAgent",
                "model": "qwen2.5-coder:latest",
                "reason": "Explicit algorithmic or LeetCode problem solving keywords identified."
            }
            self._log_decision(prompt, res)
            return res

        # 3. Explicit Software Project Generation -> PROJECT_GENERATION
        project_verbs = ["develop", "build", "create", "design", "make", "generate", "construct"]
        project_nouns = ["website", "app", "application", "platform", "system", "portal", "dashboard", "clone", "saas", "crm", "ecommerce", "e-commerce", "store", "tracker", "tool"]

        has_p_verb = any(v in p_lower for v in project_verbs)
        has_p_noun = any(n in p_lower for n in project_nouns)

        if (has_p_verb and has_p_noun) or any(phrase in p_lower for phrase in ["food delivery app", "netflix clone", "todo app", "spotify clone", "formula 1 website", "cricket website", "expense tracker"]):
            res = {
                "intent": IntentCategory.PROJECT_GENERATION,
                "confidence": 0.99,
                "workflow": "Autonomous Software Engineer Pipeline (RequirementAnalyzer -> Planner -> Architect -> Generator -> Reviewer -> Testing -> Exporter)",
                "target_agent": "AutonomousSoftwareEngineer",
                "model": "qwen2.5-coder:latest",
                "reason": "Explicit full-stack software creation instruction (verb + target project noun)."
            }
            self._log_decision(prompt, res)
            return res

        # 4. Debugging & Fixes -> DEBUGGING
        debugging_keywords = ["debug", "fix error", "fix python code", "why fails", "syntaxerror", "typeerror", "traceback", "crashing", "why is my", "fix this error"]
        if any(kw in p_lower for kw in debugging_keywords):
            res = {
                "intent": IntentCategory.DEBUGGING,
                "confidence": 0.96,
                "workflow": "AST Debugging & Exception Resolution Pipeline",
                "target_agent": "DebugAgent",
                "model": "qwen2.5-coder:latest",
                "reason": "Error diagnosis or code crash stack trace keywords identified."
            }
            self._log_decision(prompt, res)
            return res

        # 5. Concept & Code Explanations -> EXPLANATION
        if any(p_lower.startswith(kw) for kw in ["explain", "what is", "how does", "why is", "tell me about"]) or "explain code" in p_lower:
            res = {
                "intent": IntentCategory.EXPLANATION,
                "confidence": 0.95,
                "workflow": "Technical Concept Explanation Pipeline",
                "target_agent": "ExplanationAgent",
                "model": "qwen2.5-coder:latest",
                "reason": "Concept query or explanation request prefix detected."
            }
            self._log_decision(prompt, res)
            return res

        # 6. Snippet / Code Generation -> CODE_GENERATION
        code_gen_keywords = ["code for", "write code", "function to", "write a python script", "binary search implementation in python", "generate script"]
        if any(kw in p_lower for kw in code_gen_keywords) or (has_verbs and "in python" in p_lower):
            res = {
                "intent": IntentCategory.CODE_GENERATION,
                "confidence": 0.95,
                "workflow": "Isolated Snippet & Utility Generator Pipeline",
                "target_agent": "CodingAgent",
                "model": "qwen2.5-coder:latest",
                "reason": "Direct request for an isolated code snippet or utility script."
            }
            self._log_decision(prompt, res)
            return res

        # 7. Documentation Request -> DOCUMENTATION
        if any(kw in p_lower for kw in ["readme", "documentation", "docstring", "api docs"]):
            res = {
                "intent": IntentCategory.DOCUMENTATION,
                "confidence": 0.94,
                "workflow": "Technical Documentation Generator Pipeline",
                "target_agent": "DocumentationAgent",
                "model": "qwen2.5-coder:latest",
                "reason": "Documentation generation request detected."
            }
            self._log_decision(prompt, res)
            return res

        # 8. RAG Document Search -> RAG_QUERY
        if any(kw in p_lower for kw in ["summarize document", "query pdf", "rag search", "uploaded file"]):
            res = {
                "intent": IntentCategory.RAG_QUERY,
                "confidence": 0.96,
                "workflow": "Vector RAG Grounded Search Pipeline",
                "target_agent": "RAGAgent",
                "model": "qwen2.5-coder:latest",
                "reason": "Document RAG retrieval query detected."
            }
            self._log_decision(prompt, res)
            return res

        # 9. General Chat & Greetings -> GENERAL_CHAT
        greetings = ["hello", "hi", "hey", "who are you", "good morning", "good evening", "what can you do"]
        if any(p_lower.startswith(g) for g in greetings):
            res = {
                "intent": IntentCategory.GENERAL_CHAT,
                "confidence": 0.98,
                "workflow": "General AI Assistant Conversation",
                "target_agent": "ChatAgent",
                "model": "qwen2.5-coder:latest",
                "reason": "Conversational greeting or general assistant query."
            }
            self._log_decision(prompt, res)
            return res

        # Fallback: AMBIGUOUS (Zero universal CodingAgent fallback)
        res = {
            "intent": IntentCategory.AMBIGUOUS,
            "confidence": 0.80,
            "workflow": "Clarification & Intent Disambiguation",
            "target_agent": "ClarificationAgent",
            "model": "qwen2.5-coder:latest",
            "reason": "Prompt lacks clear verbs or intent signals; requesting clarification instead of defaulting to CodingAgent."
        }
        self._log_decision(prompt, res)
        return res

    def _log_decision(self, prompt: str, info: Dict[str, Any]):
        print(f"\n{"-"*75}")
        print(f" USER PROMPT:       '{prompt}'")
        print(f" DETECTED INTENT:   {info['intent']}")
        print(f" CONFIDENCE:        {info['confidence']}")
        print(f" SELECTED WORKFLOW: {info['workflow']}")
        print(f" SELECTED AGENT:    {info['target_agent']}")
        print(f" MODEL:             {info['model']}")
        print(f" REASON:            {info['reason']}")
        print(f"{"-"*75}\n")
        _logger.info(f"RouterAgent: Prompt '{prompt[:30]}' -> {info['intent']} (Conf: {info['confidence']})")


global_router_agent = RouterAgent()