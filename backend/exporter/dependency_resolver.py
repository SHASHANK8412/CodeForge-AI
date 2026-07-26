import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger("aiforge.exporter.dependency_resolver")


class DependencyResolver:
    """
    DependencyResolver inspects generated Python and React source files,
    detecting required packages and producing requirements.txt and package.json manifests.
    """

    DEFAULT_PYTHON_DEPS = [
        "fastapi==0.110.0",
        "uvicorn==0.28.0",
        "pydantic==2.6.4",
        "sqlalchemy==2.0.28",
        "psycopg2-binary==2.9.9",
        "python-jose[cryptography]==3.3.0",
        "passlib[bcrypt]==1.7.4",
        "requests==2.31.0"
    ]

    DEFAULT_REACT_DEPS = {
        "react": "^18.2.0",
        "react-dom": "^18.2.0",
        "react-icons": "^5.0.1",
        "axios": "^1.6.8",
        "tailwindcss": "^3.4.1"
    }

    def generate_requirements_txt(self, backend_files: Dict[str, str]) -> str:
        """Generates requirements.txt content based on backend imports."""
        deps = set(self.DEFAULT_PYTHON_DEPS)

        full_code = "\n".join(backend_files.values())
        if "jwt" in full_code.lower() or "jose" in full_code.lower():
            deps.add("python-jose[cryptography]==3.3.0")
        if "bcrypt" in full_code.lower():
            deps.add("passlib[bcrypt]==1.7.4")
        if "stripe" in full_code.lower():
            deps.add("stripe==8.8.0")
        if "chromadb" in full_code.lower():
            deps.add("chromadb==0.4.24")

        return "\n".join(sorted(list(deps))) + "\n"

    def generate_package_json(self, project_name: str, frontend_files: Dict[str, str]) -> str:
        """Generates package.json for React frontend."""
        deps = dict(self.DEFAULT_REACT_DEPS)
        full_code = "\n".join(frontend_files.values())

        if "react-router" in full_code.lower():
            deps["react-router-dom"] = "^6.22.3"
        if "chart" in full_code.lower() or "recharts" in full_code.lower():
            deps["recharts"] = "^2.12.3"

        pkg_manifest = {
            "name": project_name.lower().replace(" ", "-"),
            "version": "1.0.0",
            "private": True,
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "vite build",
                "lint": "eslint . --ext js,jsx --report-unused-disable-directives --max-warnings 0",
                "preview": "vite preview"
            },
            "dependencies": deps,
            "devDependencies": {
                "@types/react": "^18.2.66",
                "@types/react-dom": "^18.2.22",
                "@vitejs/plugin-react": "^4.2.1",
                "autoprefixer": "^10.4.19",
                "postcss": "^8.4.38",
                "vite": "^5.2.0"
            }
        }
        return json.dumps(pkg_manifest, indent=2) + "\n"


# Global DependencyResolver Instance
global_dependency_resolver = DependencyResolver()
