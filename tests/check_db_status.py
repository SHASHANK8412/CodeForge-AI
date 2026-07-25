"""
AIForge Database Health & Connectivity Checker
==============================================
Validates:
1. SQLite Local Memory Database (memory.db)
2. Knowledge Graph Database (ai_forge.db)
3. PostgreSQL External Database (DATABASE_URL in .env)
"""

import os
import sys
import sqlite3
from pathlib import Path

# Ensure UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")


def check_sqlite_db(db_path: Path, name: str) -> bool:
    print(f"Checking {name} at '{db_path}'...")
    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        res = cursor.fetchone()
        conn.close()
        if res and res[0] == 1:
            print(f"  ✔ {name}: HEALTHY (Connected & Executed SQL successfully)")
            return True
        else:
            print(f"  ❌ {name}: FAILED (Unexpected query result: {res})")
            return False
    except Exception as exc:
        print(f"  ❌ {name}: FAILED ({exc})")
        return False


def check_postgresql_db() -> bool:
    db_url = os.getenv("DATABASE_URL", "")
    print(f"Checking PostgreSQL Connection (DATABASE_URL)...")
    if not db_url or "postgresql" not in db_url:
        print(f"  ℹ PostgreSQL URL not set or using SQLite fallback ({db_url})")
        return True

    print(f"  Configured URL: {db_url}")
    try:
        import urllib.parse
        parsed = urllib.parse.urlparse(db_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 5432

        # Check socket connectivity first
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3.0)
        result = sock.connect_ex((host, port))
        sock.close()

        if result == 0:
            print(f"  ✔ PostgreSQL TCP Connection to {host}:{port}: HEALTHY (Port Open)")
            return True
        else:
            print(f"  ⚠️ PostgreSQL Port {port} on '{host}' is NOT open or unreachable.")
            print(f"     (Tip: Ensure PostgreSQL service is running on port {port})")
            return False
    except Exception as exc:
        print(f"  ⚠️ PostgreSQL Connection Check Failed: {exc}")
        return False


def main():
    print("======================================================================")
    print(" 🗄️ AIForge Database Health & Status Diagnostic")
    print("======================================================================\n")

    memory_db_path = project_root / "backend" / "database" / "memory.db"
    store_db_path = project_root / "backend" / "memory" / "store" / "ai_forge.db"

    sq1 = check_sqlite_db(memory_db_path, "AIForge Project Memory SQLite DB")
    sq2 = check_sqlite_db(store_db_path, "AIForge System Store SQLite DB")
    pg = check_postgresql_db()

    print("\n======================================================================")
    all_ok = sq1 and sq2
    print(f" DATABASE STATUS: [{'HEALTHY / WORKING' if all_ok else 'ATTENTION REQUIRED'}]")
    print("======================================================================\n")

    return all_ok


if __name__ == "__main__":
    main()
