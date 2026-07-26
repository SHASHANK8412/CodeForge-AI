# PostgreSQL Schema & Indexing Guide

## Guidelines
1. **Primary Keys**: Every table must define an explicit `PRIMARY KEY` (INTEGER or UUID).
2. **Foreign Keys**: Define `FOREIGN KEY` constraints with `ON DELETE CASCADE` or `ON DELETE SET NULL`.
3. **Indexing**: Create `INDEX` on columns frequently used in `WHERE`, `JOIN`, or `ORDER BY` clauses.
4. **SQLAlchemy ORM**: Use SQLAlchemy 2.0 `DeclarativeBase` models and `async_sessionmaker`.
