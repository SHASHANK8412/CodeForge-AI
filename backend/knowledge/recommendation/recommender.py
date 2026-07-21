import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.knowledge")

class Recommender:
    """
    Ranks stack configurations based on previous SRE experience.
    """

    def __init__(self) -> None:
        pass

    def recommend_architecture(self, prompt: str) -> Dict[str, Any]:
        """
        Selects best-suited database, auth, and APIs configurations based on prompt indicators.
        """
        prompt_lower = prompt.lower()
        
        recommendations = []
        reasoning = []

        # 1. AI check
        if any(w in prompt_lower for w in ["ai", "chatbot", "rag", "ollama", "llm"]):
            recommendations.append("FastAPI + Ollama (Qwen2.5-Coder) + RAG")
            reasoning.append("Chat/AI queries maps well to FastAPI async routing with local Ollama inference.")

        # 2. Database check
        if any(w in prompt_lower for w in ["banking", "finance", "payment", "transaction"]):
            recommendations.append("PostgreSQL")
            reasoning.append("Financial systems require ACID-compliant transactional consistency models.")
        else:
            recommendations.append("SQLite")
            reasoning.append("Default SQLite database handles local file layouts with zero Operational overhead.")

        # 3. Auth check
        if any(w in prompt_lower for w in ["auth", "login", "users", "admin", "secure"]):
            recommendations.append("JWT Stateless Authentication")
            reasoning.append("JWT cookies verify admin interfaces stateless boundaries cleanly.")

        # 4. Real-time check
        if "real-time" in prompt_lower or "chat" in prompt_lower:
            recommendations.append("WebSockets")
            reasoning.append("Bi-directional real-time communication needs WebSockets handles.")

        # Fallback default backend
        if not recommendations:
            recommendations.extend(["FastAPI", "React", "Docker"])
            reasoning.append("Default stack selection (FastAPI + React + Docker) maximizes code modularity.")

        return {
            "recommended_stack": recommendations,
            "reasoning": reasoning
        }
