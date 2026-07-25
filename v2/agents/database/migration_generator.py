"""
AIForge V2 – Alembic Migration Generator
========================================
Generates versioned Alembic schema migration scripts (`upgrade()` & `downgrade()`).
"""

from typing import List
from v2.agents.database.models import MigrationSpec


class AlembicMigrationGenerator:

    def generate_default_migrations(self) -> List[MigrationSpec]:
        return [
            MigrationSpec(
                revision_id="0001_initial_schema",
                description="Create initial database tables (users, projects, tasks, agent_logs)",
                up_script="""def upgrade():
    op.create_table('users', sa.Column('id', sa.String(), primary_key=True), sa.Column('username', sa.String(), unique=True))
    op.create_table('projects', sa.Column('id', sa.String(), primary_key=True), sa.Column('user_id', sa.String(), sa.ForeignKey('users.id')))
    op.create_table('tasks', sa.Column('id', sa.String(), primary_key=True), sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id')))
""",
                down_script="""def downgrade():
    op.drop_table('tasks')
    op.drop_table('projects')
    op.drop_table('users')
"""
            )
        ]


global_migration_generator = AlembicMigrationGenerator()
