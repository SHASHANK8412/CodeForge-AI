from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BasePlugin(ABC):
    """
    Abstract Base Class for all AIForge plugins.
    Ensures consistent lifecycle management and permission declarations.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        pass

    @property
    @abstractmethod
    def author(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    def homepage(self) -> str:
        return ""

    @property
    def license(self) -> str:
        return "MIT"

    @property
    def dependencies(self) -> List[str]:
        return []

    @property
    def permissions(self) -> List[str]:
        return []

    @property
    def capabilities(self) -> List[str]:
        return []

    @abstractmethod
    def initialize(self) -> None:
        pass

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def validate(self) -> bool:
        pass

    @abstractmethod
    def shutdown(self) -> None:
        pass

    def cleanup(self) -> None:
        pass

    def health_check(self) -> Dict[str, Any]:
        return {"status": "Healthy", "errors": []}

    def metrics(self) -> Dict[str, Any]:
        return {}

    def serialize(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "permissions": self.permissions,
            "dependencies": self.dependencies
        }

    def deserialize(self, data: Dict[str, Any]) -> None:
        pass

    def before_execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return context

    def after_execute(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def rollback(self, context: Dict[str, Any]) -> None:
        pass
