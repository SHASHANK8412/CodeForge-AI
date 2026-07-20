import logging

_logger = logging.getLogger("aiforge.performance")

class NetlifyGenerator:
    """
    Generates netlify.toml layout for SPA React/Vue deployments,
    auto-configuring publishing folders, build pipelines, and routing proxies.
    """

    def __init__(self) -> None:
        pass

    def generate_config(self, framework: str = "react") -> str:
        """
        Creates netlify.toml structure.
        """
        _logger.info(f"Generating netlify.toml configuration for framework: {framework}")
        
        publish_dir = "dist"
        build_cmd = "npm run build"
        
        if framework.lower() == "nextjs":
            publish_dir = ".next"
            build_cmd = "npm run build"

        return f"""# Netlify Deployment Configuration
[build]
  command = "{build_cmd}"
  publish = "{publish_dir}"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
  force = false

[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options = "DENY"
    X-XSS-Protection = "1; mode=block"
    X-Content-Type-Options = "nosniff"
"""
