"""
AIForge V2 – Database Relationship Generator
============================================
Generates 1:1, 1:N, and M:N table relationship specifications.
"""

from typing import List
from v2.agents.database.models import RelationshipSpec


class RelationshipGenerator:

    def generate_default_relationships(self) -> List[RelationshipSpec]:
        return [
            RelationshipSpec(parent_table="users", child_table="projects", rel_type="1:N", foreign_key_col="user_id"),
            RelationshipSpec(parent_table="projects", child_table="tasks", rel_type="1:N", foreign_key_col="project_id"),
            RelationshipSpec(parent_table="projects", child_table="agent_logs", rel_type="1:N", foreign_key_col="project_id")
        ]


global_relationship_generator = RelationshipGenerator()
