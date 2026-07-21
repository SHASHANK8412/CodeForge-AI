import sqlite3
import logging
from pathlib import Path
from typing import Dict, Any, List, Set

_logger = logging.getLogger("aiforge.knowledge")

class KnowledgeGraph:
    """
    Persistent SQLite adjacency-list Knowledge Graph mapping technology relationships.
    """

    def __init__(self, db_path: str = None) -> None:
        if db_path is None:
            db_path = str(Path(__file__).resolve().parent.parent / "memory" / "knowledge.db")
        self.db_path = Path(db_path)

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.db_path), timeout=10.0)

    def add_node(self, name: str, category: str = "framework") -> None:
        name_clean = name.lower().strip()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO graph_nodes (name, category)
                VALUES (?, ?)
            """, (name_clean, category))
            conn.commit()

    def add_edge(self, source: str, target: str, relation: str = "uses") -> None:
        s_clean = source.lower().strip()
        t_clean = target.lower().strip()
        
        # Add nodes automatically
        self.add_node(s_clean)
        self.add_node(t_clean)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO graph_edges (source, target, relation)
                VALUES (?, ?, ?)
            """, (s_clean, t_clean, relation))
            conn.commit()

    def get_neighbors(self, node: str) -> List[Dict[str, str]]:
        node_clean = node.lower().strip()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT target, relation FROM graph_edges WHERE source = ?", (node_clean,))
            return [{"target": row[0], "relation": row[1]} for row in cursor.fetchall()]

    def get_all_edges(self) -> List[Dict[str, str]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT source, target, relation FROM graph_edges")
            return [{"source": row[0], "target": row[1], "relation": row[2]} for row in cursor.fetchall()]

    def get_all_nodes(self) -> List[Dict[str, str]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, category FROM graph_nodes")
            return [{"name": row[0], "category": row[1]} for row in cursor.fetchall()]
