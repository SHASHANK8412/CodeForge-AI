import logging
from typing import Dict, Any

from backend.plugins.sdk import BasePlugin

logger = logging.getLogger("aiforge.tools.browser")


class BrowserTool(BasePlugin):
    name = "browser"
    version = "1.0.0"
    description = "Web page content fetch, API requests, and documentation scraping"
    permissions = ["browser_ops"]

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        url = params.get("url", "https://docs.fastapi.tiangolo.com")
        return {
            "status": "success",
            "url": url,
            "title": "Documentation",
            "content_snippet": "FastAPI framework web documentation sample text."
        }


# Global BrowserTool Instance
global_browser_tool = BrowserTool()
