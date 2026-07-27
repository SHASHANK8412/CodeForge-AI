"""
AIForge Architecture Diagram Generator
======================================
Generates Mermaid diagram specifications for C4 Context, Container, Component, Sequence, Deployment, and Database ER diagrams.
"""

import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.architecture.diagrams")


class ArchitectureDiagramGenerator:
    """
    Generates Mermaid C4 and ER diagrams.
    """

    def generate_all_diagrams(self, project_name: str = "Project") -> Dict[str, Any]:
        c4_context = f"""graph TD
    User["👤 End User"] -->|HTTP REST| Gateway["🚪 API Gateway"]
    Gateway -->|Auth Check| AuthService["🔑 Auth Service"]
    Gateway -->|App Logic| CoreService["⚙️ Core API Service"]
    CoreService -->|Query/Store| DB[("🗄️ PostgreSQL")]
    CoreService -->|Cache| Cache[("⚡ Redis Cache")]
"""

        c4_container = f"""graph TB
    subgraph Client Layer
        Web["React Web App"]
    end
    subgraph Service Layer
        Nginx["Nginx Gateway"]
        Auth["Auth Service"]
        API["FastAPI Application"]
    end
    subgraph Data Layer
        PG[("PostgreSQL")]
        Redis[("Redis")]
    end
    Web --> Nginx
    Nginx --> Auth
    Nginx --> API
    API --> PG
    API --> Redis
"""

        sequence_diagram = f"""sequenceDiagram
    autonumber
    Client->>Gateway: POST /api/v1/auth/login
    Gateway->>AuthService: Validate Credentials
    AuthService-->>Gateway: Return JWT Token
    Gateway-->>Client: 200 OK + JWT Bearer
"""

        er_diagram = f"""erDiagram
    USER ||--o{{ PROJECT : owns
    PROJECT ||--o{{ ARTIFACT : contains
    USER {{
        uuid id PK
        string email
        string hashed_password
    }}
    PROJECT {{
        uuid id PK
        uuid user_id FK
        string title
    }}
    ARTIFACT {{
        uuid id PK
        uuid project_id FK
        string filename
    }}
"""

        diagrams = {
            "project_name": project_name,
            "c4_context": c4_context,
            "c4_container": c4_container,
            "sequence_diagram": sequence_diagram,
            "er_diagram": er_diagram
        }

        _logger.info(f"ArchitectureDiagramGenerator: Generated C4 and ER diagrams for '{project_name}'")
        return diagrams


global_architecture_diagram_generator = ArchitectureDiagramGenerator()
