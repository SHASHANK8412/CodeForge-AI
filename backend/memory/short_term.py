import logging
from typing import Dict, Any, List, Optional
from backend.memory.models import DecisionRecord

logger = logging.getLogger("aiforge.memory.short_term")


class ShortTermMemory:
    """
    ShortTermMemory holds transient workflow state for an active generation task.
    Lifespan: Single generation execution session.
    """

    def __init__(self):
        self._store: Dict[str, Any] = {}
        self._agent_outputs: Dict[str, Any] = {}
        self._files: Dict[str, str] = {}
        self._errors: List[Dict[str, Any]] = []
        self._test_results: Dict[str, Any] = {}
        self._decisions: List[Dict[str, Any]] = []
        self._generation_id: Optional[str] = None
        self._project_id: Optional[str] = None

    def initialize_session(self, project_id: str, generation_id: str) -> None:
        self.clear()
        self._project_id = project_id
        self._generation_id = generation_id

    def set(self, key: str, value: Any) -> None:
        self._store[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._store.get(key, default)

    def set_agent_output(self, agent_name: str, output: Any) -> None:
        self._agent_outputs[agent_name] = output

    def get_agent_output(self, agent_name: str) -> Any:
        return self._agent_outputs.get(agent_name)

    def set_file(self, filename: str, content: str) -> None:
        self._files[filename] = content

    def get_files(self) -> Dict[str, str]:
        return dict(self._files)

    def add_error(self, agent: str, error: str) -> None:
        self._errors.append({"agent": agent, "error": error})

    def get_errors(self) -> List[Dict[str, Any]]:
        return list(self._errors)

    def set_test_results(self, results: Dict[str, Any]) -> None:
        self._test_results = results

    def get_test_results(self) -> Dict[str, Any]:
        return dict(self._test_results)

    def add_decision(self, decision: Dict[str, Any]) -> None:
        self._decisions.append(decision)

    def get_decisions(self) -> List[Dict[str, Any]]:
        return list(self._decisions)

    def get_all(self) -> Dict[str, Any]:
        return {
            "project_id": self._project_id,
            "generation_id": self._generation_id,
            "store": dict(self._store),
            "agent_outputs": dict(self._agent_outputs),
            "files": dict(self._files),
            "errors": list(self._errors),
            "test_results": dict(self._test_results),
            "decisions": list(self._decisions),
        }

    def clear(self) -> None:
        self._store.clear()
        self._agent_outputs.clear()
        self._files.clear()
        self._errors.clear()
        self._test_results.clear()
        self._decisions.clear()
        self._generation_id = None
        self._project_id = None


# Global ShortTermMemory instance
global_short_term_memory = ShortTermMemory()
