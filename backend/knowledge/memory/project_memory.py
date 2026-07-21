import sqlite3
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.knowledge")

class ProjectMemory:
    """
    Manages SQLite database storage for completed projects, bug histories,
    lessons learned, and framework experience metrics.
    """

    def __init__(self, db_path: str = None) -> None:
        if db_path is None:
            db_path = str(Path(__file__).resolve().parent / "knowledge.db")
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.db_path), timeout=10.0)

    def _init_db(self) -> None:
        """
        Initializes schema tables: projects, bugs, lessons, experience, graph nodes/edges.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Projects Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    type TEXT,
                    frameworks TEXT,
                    frontend TEXT,
                    backend TEXT,
                    database_name TEXT,
                    auth TEXT,
                    folder_structure TEXT,
                    deployment TEXT,
                    build_time INTEGER,
                    success_rate REAL
                )
            """)

            # Bugs Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bugs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bug_hash TEXT UNIQUE,
                    description TEXT,
                    category TEXT,
                    root_cause TEXT,
                    fix_solution TEXT,
                    severity TEXT,
                    prevention TEXT
                )
            """)

            # Lessons Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lessons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name TEXT,
                    worked TEXT,
                    failed TEXT,
                    bottlenecks TEXT
                )
            """)

            # Experience Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS experience (
                    technology TEXT PRIMARY KEY,
                    score INTEGER
                )
            """)

            # Graph Nodes & Edges Tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS graph_nodes (
                    name TEXT PRIMARY KEY,
                    category TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS graph_edges (
                    source TEXT,
                    target TEXT,
                    relation TEXT,
                    PRIMARY KEY (source, target, relation)
                )
            """)
            conn.commit()

    def save_project(self, project: Dict[str, Any]) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO projects (name, type, frameworks, frontend, backend, database_name, auth, folder_structure, deployment, build_time, success_rate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                project.get("name"),
                project.get("type"),
                ",".join(project.get("frameworks", [])),
                project.get("frontend"),
                project.get("backend"),
                project.get("database"),
                project.get("auth"),
                json_str := json.dumps(project.get("folder_structure", [])),
                project.get("deployment"),
                project.get("build_time", 40),
                project.get("success_rate", 95.0)
            ))
            conn.commit()

    def save_bug(self, bug: Dict[str, Any]) -> None:
        desc = bug.get("description", "")
        # Create hash to prevent duplicate bug items
        bug_hash = hashlib.md5(desc.encode("utf-8")).hexdigest()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO bugs (bug_hash, description, category, root_cause, fix_solution, severity, prevention)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                bug_hash,
                desc,
                bug.get("category"),
                bug.get("root_cause"),
                bug.get("fix"),
                bug.get("severity"),
                bug.get("prevention")
            ))
            conn.commit()

    def get_all_bugs(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM bugs")
            return [dict(row) for row in cursor.fetchall()]

    def save_lesson(self, project_name: str, lesson: Dict[str, Any]) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO lessons (project_name, worked, failed, bottlenecks)
                VALUES (?, ?, ?, ?)
            """, (
                project_name,
                ",".join(lesson.get("worked", [])),
                ",".join(lesson.get("failed", [])),
                ",".join(lesson.get("bottlenecks", []))
            ))
            conn.commit()

    def get_all_lessons(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM lessons")
            return [dict(row) for row in cursor.fetchall()]

    def update_experience(self, technology: str, points: int = 1) -> int:
        tech_clean = technology.lower().strip()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT score FROM experience WHERE technology = ?", (tech_clean,))
            row = cursor.fetchone()
            if row:
                new_score = row[0] + points
                cursor.execute("UPDATE experience SET score = ? WHERE technology = ?", (new_score, tech_clean))
            else:
                new_score = points
                cursor.execute("INSERT INTO experience (technology, score) VALUES (?, ?)", (tech_clean, new_score))
            conn.commit()
            return new_score

    def get_experience_score(self, technology: str) -> int:
        tech_clean = technology.lower().strip()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT score FROM experience WHERE technology = ?", (tech_clean,))
            row = cursor.fetchone()
            return row[0] if row else 0

import json
