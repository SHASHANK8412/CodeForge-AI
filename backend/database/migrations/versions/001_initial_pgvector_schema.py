"""Initial PostgreSQL + pgvector Schema

Revision ID: 001_initial_pgvector_schema
Revises: 
Create Date: 2026-08-10 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_pgvector_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension if on PostgreSQL
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    existing_tables = sa.inspect(bind).get_table_names()

    # 1. users
    if 'users' not in existing_tables:
        op.create_table(
            'users',
            sa.Column('id', sa.String(length=64), nullable=False),
            sa.Column('username', sa.String(length=128), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('password_hash', sa.String(length=255), nullable=False),
            sa.Column('role', sa.String(length=64), nullable=True),
            sa.Column('created_at', sa.String(length=64), nullable=True),
            sa.Column('updated_at', sa.String(length=64), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('email'),
            sa.UniqueConstraint('username')
        )

    # 2. projects
    if 'projects' not in existing_tables:
        op.create_table(
            'projects',
            sa.Column('id', sa.String(length=64), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('status', sa.String(length=64), nullable=True),
            sa.Column('created_at', sa.String(length=64), nullable=True),
            sa.Column('updated_at', sa.String(length=64), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_projects_status', 'projects', ['status'])

    # 3. agents
    if 'agents' not in existing_tables:
        op.create_table(
            'agents',
            sa.Column('id', sa.String(length=64), nullable=False),
            sa.Column('project_id', sa.String(length=64), nullable=False),
            sa.Column('name', sa.String(length=128), nullable=False),
            sa.Column('type', sa.String(length=64), nullable=False),
            sa.Column('status', sa.String(length=64), nullable=True),
            sa.Column('created_at', sa.String(length=64), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_agents_proj', 'agents', ['project_id'])

    # 4. runs
    if 'runs' not in existing_tables:
        op.create_table(
            'runs',
            sa.Column('id', sa.String(length=64), nullable=False),
            sa.Column('project_id', sa.String(length=64), nullable=False),
            sa.Column('status', sa.String(length=64), nullable=True),
            sa.Column('duration_s', sa.Float(), nullable=True),
            sa.Column('created_at', sa.String(length=64), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_runs_proj', 'runs', ['project_id'])

    # 5. incidents
    if 'incidents' not in existing_tables:
        op.create_table(
            'incidents',
            sa.Column('id', sa.String(length=64), nullable=False),
            sa.Column('project_id', sa.String(length=64), nullable=False),
            sa.Column('type', sa.String(length=64), nullable=False),
            sa.Column('severity', sa.String(length=64), nullable=True),
            sa.Column('status', sa.String(length=64), nullable=True),
            sa.Column('symptoms', sa.Text(), nullable=True),
            sa.Column('root_cause', sa.Text(), nullable=True),
            sa.Column('created_at', sa.String(length=64), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_incidents_proj_status', 'incidents', ['project_id', 'status'])

    # 6. deployments
    if 'deployments' not in existing_tables:
        op.create_table(
            'deployments',
            sa.Column('id', sa.String(length=64), nullable=False),
            sa.Column('project_id', sa.String(length=64), nullable=False),
            sa.Column('environment', sa.String(length=64), nullable=True),
            sa.Column('status', sa.String(length=64), nullable=True),
            sa.Column('commit_hash', sa.String(length=64), nullable=True),
            sa.Column('created_at', sa.String(length=64), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_deployments_proj', 'deployments', ['project_id'])

    # 7. architecture_decisions
    if 'architecture_decisions' not in existing_tables:
        op.create_table(
            'architecture_decisions',
            sa.Column('id', sa.String(length=64), nullable=False),
            sa.Column('project_id', sa.String(length=64), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('status', sa.String(length=64), nullable=True),
            sa.Column('decision', sa.Text(), nullable=False),
            sa.Column('tradeoffs', sa.Text(), nullable=True),
            sa.Column('created_at', sa.String(length=64), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_arch_dec_proj', 'architecture_decisions', ['project_id'])

    # 8. engineering_memories
    if 'engineering_memories' not in existing_tables:
        op.create_table(
            'engineering_memories',
            sa.Column('id', sa.String(length=64), nullable=False),
            sa.Column('project_id', sa.String(length=64), nullable=False),
            sa.Column('type', sa.String(length=64), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('importance', sa.String(length=64), nullable=True),
            sa.Column('confidence', sa.String(length=64), nullable=True),
            sa.Column('source', sa.String(length=64), nullable=True),
            sa.Column('status', sa.String(length=64), nullable=True),
            sa.Column('version', sa.Integer(), nullable=True),
            sa.Column('tags_json', sa.Text(), nullable=True),
            sa.Column('created_at', sa.String(length=64), nullable=True),
            sa.Column('updated_at', sa.String(length=64), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_memories_proj_status', 'engineering_memories', ['project_id', 'status'])

    # 9. vector_embeddings
    if 'vector_embeddings' not in existing_tables:
        op.create_table(
            'vector_embeddings',
            sa.Column('id', sa.String(length=64), nullable=False),
            sa.Column('project_id', sa.String(length=64), nullable=False),
            sa.Column('collection_name', sa.String(length=128), nullable=True),
            sa.Column('document_id', sa.String(length=128), nullable=False),
            sa.Column('text', sa.Text(), nullable=False),
            sa.Column('metadata_json', sa.Text(), nullable=True),
            sa.Column('embedding_json', sa.Text(), nullable=False),
            sa.Column('created_at', sa.String(length=64), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_vec_proj_coll', 'vector_embeddings', ['project_id', 'collection_name'])
        op.create_index('idx_vec_doc_id', 'vector_embeddings', ['project_id', 'document_id'])



def downgrade() -> None:
    op.drop_table('vector_embeddings')
    op.drop_table('engineering_memories')
    op.drop_table('architecture_decisions')
    op.drop_table('deployments')
    op.drop_table('incidents')
    op.drop_table('runs')
    op.drop_table('agents')
    op.drop_table('projects')
    op.drop_table('users')
