import logging

_logger = logging.getLogger("aiforge.performance")

# Default version pins for commonly detected pip packages to ensure valid dependency specs
BACKEND_VERSION_PINS = {
    "fastapi": "fastapi>=0.100.0",
    "uvicorn": "uvicorn>=0.22.0",
    "pydantic": "pydantic>=2.0.0",
    "python-dotenv": "python-dotenv>=1.0.0",
    "motor": "motor>=3.2.0",
    "pymongo": "pymongo>=4.5.0",
    "sqlalchemy": "sqlalchemy>=2.0.0",
    "psycopg2-binary": "psycopg2-binary>=2.9.6",
    "psycopg": "psycopg[binary]>=3.1.9",
    "mysql-connector-python": "mysql-connector-python>=8.0.33",
    "redis": "redis>=4.6.0",
    "requests": "requests>=2.31.0",
    "httpx": "httpx>=0.24.1",
    "pytest": "pytest>=7.4.0",
    "pyjwt": "pyjwt>=2.7.0",
    "python-jose": "python-jose[cryptography]>=3.3.0",
    "passlib": "passlib[bcrypt]>=1.7.4",
    "cryptography": "cryptography>=41.0.1",
    "anyio": "anyio>=3.7.1"
}


class RequirementsGenerator:
    """
    Programmatically builds and outputs requirements.txt contents with sorted,
    clean, and version-pinned packages.
    """

    def __init__(self) -> None:
        pass

    def generate_requirements(self, dependencies: list[str], extras: list[str] | None = None) -> str:
        """
        Builds, sorts, and pins python requirements with optional extra packages.
        """
        _logger.info("Generating requirements.txt dynamically...")

        cleaned_deps = set()

        # Add detected dependencies
        for dep in dependencies:
            dep_clean = dep.strip()
            if not dep_clean:
                continue
            
            # Map clean import package to pinned version
            # E.g. If it is already pydantic>=2.0.0, keep it. Otherwise resolve it.
            base_name = dep_clean.split(">")[0].split("<")[0].split("=")[0].strip().lower()
            pinned = BACKEND_VERSION_PINS.get(base_name, dep_clean)
            cleaned_deps.add(pinned)

        # Add optional extra packages
        if extras:
            for extra in extras:
                extra_clean = extra.strip()
                if extra_clean:
                    base_name = extra_clean.split(">")[0].split("<")[0].split("=")[0].strip().lower()
                    pinned = BACKEND_VERSION_PINS.get(base_name, extra_clean)
                    cleaned_deps.add(pinned)

        # Ensure base FastAPI requirements are always met
        base_fastapi = ["fastapi>=0.100.0", "uvicorn>=0.22.0", "pydantic>=2.0.0"]
        for base in base_fastapi:
            base_name = base.split(">")[0]
            if not any(d.startswith(base_name) for d in cleaned_deps):
                cleaned_deps.add(base)

        # Sort alphabetically
        sorted_requirements = sorted(list(cleaned_deps))

        formatted_reqs = "\n".join(sorted_requirements) + "\n"
        _logger.info("requirements.txt generated successfully")
        return formatted_reqs
