import json
import logging
from typing import Any

_logger = logging.getLogger("aiforge.performance")

# Default version pins for commonly detected packages to ensure valid node packages
FRONTEND_VERSION_PINS = {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.14.2",
    "axios": "^1.4.0",
    "tailwindcss": "^3.3.3",
    "postcss": "^8.4.27",
    "autoprefixer": "^10.4.14",
    "lucide-react": "^0.263.0",
    "framer-motion": "^10.12.16",
    "recharts": "^2.7.2",
    "sass": "^1.63.6",
    "typescript": "^5.0.2"
}


class PackageGenerator:
    """
    Programmatically builds and outputs a valid package.json file for the frontend
    application using the detected dependencies.
    """

    def __init__(self) -> None:
        pass

    def generate_package_json(self, project_name: str, dependencies: list[str]) -> str:
        """
        Builds and returns package.json JSON string dynamically.
        """
        _logger.info("Generating package.json dynamically...")

        # Normalize project name for package.json validation rules
        normalized_name = "".join([c if c.isalnum() or c in "-_" else "-" for c in project_name]).lower()
        normalized_name = normalized_name.strip("-")

        # Programmatic dependencies building
        deps_dict: dict[str, str] = {}
        for dep in dependencies:
            version = FRONTEND_VERSION_PINS.get(dep.lower(), "latest")
            deps_dict[dep] = version

        # Ensure base React packages are present if not already detected
        if "react" not in deps_dict:
            deps_dict["react"] = FRONTEND_VERSION_PINS["react"]
        if "react-dom" not in deps_dict:
            deps_dict["react-dom"] = FRONTEND_VERSION_PINS["react-dom"]

        package_data: dict[str, Any] = {
            "name": normalized_name or "aiforge-frontend",
            "version": "1.0.0",
            "private": True,
            "scripts": {
                "dev": "vite",
                "build": "vite build",
                "lint": "eslint . --ext js,jsx --report-unused-disable-directives --max-warnings 0",
                "preview": "vite preview"
            },
            "dependencies": deps_dict,
            "devDependencies": {
                "@types/react": "^18.2.15",
                "@types/react-dom": "^18.2.7",
                "@vitejs/plugin-react": "^4.0.3",
                "eslint": "^8.45.0",
                "eslint-plugin-react": "^7.32.2",
                "eslint-plugin-react-hooks": "^4.6.0",
                "eslint-plugin-react-refresh": "^0.4.3",
                "vite": "^4.4.5"
            },
            "engines": {
                "node": ">=18.0.0"
            }
        }

        # If tailwindcss is present, include postcss and autoprefixer in devDependencies
        if "tailwindcss" in deps_dict:
            package_data["devDependencies"]["postcss"] = FRONTEND_VERSION_PINS["postcss"]
            package_data["devDependencies"]["autoprefixer"] = FRONTEND_VERSION_PINS["autoprefixer"]

        formatted_json = json.dumps(package_data, indent=4)
        _logger.info("package.json generated successfully")
        return formatted_json
