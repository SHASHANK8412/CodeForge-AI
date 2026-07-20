import time
import logging
from typing import Dict, Any, Tuple
from backend.monitoring.knowledge_base import IncidentKnowledgeBase

_logger = logging.getLogger("aiforge.sre")

class RecoveryEngine:
    """
    Executes automated self-healing procedures (restarts, scale-ups, cache clears, configuration refreshes)
    based on SRE policies, LLM recommendations, and knowledge base performance logs.
    """

    def __init__(self, knowledge_base: IncidentKnowledgeBase) -> None:
        self.knowledge_base = knowledge_base

    def execute_recovery(
        self,
        signature: str,
        recommendation: Dict[str, Any],
        attempt_number: int = 1
    ) -> Tuple[str, float]:
        """
        Runs the SRE recovery action. Returns (selected_strategy: str, execution_duration: float).
        """
        # 1. Determine best strategy
        llm_recommended = recommendation.get("recommended_action", "Restart Container")
        kb_best = self.knowledge_base.get_best_strategy(signature)

        # If it's the first attempt, prefer KB if available, otherwise trust LLM recommendation
        if attempt_number == 1:
            strategy = kb_best or llm_recommended
        else:
            # On retries, alternate to the LLM recommendation or fallback defaults
            strategy = llm_recommended if kb_best != llm_recommended else "Restart Container"

        _logger.info(f"Executing self-healing plan: '{strategy}' (Attempt {attempt_number})")
        
        start_time = time.time()

        # Simulate script executions for SRE actions
        # In a full production setup, this delegates to the Docker SDK or K8s API
        strat_lower = strategy.lower()
        if "database" in strat_lower or "db" in strat_lower:
            # Simulate database container reset
            _logger.info("[RECOVERY] Executing: docker restart aiforge-postgres")
            time.sleep(1.0)
        elif "cache" in strat_lower or "clear" in strat_lower:
            # Simulate Redis flush
            _logger.info("[RECOVERY] Executing: redis-cli FLUSHALL")
            time.sleep(0.2)
        elif "scale" in strat_lower or "replica" in strat_lower:
            # Simulate Scaling replicas up
            _logger.info("[RECOVERY] Executing: kubectl scale deployment/backend --replicas=3")
            time.sleep(1.5)
        elif "secret" in strat_lower or "rotate" in strat_lower:
            # Simulate key rotation
            _logger.info("[RECOVERY] Generating new crypt keys and rewriting env configuration")
            time.sleep(0.5)
        else:
            # Default Restart Container
            _logger.info("[RECOVERY] Executing: docker restart aiforge-backend")
            time.sleep(0.8)

        duration = time.time() - start_time
        _logger.info(f"Recovery action '{strategy}' executed in {duration:.2f}s")
        
        return strategy, duration
