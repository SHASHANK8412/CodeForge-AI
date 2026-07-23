"""
AIForge Learning - Project Memory Database
==========================================
Persists structured project intelligence metadata in SQLite/JSON.
Stores frameworks, databases, auth types, architectures, components,
design patterns, quality scores, and fixed bugs count.
"""

import json
import sqlite3
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.learning")


class ProjectMemoryDB:
    """
    SQLite and JSON database for storing generated project intelligence.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            db_dir = Path(__file__).resolve().parents[1] / "memory"
            db_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(db_dir / "project_intelligence.db")
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_intelligence (
                    id TEXT PRIMARY KEY,
                    project_name TEXT NOT NULL,
                    tech_stack TEXT,
                    architecture TEXT,
                    authentication TEXT,
                    database_type TEXT,
                    frontend_framework TEXT,
                    design_patterns TEXT,
                    quality_score REAL,
                    bugs_fixed_count INTEGER,
                    raw_summary TEXT,
                    timestamp REAL
                )
            """)
            conn.commit()
            conn.close()
            _logger.info(f"ProjectMemoryDB initialized at '{self.db_path}'")
        except Exception as e:
            _logger.error(f"Failed to initialize ProjectMemoryDB: {e}")

    def save_project(
        self,
        project_name: str,
        tech_stack: List[str],
        architecture: str = "FastAPI + React",
        authentication: str = "JWT",
        database_type: str = "SQLite",
        frontend_framework: str = "React + Tailwind",
        design_patterns: Optional[List[str]] = None,
        quality_score: float = 95.0,
        bugs_fixed_count: int = 0,
        raw_summary: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        import time
        pid = f"proj_{int(time.time() * 1000)}"
        design_patterns = design_patterns or ["Repository", "MVC", "JWT Middleware"]
        raw_summary = raw_summary or {}
        ts = time.time()

        record = {
            "id": pid,
            "project_name": project_name,
            "tech_stack": tech_stack,
            "architecture": architecture,
            "authentication": authentication,
            "database_type": database_type,
            "frontend_framework": frontend_framework,
            "design_patterns": design_patterns,
            "quality_score": round(quality_score, 1),
            "bugs_fixed_count": bugs_fixed_count,
            "raw_summary": raw_summary,
            "timestamp": ts
        }

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO project_intelligence (
                    id, project_name, tech_stack, architecture, authentication,
                    database_type, frontend_framework, design_patterns,
                    quality_score, bugs_fixed_count, raw_summary, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pid, project_name, json.dumps(tech_stack), architecture, authentication,
                database_type, frontend_framework, json.dumps(design_patterns),
                quality_score, bugs_fixed_count, json.dumps(raw_summary), ts
            ))
            conn.commit()
            conn.close()
            _logger.info(f"ProjectMemoryDB saved project '{project_name}' (ID={pid}, Score={quality_score})")
        except Exception as e:
            _logger.error(f"Failed to save project to DB: {e}")

        return record

    def get_all_projects(self) -> List[Dict[str, Any]]:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, project_name, tech_stack, architecture, authentication, database_type, frontend_framework, design_patterns, quality_score, bugs_fixed_count, raw_summary, timestamp FROM project_intelligence ORDER BY timestamp DESC")
            rows = cursor.fetchall()
            conn.close()

            projects = []
            for r in rows:
                projects.append({
                    "id": r[0],
                    "project_name": r[1],
                    "tech_stack": json.loads(r[2] or "[]"),
                    "architecture": r[3],
                    "authentication": r[4],
                    "database_type": r[5],
                    "frontend_framework": r[6],
                    "design_patterns": json.loads(r[7] or "[]"),
                    "quality_score": r[8],
                    "bugs_fixed_count": r[9],
                    "raw_summary": json.loads(r[10] or "{}"),
                    "timestamp": r[11]
                })
            return projects
        except Exception as e:
            _logger.error(f"Failed to retrieve projects: {e}")
            return []
