import json
import logging
from pathlib import Path
from typing import Dict, List, Any

_logger = logging.getLogger("aiforge.sre")

class IncidentKnowledgeBase:
    """
    Manages persistent memory storing operational incidents, selected recovery plans,
    execution metrics, and outcome success logs.
    """

    def __init__(self, file_path: str = None) -> None:
        if file_path is None:
            # Default to monitoring folder path
            file_path = str(Path(__file__).parent / "incident_kb.json")
        self.file_path = Path(file_path)
        self.kb_data: List[Dict[str, Any]] = []
        self._load_kb()

    def _load_kb(self) -> None:
        try:
            if self.file_path.exists():
                with open(self.file_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        self.kb_data = json.loads(content)
                        return
            
            # Initial seed knowledge data
            self.kb_data = [
                {
                    "signature": "db_connection_failure",
                    "root_cause": "PostgreSQL offline",
                    "strategy": "Restart Database",
                    "success": True,
                    "duration_seconds": 12.5,
                    "confidence": 0.95
                },
                {
                    "signature": "high_cpu",
                    "root_cause": "Thread starvation",
                    "strategy": "Scale Replicas",
                    "success": True,
                    "duration_seconds": 25.0,
                    "confidence": 0.85
                },
                {
                    "signature": "redis_failure",
                    "root_cause": "Cache disconnect",
                    "strategy": "Clear Cache",
                    "success": True,
                    "duration_seconds": 3.0,
                    "confidence": 0.90
                }
            ]
            self._save_kb()
        except Exception as e:
            _logger.error(f"Failed to load incident knowledge base: {str(e)}")
            self.kb_data = []

    def _save_kb(self) -> None:
        try:
            # Ensure folder structure exists
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.kb_data, f, indent=2)
        except Exception as e:
            _logger.error(f"Failed to write SRE knowledge base JSON: {str(e)}")

    def add_record(
        self,
        signature: str,
        root_cause: str,
        strategy: str,
        success: bool,
        duration_seconds: float,
        confidence: float
    ) -> None:
        """
        Appends a recovery event record to persistent memory.
        """
        record = {
            "signature": signature,
            "root_cause": root_cause,
            "strategy": strategy,
            "success": success,
            "duration_seconds": duration_seconds,
            "confidence": confidence
        }
        self.kb_data.append(record)
        self._save_kb()

    def get_best_strategy(self, signature: str) -> str | None:
        """
        Returns the historical strategy with the highest success rate for a given signature.
        """
        matching = [r for r in self.kb_data if r.get("signature") == signature]
        if not matching:
            return None

        # Compute success rates per strategy type
        strategies_score: Dict[str, Dict[str, Any]] = {}
        for r in matching:
            strat = r["strategy"]
            if strat not in strategies_score:
                strategies_score[strat] = {"attempts": 0, "successes": 0}
            strategies_score[strat]["attempts"] += 1
            if r["success"]:
                strategies_score[strat]["successes"] += 1

        best_strat = None
        best_rate = -1.0

        for strat, stats in strategies_score.items():
            rate = stats["successes"] / stats["attempts"]
            if rate > best_rate:
                best_rate = rate
                best_strat = strat

        return best_strat

    def get_records(self) -> List[Dict[str, Any]]:
        return self.kb_data
