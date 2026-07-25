"""
AIForge V2 – Database Index Optimization Generator
==================================================
Generates optimized SQL index specifications for foreign keys, usernames, emails, and status fields.
"""

from typing import List
from v2.agents.database.models import IndexSpec


class DatabaseIndexGenerator:

    def generate_default_indexes(self) -> List[IndexSpec]:
        return [
            IndexSpec(index_name="idx_users_email", table_name="users", columns=["email"], is_unique=True),
            IndexSpec(index_name="idx_users_username", table_name="users", columns=["username"], is_unique=True),
            IndexSpec(index_name="idx_projects_user_id", table_name="projects", columns=["user_id"], is_unique=False),
            IndexSpec(index_name="idx_tasks_project_id", table_name="tasks", columns=["project_id"], is_unique=False),
            IndexSpec(index_name="idx_agent_logs_agent", table_name="agent_logs", columns=["agent_name"], is_unique=False)
        ]


global_index_generator = DatabaseIndexGenerator()
