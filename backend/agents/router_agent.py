"""
AIForge Precision Intent Router Agent
======================================
Classifies incoming user prompts into precise intent categories (CODING, DEBUGGING, EXPLANATION, RESUME, PROJECT_GENERATION, RAG)
to guarantee that project prompts like 'Develop Formula 1 Website' route to the multi-agent project pipeline instead of CodingAgent.
"""

import re
import logging
from typing import Dict, Any

_logger = logging.getLogger("aiforge.agents.router_agent")


class IntentCategory:
    CODING = "CODING"
    DEBUGGING = "DEBUGGING"
    EXPLANATION = "EXPLANATION"
    RESUME = "RESUME"
    PROJECT_GENERATION = "PROJECT_GENERATION"
    RAG = "RAG"


class RouterAgent:
    """
    Precision prompt classification agent routing requests to specialized handlers.
    """

    def classify_intent(self, prompt: str) -> Dict[str, Any]:
        """
        Analyzes user prompt text and determines the optimal agent intent category.
        """
        p_lower = prompt.lower().strip()
        words = p_lower.split()

        # 1. Resume Keywords -> Resume Agent
        resume_keywords = ["resume", "cv", "resume review", "resume analyzer", "career summary"]
        if any(kw in p_lower for kw in resume_keywords):
            _logger.info(f"RouterAgent: Prompt '{prompt[:30]}...' -> Classified as RESUME")
            return {"intent": IntentCategory.RESUME, "confidence": 0.98, "target_agent": "ResumeAgent"}

        # 2. RAG Document Grounding Keywords -> RAG Agent
        rag_keywords = ["summarize document", "query pdf", "rag search", "grounded search", "from uploaded file"]
        if any(kw in p_lower for kw in rag_keywords):
            _logger.info(f"RouterAgent: Prompt '{prompt[:30]}...' -> Classified as RAG")
            return {"intent": IntentCategory.RAG, "confidence": 0.96, "target_agent": "RAGAgent"}

        # 3. Debugging Keywords -> Debug Agent
        debugging_keywords = ["debug", "fix error", "fix python code", "why fails", "syntaxerror", "typeerror", "traceback", "fix this error"]
        if any(kw in p_lower for kw in debugging_keywords):
            _logger.info(f"RouterAgent: Prompt '{prompt[:30]}...' -> Classified as DEBUGGING")
            return {"intent": IntentCategory.DEBUGGING, "confidence": 0.96, "target_agent": "DebugAgent"}

        # 4. Code Explanation Keywords -> Explanation Agent
        if any(p_lower.startswith(kw) for kw in ["explain", "what is", "how does", "why is", "tell me about"]) or "explain code" in p_lower:
            _logger.info(f"RouterAgent: Prompt '{prompt[:30]}...' -> Classified as EXPLANATION")
            return {"intent": IntentCategory.EXPLANATION, "confidence": 0.95, "target_agent": "ExplanationAgent"}

        # 5. Explicit Coding / DSA / Algorithm Keywords -> Coding Agent
        coding_keywords = [
            "binary search", "linked list", "insertion", "linked list insertion", "reverse linked list",
            "merge sort", "quick sort", "quicksort", "bubble sort", "heap sort", "dsa", "leetcode",
            "algorithm", "code for", "write code", "function to", "dfs", "bfs", "dijkstra", "two sum",
            "fibonacci", "array reversal", "stack implementation", "queue implementation"
        ]
        has_coding_keyword = any(kw in p_lower for kw in coding_keywords)

        # 6. Project Generation Verbs & Nouns -> Project Pipeline
        project_verbs = ["develop", "build", "create", "design", "make", "generate", "construct"]
        project_nouns = ["website", "app", "application", "platform", "system", "portal", "dashboard", "clone", "saas", "crm", "ecommerce", "e-commerce", "full-stack", "fullstack", "service", "tool"]

        has_project_verb = any(v in words or f"{v} " in p_lower for v in project_verbs)
        has_project_noun = any(n in p_lower for n in project_nouns)

        if (has_project_verb and has_project_noun) or (has_project_noun and not has_coding_keyword) or any(phrase in p_lower for phrase in ["food delivery", "netflix clone", "todo app", "spotify clone", "formula 1 website", "f1 website"]):
            _logger.info(f"RouterAgent: Prompt '{prompt[:30]}...' -> Classified as PROJECT_GENERATION")
            return {"intent": IntentCategory.PROJECT_GENERATION, "confidence": 0.98, "target_agent": "LangGraph_MultiAgent_Pipeline"}

        if has_coding_keyword:
            _logger.info(f"RouterAgent: Prompt '{prompt[:30]}...' -> Classified as CODING")
            return {"intent": IntentCategory.CODING, "confidence": 0.97, "target_agent": "CodingAgent"}

        # Default fallback: If project nouns/verbs present, default to PROJECT_GENERATION; else CODING
        if has_project_verb or has_project_noun:
            return {"intent": IntentCategory.PROJECT_GENERATION, "confidence": 0.85, "target_agent": "LangGraph_MultiAgent_Pipeline"}

        return {"intent": IntentCategory.CODING, "confidence": 0.75, "target_agent": "CodingAgent"}


global_router_agent = RouterAgent()