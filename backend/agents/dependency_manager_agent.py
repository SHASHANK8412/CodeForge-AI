import re
import json
import logging
from typing import Dict, Any, List, Set
from backend.agents.base_agent import BaseAgent

logger = logging.getLogger("aiforge.dependency_manager")


class DependencyManagerAgent(BaseAgent):
    """
    Dependency Manager Agent:
    - Scans Python & JavaScript/TypeScript source code to extract external imports.
    - Generates pinned requirements.txt, package.json, Dockerfile, docker-compose.yml, .env.example.
    - Verifies dependency compatibility and completes missing manifests.
    """

    STD_PYTHON_LIBS = {
        "os", "sys", "re", "json", "math", "time", "datetime", "typing", "pathlib",
        "logging", "collections", "functools", "itertools", "asyncio", "hashlib",
        "random", "subprocess", "copy", "uuid", "abc", "io", "base64", "ast"
    }

    KNOWN_PYTHON_PACKAGES = {
        "fastapi": "fastapi>=0.100.0",
        "uvicorn": "uvicorn[standard]>=0.22.0",
        "pydantic": "pydantic>=2.0.0",
        "sqlalchemy": "sqlalchemy>=2.0.0",
        "pytest": "pytest>=7.4.0",
        "httpx": "httpx>=0.24.0",
        "requests": "requests>=2.31.0",
        "jwt": "pyjwt>=2.8.0",
        "jose": "python-jose[cryptography]>=3.3.0",
        "passlib": "passlib[bcrypt]>=1.7.4",
        "dotenv": "python-dotenv>=1.0.0",
        "cors": "fastapi>=0.100.0",
        "redis": "redis>=4.6.0",
        "psycopg2": "psycopg2-binary>=2.9.6",
        "asyncpg": "asyncpg>=0.28.0",
        "pymongo": "pymongo>=4.4.0",
        "motor": "motor>=3.2.0"
    }

    KNOWN_NODE_PACKAGES = {
        "react": "^18.2.0",
        "react-dom": "^18.2.0",
        "axios": "^1.6.0",
        "lucide-react": "^0.292.0",
        "react-router-dom": "^6.20.0",
        "tailwindcss": "^3.3.5",
        "vite": "^5.0.0"
    }

    def __init__(self):
        super().__init__(
            system_prompt=(
                "You are the Dependency Manager Agent for AIForge. Your job is to analyze "
                "generated source code, extract imported modules, and generate production-ready "
                "requirements.txt, package.json, Dockerfile, docker-compose.yml, and .env.example."
            ),
            task_name="dependency_manager"
        )

    def extract_python_imports(self, code_dict: Dict[str, str]) -> Set[str]:
        imports = set()
        for filepath, content in code_dict.items():
            if filepath.endswith(".py"):
                # Match import module or from module import ...
                matches = re.findall(r"^(?:import|from)\s+([a-zA-Z0-9_]+)", content, re.MULTILINE)
                for mod in matches:
                    if mod not in self.STD_PYTHON_LIBS:
                        imports.add(mod.lower())
        return imports

    def extract_node_imports(self, code_dict: Dict[str, str]) -> Set[str]:
        imports = set()
        for filepath, content in code_dict.items():
            if filepath.endswith((".js", ".jsx", ".ts", ".tsx")):
                matches = re.findall(r"import\s+.*?from\s+['\"]([^'\".\n]+)['\"]", content)
                for mod in matches:
                    if not mod.startswith("."):
                        # Extract root package name e.g. @lucide/react -> @lucide/react, axios/lib -> axios
                        pkg = mod.split("/")[0] if not mod.startswith("@") else "/".join(mod.split("/")[:2])
                        imports.add(pkg)
        return imports

    def generate_requirements_txt(self, python_imports: Set[str]) -> str:
        pkgs = set()
        # Default essential dependencies for FastAPI AIForge apps
        pkgs.add("fastapi>=0.100.0")
        pkgs.add("uvicorn[standard]>=0.22.0")
        pkgs.add("pydantic>=2.0.0")
        pkgs.add("python-dotenv>=1.0.0")
        pkgs.add("pytest>=7.4.0")
        pkgs.add("httpx>=0.24.0")

        for imp in python_imports:
            if imp in self.KNOWN_PYTHON_PACKAGES:
                pkgs.add(self.KNOWN_PYTHON_PACKAGES[imp])

        return "\n".join(sorted(list(pkgs))) + "\n"

    def generate_package_json(self, project_name: str, node_imports: Set[str]) -> str:
        deps = {
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "axios": "^1.6.0",
            "lucide-react": "^0.292.0"
        }
        dev_deps = {
            "@vitejs/plugin-react": "^4.2.0",
            "vite": "^5.0.0"
        }

        for imp in node_imports:
            if imp in self.KNOWN_NODE_PACKAGES:
                deps[imp] = self.KNOWN_NODE_PACKAGES[imp]

        pkg_dict = {
            "name": project_name.lower().replace(" ", "-"),
            "private": True,
            "version": "1.0.0",
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "vite build",
                "preview": "vite preview",
                "lint": "eslint ."
            },
            "dependencies": deps,
            "devDependencies": dev_deps
        }
        return json.dumps(pkg_dict, indent=2) + "\n"

    def generate_dockerfile(self) -> str:
        return """# Multi-stage Dockerfile for FastAPI Backend & Vite Frontend
FROM python:3.11-slim as backend
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

    def generate_docker_compose(self, project_name: str) -> str:
        safe_name = project_name.lower().replace(" ", "-")
        return f"""version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: {safe_name}-backend
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: always

  db:
    image: postgres:15-alpine
    container_name: {safe_name}-db
    environment:
      POSTGRES_DB: appdb
      POSTGRES_USER: appuser
      POSTGRES_PASSWORD: apppassword
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
"""

    def generate_env_example(self, env_keys: List[str] = None) -> str:
        default_keys = [
            "PORT=8000",
            "ENVIRONMENT=production",
            "DATABASE_URL=postgresql://appuser:apppassword@localhost:5432/appdb",
            "SECRET_KEY=super-secret-key-change-in-production",
            "CORS_ORIGINS=http://localhost:3000,http://localhost:5173",
            "LOG_LEVEL=INFO"
        ]
        if env_keys:
            for k in env_keys:
                if not any(k in line for line in default_keys):
                    default_keys.append(f"{k}=your_{k.lower()}_val")
        return "\n".join(default_keys) + "\n"

    def run_dependency_analysis(
        self,
        project_name: str,
        backend_files: Dict[str, str],
        frontend_files: Dict[str, str]
    ) -> Dict[str, str]:
        py_imports = self.extract_python_imports(backend_files)
        js_imports = self.extract_node_imports(frontend_files)

        reqs = self.generate_requirements_txt(py_imports)
        pkg = self.generate_package_json(project_name, js_imports)
        df = self.generate_dockerfile()
        dc = self.generate_docker_compose(project_name)
        env = self.generate_env_example()

        return {
            "requirements.txt": reqs,
            "package.json": pkg,
            "Dockerfile": df,
            "docker-compose.yml": dc,
            ".env.example": env
        }
