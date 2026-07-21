import time
import sqlite3
import logging
from typing import Dict, Any, List

from .base_tool import BaseTool

_logger = logging.getLogger("aiforge.tools")

class PostgresTool(BaseTool):
    """
    Simulates / wraps database queries executing against target SQL tables.
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        super().__init__("PostgresTool")
        self.db_path = db_path
        self.conn = None

    def initialize(self) -> None:
        # Create standard schema for queries
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self.conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)")
        self.conn.commit()

    def validate(self, **kwargs) -> bool:
        sql = kwargs.get("sql", "")
        # Enforce parameterized query standards (block manual quote injections)
        if "'" in sql or '"' in sql:
            if "?" not in sql and "%s" not in sql:
                _logger.warning("Unsafe SQL: Raw binds detected without parameter markers.")
                return False
        return True

    def execute(self, **kwargs) -> Dict[str, Any]:
        sql = kwargs.get("sql", "")
        params = kwargs.get("params", ())

        if not self.validate(sql=sql):
            return self._format_result(False, "", "SQL query failed safety parameterizations validation checks.", 0.0, 1)

        start = time.perf_counter()
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, params)
            
            if sql.strip().upper().startswith("SELECT"):
                rows = cursor.fetchall()
                output = str(rows)
            else:
                self.conn.commit()
                output = f"Rows affected: {cursor.rowcount}"

            elapsed = time.perf_counter() - start
            return self._format_result(True, output, "", elapsed, 0)
        except Exception as e:
            elapsed = time.perf_counter() - start
            return self._format_result(False, "", f"Database Query error: {str(e)}", elapsed, -1)

    def cleanup(self) -> None:
        if self.conn:
            self.conn.close()

    def health_check(self) -> bool:
        return True
