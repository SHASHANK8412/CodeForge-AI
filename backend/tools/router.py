import logging

_logger = logging.getLogger("aiforge.tools")

class ToolRouter:
    """
    Intelligent intent parser mapping query prompts to registered tool categories.
    """

    def __init__(self) -> None:
        pass

    def route_intent(self, prompt: str) -> str:
        p = prompt.lower().strip()

        if "git" in p or "commit" in p or "push" in p or "clone" in p:
            return "gittool"
        elif "pytest" in p or "pip" in p or "npm" in p or "terminal" in p:
            return "terminaltool"
        elif "docker" in p or "compose" in p:
            return "dockertool"
        elif "sql" in p or "select" in p or "insert" in p or "postgres" in p:
            return "postgrestool"
        elif "http" in p or "fetch" in p or "axios" in p:
            return "apitool"
        elif "url" in p or "browse" in p or "docs" in p:
            return "browsertool"
        elif "read" in p or "write" in p or "list" in p or "file" in p:
            return "filesystemtool"
        
        # Default fallback
        return "terminaltool"
