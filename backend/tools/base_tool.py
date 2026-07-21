from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseTool(ABC):
    """
    Abstract Base Tool class enforcing initialize, validate, execute,
    cleanup, and health check hooks.
    """

    def __init__(self, tool_name: str) -> None:
        self.tool_name = tool_name

    @abstractmethod
    def initialize(self) -> None:
        pass

    @abstractmethod
    def validate(self, **kwargs) -> bool:
        pass

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        pass

    @abstractmethod
    def cleanup(self) -> None:
        pass

    @abstractmethod
    def health_check(self) -> bool:
        pass

    def _format_result(self, success: bool, output: str, error: str = "",
                       execution_time: float = 0.0, exit_code: int = 0,
                       metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        return {
            "success": success,
            "output": output,
            "error": error,
            "execution_time": execution_time,
            "exit_code": exit_code,
            "tool_name": self.tool_name,
            "metadata": metadata or {}
        }
