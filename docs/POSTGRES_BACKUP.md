# AIForge — PostgreSQL & pgvector Database Backup & Disaster Recovery Guide

This document outlines non-destructive backup strategies, point-in-time recovery (PITR) procedures, and WAL archiving policies for AIForge PostgreSQL + pgvector unified storage.

---

## 1. Environment & Backup Strategy Overview

AIForge stores structured application data (Users, Projects, Incidents, Engineering Memories) and vector embeddings (pgvector HNSW/IVFFlat indexes) in PostgreSQL.

Backup types supported:
- **Logical Backups (`pg_dump`)**: Portable SQL/custom archives for schema & data snapshots.
- **Physical WAL Archiving**: Continuous Write-Ahead Log archiving for point-in-time recovery.

> [!IMPORTANT]
> Never execute destructive `DROP DATABASE` or `TRUNCATE` operations automatically. Always verify backups in an isolated staging environment first.

---

## 2. Logical Backups (`pg_dump`)

### Daily Automated Backup Script Example (`scripts/backup_postgres.sh`)

```bash
#!/usr/bin/env bash
set -eo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/aiforge}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DB_NAME="${POSTGRES_DB:-aiforge_db}"
DB_USER="${POSTGRES_USER:-postgres}"

mkdir -p "${BACKUP_DIR}"

echo "Starting logical backup for database: ${DB_NAME}"
pg_dump -h localhost -U "${DB_USER}" -F c -b -v -f "${BACKUP_DIR}/aiforge_${TIMESTAMP}.dump" "${DB_NAME}"

echo "Backup completed: ${BACKUP_DIR}/aiforge_${TIMESTAMP}.dump"
```

### Restoring a Backup (`pg_restore`)

```bash
pg_restore -h localhost -U postgres -d aiforge_db --clean --if-exists /var/backups/aiforge/aiforge_20260810_000000.dump
```

---

## 3. pgvector Index Rebuilding Post-Restore

When restoring pgvector vector embeddings, reindex vector indexes for optimal query performance:

```sql
-- Re-index vector HNSW index post restore
REINDEX INDEX idx_vec_embedding_hnsw;
ANALYZE vector_embeddings;
```

---

## 4. Disaster Recovery Checklist

1. Verify `GET /health/database` returns `"status": "healthy"`.
2. Ensure pgvector extension is active: `SELECT * FROM pg_extension WHERE extname = 'vector';`.
3. Verify strict project isolation (`project_id` filters) remain intact.
