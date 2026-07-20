import logging

_logger = logging.getLogger("aiforge.performance")

class VercelGenerator:
    """
    Generates vercel.json configuration for Vercel, handling routing, static serving,
    rewrites, and SPA redirections.
    """

    def __init__(self) -> None:
        pass

    def generate_config(self, app_name: str, has_backend: bool = True) -> str:
        """
        Creates vercel.json structure.
        """
        _logger.info(f"Generating vercel.json configuration for: {app_name}")
        
        rewrites = ""
        if has_backend:
            # Proxy /api requests to Serverless Functions or Render Backend URL
            rewrites = """,
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "https://api.aiforge.local/api/$1"
    }
  ]"""

        return f"""{{
  "version": 2,
  "name": "{app_name}-frontend",
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "cleanUrls": true,
  "routes": [
    {{
      "handle": "filesystem"
    }},
    {{
      "src": "/(.*)",
      "dest": "/index.html"
    }}
  ]{rewrites}
}}
"""
