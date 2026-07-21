import json
import logging
from pathlib import Path
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.debate")

class DebateMemory:
    """
    Stores and reuses debate sessions to prevent duplicate LLM reasoning.
    """

    def __init__(self, memory_dir: str = None) -> None:
        if memory_dir is None:
            memory_dir = str(Path(__file__).resolve().parent.parent / "memory" / "debates")
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)

    def save_debate(self, project_name: str, debate_session: Dict[str, Any]) -> str:
        """
        Saves a completed debate session summary JSON.
        """
        # Normalize name for filename safety
        safe_name = "".join(c for c in project_name if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "_")
        file_path = self.memory_dir / f"{safe_name}.json"
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(debate_session, f, indent=2)
            _logger.info(f"Successfully saved SRE debate memory: {file_path.name}")
            return str(file_path)
        except Exception as e:
            _logger.error(f"Failed to save SRE debate memory: {str(e)}")
            return ""

    def lookup_similar_debate(self, prompt: str) -> Dict[str, Any]:
        """
        Performs basic keyword matching lookup over past debate summaries.
        """
        keywords = set(prompt.lower().split())
        best_match: Dict[str, Any] = {}
        best_score = 0

        for file_path in self.memory_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Check match overlap on project details or stack
                past_prompt = data.get("prompt", "").lower()
                past_keywords = set(past_prompt.split())
                overlap = len(keywords.intersection(past_keywords))

                if overlap > best_score and overlap >= 2:
                    best_score = overlap
                    best_match = data
            except Exception as e:
                _logger.error(f"Failed to read SRE debate file during lookup: {str(e)}")

        if best_match:
            _logger.info(f"Reusing cached debate solution from: {best_match.get('project_name', 'Cached Session')}")
        return best_match
