import logging
from typing import Dict, Any

from .registry import ToolRegistry
from .router import ToolRouter
from .terminal_tool import TerminalTool
from .filesystem_tool import FilesystemTool
from .git_tool import GitTool
from .docker_tool import DockerTool
from .postgres_tool import PostgresTool
from .api_tool import ApiTool
from .browser_tool import BrowserTool

_logger = logging.getLogger("aiforge.tools")

class ToolAgent:
    """
    Main Tool Agent worker coordinating registry actions, safe execution rules, and self-healing.
    """

    def __init__(self) -> None:
        self.registry = ToolRegistry()
        self.router = ToolRouter()
        self._bootstrap_tools()

    def _bootstrap_tools(self) -> None:
        self.registry.register(TerminalTool())
        self.registry.register(FilesystemTool())
        self.registry.register(GitTool())
        self.registry.register(DockerTool())
        self.registry.register(PostgresTool())
        self.registry.register(ApiTool())
        self.registry.register(BrowserTool())

    def handle_request(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Routes and executes the appropriate tool based on developer input prompt.
        """
        tool_name = self.router.route_intent(prompt)
        _logger.info(f"Tool Agent routing intent '{prompt}' -> {tool_name}")
        
        # Execute tool
        res = self.registry.execute_tool(tool_name, **kwargs)
        
        # Self-healing logic for failures
        if not res["success"] and kwargs.get("retry_count", 0) < 3:
            _logger.warning(f"Execution failed. Attempting self-healing retry logic...")
            # Simulate a quick self-healing patch lookup
            kwargs["retry_count"] = kwargs.get("retry_count", 0) + 1
            res = self.registry.execute_tool(tool_name, **kwargs)

        return res
