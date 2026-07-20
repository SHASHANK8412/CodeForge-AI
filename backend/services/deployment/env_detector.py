import re
import logging
from typing import Dict, Set

_logger = logging.getLogger("aiforge.performance")

# Common keys to document with helpful default descriptions
ENV_DESCRIPTIONS = {
    "DATABASE_URL": "Connection string for the primary database (e.g., postgresql://user:pass@host:port/db)",
    "JWT_SECRET": "Cryptographic key for signing JWT tokens",
    "SECRET_KEY": "Application secret key for security signatures and sessions",
    "OPENAI_API_KEY": "OpenAI API Credential Key",
    "GOOGLE_API_KEY": "Google Gemini API Credential Key",
    "REDIS_URL": "Redis cache/message broker connection URL (e.g., redis://localhost:6379)",
    "SUPABASE_URL": "Supabase project API endpoint URL",
    "SUPABASE_KEY": "Supabase client API keys credential",
    "PORT": "Application port to bind the server to (default: 8000)",
    "OLLAMA_MODEL": "Default model tag to run in Ollama service local model list",
}

class EnvDetector:
    """
    Scans generated frontend and backend code files to discover required environment variables
    and generates custom documented .env.example files.
    """

    def __init__(self) -> None:
        # Regexes for common env pattern lookups
        # Matches: os.environ.get("KEY"), os.getenv("KEY"), os.environ["KEY"], process.env.KEY
        self.patterns = [
            re.compile(r"os\.environ\.get\(\s*['\"]([A-Z0-9_]+)['\"]\s*[\),]"),
            re.compile(r"os\.getenv\(\s*['\"]([A-Z0-9_]+)['\"]\s*[\),]"),
            re.compile(r"os\.environ\s*\[\s*['\"]([A-Z0-9_]+)['\"]\s*\]"),
            re.compile(r"process\.env\.([A-Z0-9_]+)"),
            re.compile(r"process\.env\[\s*['\"]([A-Z0-9_]+)['\"]\s*\]"),
        ]

    def detect_variables(self, code_contents: str) -> Dict[str, str]:
        """
        Scans code content and returns a dictionary of unique environment variables to their descriptions.
        """
        detected: Set[str] = set()
        for pattern in self.patterns:
            for match in pattern.finditer(code_contents):
                detected.add(match.group(1))

        # Build documented response mapping
        variables_map = {}
        for var in sorted(detected):
            variables_map[var] = ENV_DESCRIPTIONS.get(var, f"Custom variable required by the application context")

        return variables_map

    def generate_env_example(self, variables_map: Dict[str, str]) -> str:
        """
        Compiles variables and descriptions into a ready-to-write .env.example format.
        """
        _logger.info("Compiling .env.example configuration...")
        lines = [
            "# ==========================================================================",
            "# AIForge Generated Environment Configurations Example Template",
            "# Copy this file to .env and fill in active production credentials",
            "# ==========================================================================\n"
        ]

        if not variables_map:
            # Fallback basics if no custom variables were discovered
            variables_map = {
                "PORT": "Application server port mapping binding constraint",
                "DATABASE_URL": "Primary storage persistence engine connection string"
            }

        for var, desc in sorted(variables_map.items()):
            lines.append(f"# {desc}")
            lines.append(f"{var}=")
            lines.append("")

        return "\n".join(lines)
