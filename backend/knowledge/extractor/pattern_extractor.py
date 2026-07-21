import re
import logging
from pathlib import Path
from typing import List

_logger = logging.getLogger("aiforge.knowledge")

class PatternExtractor:
    """
    Identifies reusable patterns (Repository, JWT authentication, CORS middleware, CRUD) inside codebase.
    """

    def __init__(self) -> None:
        pass

    def extract_patterns(self, workspace_path: str) -> List[str]:
        """
        Parses python files looking for specific architectural pattern names.
        """
        root = Path(workspace_path)
        patterns = []

        # Indicators mapping regex
        indicators = {
            "JWT Authentication": re.compile(r'(jwt|decode_token|encode_token|oauth)', re.IGNORECASE),
            "Repository Pattern": re.compile(r'(Repository|dao|data_access)', re.IGNORECASE),
            "CRUD Template": re.compile(r'(create_|get_|update_|delete_)', re.IGNORECASE),
            "Middleware Filter": re.compile(r'(Middleware|BaseHTTPMiddleware)', re.IGNORECASE),
            "Rate Limiting": re.compile(r'(limiter|rate_limit|rate_limiting)', re.IGNORECASE)
        }

        # Scan python codes
        aggregated_code = ""
        for file_path in root.glob("backend/**/*.py"):
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    aggregated_code += f.read() + "\n"
            except Exception:
                pass

        for name, regex in indicators.items():
            if regex.search(aggregated_code):
                patterns.append(name)

        if not patterns:
            patterns = ["Standard MVC Structure"]

        return patterns
