import re
import logging
from dataclasses import dataclass, field

_logger = logging.getLogger("aiforge.performance")

# Common python standard libraries to exclude from requirements
PYTHON_STD_LIBS = {
    "abc", "argparse", "array", "asyncio", "base64", "collections", "contextlib",
    "contextvars", "csv", "datetime", "decimal", "enum", "functools", "hashlib",
    "html", "http", "io", "json", "logging", "math", "multiprocessing", "os",
    "pathlib", "pickle", "random", "re", "select", "shutil", "socket", "sqlite3",
    "ssl", "string", "struct", "subprocess", "sys", "tempfile", "threading",
    "time", "traceback", "types", "typing", "unittest", "urllib", "uuid", "weakref",
    "xml", "zipfile"
}

# Python packages mapping from import name to pip package name
PIP_MAPPING = {
    "motor": "motor",
    "pymongo": "pymongo",
    "sqlalchemy": "sqlalchemy",
    "psycopg2": "psycopg2-binary",
    "psycopg": "psycopg[binary]",
    "mysql": "mysql-connector-python",
    "aiomysql": "aiomysql",
    "asyncpg": "asyncpg",
    "redis": "redis",
    "jwt": "pyjwt",
    "jose": "python-jose[cryptography]",
    "passlib": "passlib[bcrypt]",
    "dotenv": "python-dotenv",
    "yaml": "pyyaml",
    "pandas": "pandas",
    "numpy": "numpy",
    "requests": "requests",
    "httpx": "httpx",
    "jinja2": "jinja2",
    "pytest": "pytest",
    "pydantic": "pydantic>=2.0.0",
}


@dataclass
class ProjectDependencies:
    frontend: list[str] = field(default_factory=list)
    backend: list[str] = field(default_factory=list)
    database: list[str] = field(default_factory=list)


class DependencyGenerator:
    """
    Analyzes generated source code to discover npm and pip packages, database engines,
    deduplicates and cleans the names, and groups them.
    """

    def __init__(self) -> None:
        pass

    def detect_dependencies(self, state: dict) -> ProjectDependencies:
        """
        Extract package dependencies by analyzing the generated frontend, backend,
        and database code blocks.
        """
        _logger.info("Detecting dependencies from generated code...")
        
        frontend_code = state.get("frontend", "")
        backend_code = state.get("backend", "")
        db_code = state.get("database", "")

        frontend_deps = self._parse_frontend_imports(frontend_code)
        backend_deps = self._parse_backend_imports(backend_code)
        db_deps = self._detect_db_drivers(db_code, backend_code)

        # Merge database drivers to backend dependencies as well
        for db_dep in db_deps:
            pip_name = PIP_MAPPING.get(db_dep, db_dep)
            if pip_name not in backend_deps:
                backend_deps.append(pip_name)

        # Sort all lists alphabetically
        frontend_deps.sort()
        backend_deps.sort()
        db_deps.sort()

        _logger.info(
            f"Dependency detection completed. Frontend: {frontend_deps}, "
            f"Backend: {backend_deps}, Database: {db_deps}"
        )

        return ProjectDependencies(
            frontend=frontend_deps,
            backend=backend_deps,
            database=db_deps
        )

    def _parse_frontend_imports(self, code: str) -> list[str]:
        """
        Heuristically parses import statements in React/JavaScript files.
        """
        deps = set()
        if not code:
            return list(deps)

        # Matches: import ... from 'package' or import "package" or require("package")
        import_pattern = re.compile(
            r"(?:import\s+(?:[a-zA-Z0-9_\*\s,\{\}]+from\s+)?['\"]([^'\".\/][^'\"]*)['\"]|"
            r"require\(['\"]([^'\".\/][^'\"]*)['\"]\))"
        )

        for match in import_pattern.finditer(code):
            pkg = match.group(1) or match.group(2)
            if pkg:
                # Strip specific subpaths (e.g. 'react-dom/client' -> 'react-dom')
                if pkg.startswith("@"):
                    # scoped packages have 2 path parts: @scope/name
                    parts = pkg.split("/")
                    if len(parts) >= 2:
                        pkg = f"{parts[0]}/{parts[1]}"
                else:
                    pkg = pkg.split("/")[0]
                
                # Exclude local imports and standard Node packages
                if pkg not in {"path", "fs", "os", "crypto", "child_process", "http"}:
                    deps.add(pkg)

        # Default packages if React structure is present
        if "react" in code.lower() or "export default" in code:
            deps.add("react")
            deps.add("react-dom")

        # React Router / Axios detection
        if "route" in code.lower() or "router" in code.lower():
            deps.add("react-router-dom")
        if "axios" in code.lower() or "api" in code.lower():
            deps.add("axios")
        if "tailwind" in code.lower() or "className=" in code:
            deps.add("tailwindcss")

        return list(deps)

    def _parse_backend_imports(self, code: str) -> list[str]:
        """
        Heuristically parses import statements in Python files.
        """
        deps = set()
        if not code:
            return list(deps)

        # Matches: import package, import package.submodule, from package import ...
        import_pattern = re.compile(
            r"^\s*(?:import\s+([a-zA-Z0-9_]+)|from\s+([a-zA-Z0-9_]+)\s+import)",
            re.MULTILINE
        )

        for match in import_pattern.finditer(code):
            pkg = match.group(1) or match.group(2)
            if pkg and pkg not in PYTHON_STD_LIBS:
                pip_name = PIP_MAPPING.get(pkg, pkg)
                deps.add(pip_name)

        # Default standard FastAPI dependencies if FastAPI imports are found
        if "fastapi" in code.lower() or "app = fastapi" in code.lower():
            deps.add("fastapi")
            deps.add("uvicorn")
            deps.add("pydantic>=2.0.0")

        if "dotenv" in code.lower() or "load_dotenv" in code.lower():
            deps.add("python-dotenv")

        return list(deps)

    def _detect_db_drivers(self, db_code: str, backend_code: str) -> list[str]:
        """
        Determines what database is being configured and returns corresponding driver packages.
        """
        drivers = set()
        combined = (db_code + "\n" + backend_code).lower()

        # Database Engine check
        if "mongodb" in combined or "mongo" in combined or "motor" in combined:
            drivers.add("mongodb")
            drivers.add("motor")
        if "postgresql" in combined or "postgres" in combined or "psycopg" in combined:
            drivers.add("postgresql")
            drivers.add("psycopg2")
        if "mysql" in combined or "pymysql" in combined:
            drivers.add("mysql")
        if "redis" in combined:
            drivers.add("redis")
        if "sqlite" in combined:
            drivers.add("sqlite")

        return list(drivers)
