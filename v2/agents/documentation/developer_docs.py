"""
AIForge V2 – Developer Guide Generator
======================================
Generates DEVELOPER_GUIDE.md covering local environment, running tests, coding standards, and extending agent workflows.
"""

class DeveloperDocsGenerator:

    def generate_developer_docs(self, project_name: str) -> str:
        return f"""# Developer & Contributor Guide – {project_name}

## 1. Local Development Workflow
To add new features or modify existing agents:

```bash
# Activate virtual environment
source venv/bin/activate

# Run backend unit tests
python -m unittest discover backend/tests

# Run end-to-end system verification
python tests/verify_v2_day10.py
```

## 2. Environment Variables (.env)
- `DATABASE_URL`: PostgreSQL connection string.
- `REDIS_URL`: Redis caching broker URI.
- `JWT_SECRET`: Secret key for signing bearer tokens.
- `LOG_LEVEL`: Logging verbosity (`INFO`, `DEBUG`).

## 3. Extending Agent Workflows
To add a new autonomous agent:
1. Inherit from `BaseAgentV2` in `v2/agents/<agent_name>/agent.py`.
2. Define system prompt in `v2/agents/<agent_name>/prompts.py`.
3. Register new node in LangGraph graph `v2/orchestrator/workflow_v2.py`.
"""


global_developer_docs = DeveloperDocsGenerator()
