import logging
from typing import Dict, Any, List
from .base_tool import BaseTool

_logger = logging.getLogger("aiforge.tools")

class ToolRegistry:
    """
    Autodiscovery registry tracking all active system tools.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        name = tool.tool_name.lower().strip()
        self._tools[name] = tool
        tool.initialize()
        _logger.info(f"Registered SRE tool: {tool.tool_name}")

    def unregister(self, name: str) -> None:
        key = name.lower().strip()
        if key in self._tools:
            del self._tools[key]
            _logger.info(f"Unregistered SRE tool: {name}")

    def get_tool(self, name: str) -> BaseTool:
        key = name.lower().strip()
        return self._tools.get(key)

    def list_tools(self) -> List[str]:
        return list(self._tools.keys())

    def execute_tool(self, name: str, **kwargs) -> Dict[str, Any]:
        tool = self.get_tool(name)
        if not tool:
            return {
                "success": False,
                "output": "",
                "error": f"Tool '{name}' is not registered in the system.",
                "execution_time": 0.0,
                "exit_code": -404,
                "tool_name": name,
                "metadata": {}
            }
        return tool.execute(**kwargs)
