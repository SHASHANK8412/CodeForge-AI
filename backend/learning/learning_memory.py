import json
import logging
from pathlib import Path
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.learning")

class LearningMemory:
    """
    Manages persistence of historical project learning files.
    """

    def __init__(self, memory_dir: str = None) -> None:
        if memory_dir is None:
            memory_dir = str(Path(__file__).parent / "memory")
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)

    def save_project_summary(self, project_name: str, summary: Dict[str, Any]) -> str:
        """
        Saves a project summary JSON file.
        """
        # Sanitize filename
        safe_name = "".join(c for c in project_name if c.isalnum() or c in ("-", "_")).rstrip()
        file_path = self.memory_dir / f"{safe_name}.json"
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)
            _logger.info(f"Successfully saved project learning memory: {file_path.name}")
            return str(file_path)
        except Exception as e:
            _logger.error(f"Failed to write project learning memory JSON: {str(e)}")
            raise e

    def load_project_summary(self, project_name: str) -> Dict[str, Any] | None:
        """
        Loads a single project summary.
        """
        safe_name = "".join(c for c in project_name if c.isalnum() or c in ("-", "_")).rstrip()
        file_path = self.memory_dir / f"{safe_name}.json"
        
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            _logger.error(f"Failed to read project learning memory: {str(e)}")
            return None

    def get_all_summaries(self) -> List[Dict[str, Any]]:
        """
        Loads all project summaries from learning memory.
        """
        summaries: List[Dict[str, Any]] = []
        for file_path in self.memory_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    summaries.append(json.load(f))
            except Exception as e:
                _logger.error(f"Skipping corrupted summary file {file_path.name}: {str(e)}")
        return summaries
