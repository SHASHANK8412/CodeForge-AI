"""
AIForge V2 – Architecture Documentation Generator
=================================================
Generates ARCHITECTURE.md covering high/low-level system topology, data flow, and agent workflows.
"""

class ArchitectureDocsGenerator:

    def generate_architecture_docs(self, project_name: str) -> str:
        return f"""# System Architecture & Technical Topology – {project_name}

## 1. High-Level Architectural Pattern
The application follows a **Clean Architecture / Layered Microservice** pattern:

```text
               +----------------------------------+
               |        React Frontend SPA        |
               +----------------------------------+
                                |  HTTP / REST API
                                v
               +----------------------------------+
               |       FastAPI Gateway & Routers  |
               +----------------------------------+
                                |  Internal Calls
                                v
               +----------------------------------+
               |      Service Layer (Logic)       |
               +----------------------------------+
                                |  Repository Interface
                                v
               +----------------------------------+
               |    Repository Layer & SQLAlchemy  |
               +----------------------------------+
                                |  SQL Queries
                                v
               +----------------------------------+
               |       PostgreSQL Database        |
               +----------------------------------+
```

## 2. Component Responsibilities
- **Presentation Layer**: React TSX components (`Navbar`, `Sidebar`, `Card`, `Dashboard`).
- **State Layer**: Zustand reactive state stores (`useAuthStore`, `useProjectStore`).
- **REST API Layer**: FastAPI APIRouters with Pydantic request/response validation schemas.
- **Service Layer**: Business rules, JWT token generation, password hashing (`AuthService`, `ProjectService`).
- **Persistence Layer**: SQLAlchemy ORM models & PostgreSQL database repositories.
"""


global_architecture_docs = ArchitectureDocsGenerator()
