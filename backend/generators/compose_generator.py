import logging

_logger = logging.getLogger("aiforge.performance")

DB_SERVICE_TEMPLATES = {
    "postgresql": """  database:
    image: postgres:15-alpine
    container_name: database_container
    environment:
      POSTGRES_USER: app_user
      POSTGRES_PASSWORD: secure_password
      POSTGRES_DB: app_database
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    networks:
      - app-network""",

    "mongodb": """  database:
    image: mongo:6.0
    container_name: database_container
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: secure_password
      MONGO_INITDB_DATABASE: app_database
    ports:
      - "27017:27017"
    volumes:
      - mongodata:/data/db
    networks:
      - app-network""",

    "mysql": """  database:
    image: mysql:8.0
    container_name: database_container
    environment:
      MYSQL_ROOT_PASSWORD: root_password
      MYSQL_DATABASE: app_database
      MYSQL_USER: app_user
      MYSQL_PASSWORD: secure_password
    ports:
      - "3306:3306"
    volumes:
      - mysqldata:/var/lib/mysql
    networks:
      - app-network""",

    "redis": """  cache:
    image: redis:7-alpine
    container_name: cache_container
    ports:
      - "6379:6379"
    volumes:
      - redisdata:/data
    networks:
      - app-network"""
}


class ComposeGenerator:
    """
    Programmatically structures and outputs a production-ready docker-compose.yml
    that connects Frontend, Backend, and Database configurations.
    """

    def __init__(self) -> None:
        pass

    def generate_compose(self, db_engines: list[str]) -> str:
        """
        Dynamically designs docker-compose orchestration containing services based
        on active database requirements.
        """
        _logger.info("Generating docker-compose.yml dynamically...")

        # Base header
        compose_lines = [
            "version: '3.8'",
            "",
            "services:",
            "  backend:",
            "    build:",
            "      context: ./backend",
            "      dockerfile: Dockerfile",
            "    container_name: backend_container",
            "    ports:",
            "      - \"8000:8000\"",
            "    environment:",
            "      - PORT=8000",
            "      - DATABASE_URL=${DATABASE_URL:-mongodb://admin:secure_password@database:27017/app_database?authSource=admin}",
            "    depends_on:",
            "      - database",
            "    networks:",
            "      - app-network",
            "",
            "  frontend:",
            "    build:",
            "      context: ./frontend",
            "      dockerfile: Dockerfile",
            "    container_name: frontend_container",
            "    ports:",
            "      - \"80:80\"",
            "    depends_on:",
            "      - backend",
            "    networks:",
            "      - app-network",
            ""
        ]

        # Add Database services
        db_type = "mongodb"  # default database
        has_redis = False

        for engine in db_engines:
            engine_clean = engine.lower()
            if engine_clean in DB_SERVICE_TEMPLATES:
                if engine_clean == "redis":
                    has_redis = True
                else:
                    db_type = engine_clean

        # Add primary database block
        compose_lines.append(DB_SERVICE_TEMPLATES[db_type])
        compose_lines.append("")

        # Add Redis block if needed
        if has_redis:
            compose_lines.append(DB_SERVICE_TEMPLATES["redis"])
            compose_lines.append("")

        # Update environment values if database is different
        if db_type == "postgresql":
            url_env = "      - DATABASE_URL=${DATABASE_URL:-postgresql://app_user:secure_password@database:5432/app_database}"
            # Replace default mongodb string
            for idx, line in enumerate(compose_lines):
                if "mongodb://" in line:
                    compose_lines[idx] = url_env
                    break
        elif db_type == "mysql":
            url_env = "      - DATABASE_URL=${DATABASE_URL:-mysql+connector://app_user:secure_password@database:3306/app_database}"
            # Replace default mongodb string
            for idx, line in enumerate(compose_lines):
                if "mongodb://" in line:
                    compose_lines[idx] = url_env
                    break

        # Networks & Volumes definitions
        compose_lines.append("networks:")
        compose_lines.append("  app-network:")
        compose_lines.append("    driver: bridge")
        compose_lines.append("")

        compose_lines.append("volumes:")
        if db_type == "mongodb":
            compose_lines.append("  mongodata:")
        elif db_type == "postgresql":
            compose_lines.append("  pgdata:")
        elif db_type == "mysql":
            compose_lines.append("  mysqldata:")

        if has_redis:
            compose_lines.append("  redisdata:")

        final_compose = "\n".join(compose_lines) + "\n"
        _logger.info("docker-compose.yml generated successfully")
        return final_compose
