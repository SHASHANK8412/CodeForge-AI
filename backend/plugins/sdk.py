import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List

logger = logging.getLogger("aiforge.plugins.sdk")


class BasePlugin(ABC):
    """
    BasePlugin SDK interface for creating custom AIForge plugins and tools.
    """

    name: str = "base_plugin"
    version: str = "1.0.0"
    description: str = "Base plugin description"
    permissions: List[str] = []

    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Executes plugin logic and returns structured output dictionary."""
        pass


# Global Plugin SDK Export
__all__ = ["BasePlugin"]
