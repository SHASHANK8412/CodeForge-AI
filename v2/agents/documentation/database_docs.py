"""
AIForge V2 – Database Documentation Generator
=============================================
Generates DATABASE_DOCUMENTATION.md documenting PostgreSQL tables, relationships, indexes, and Alembic migrations.
"""

class DatabaseDocsGenerator:

    def generate_database_docs(self, project_name: str) -> str:
        return f"""# PostgreSQL Database Documentation – {project_name}

## 1. Relational Schema Summary

### Table `users`
- `id` (VARCHAR 64, PK)
- `username` (VARCHAR 128, UNIQUE, NOT NULL)
- `email` (VARCHAR 256, UNIQUE, NOT NULL)
- `password_hash` (VARCHAR 256, NOT NULL)
- `role` (VARCHAR 32, DEFAULT 'user')

### Table `projects`
- `id` (VARCHAR 64, PK)
- `user_id` (VARCHAR 64, FK `users.id` CASCADE)
- `name` (VARCHAR 256, NOT NULL)
- `complexity_tier` (VARCHAR 32, DEFAULT 'medium')

### Table `tasks`
- `id` (VARCHAR 64, PK)
- `project_id` (VARCHAR 64, FK `projects.id` CASCADE)
- `assigned_agent` (VARCHAR 64, NOT NULL)
- `title` (VARCHAR 256, NOT NULL)

## 2. Table Relationships
- `users` (1) $\rightarrow$ (N) `projects` (Foreign Key: `projects.user_id`)
- `projects` (1) $\rightarrow$ (N) `tasks` (Foreign Key: `tasks.project_id`)

## 3. Database Indexes
- `idx_users_email` ON `users(email)`
- `idx_projects_user_id` ON `projects(user_id)`
- `idx_tasks_project_id` ON `tasks(project_id)`
"""


global_database_docs = DatabaseDocsGenerator()
