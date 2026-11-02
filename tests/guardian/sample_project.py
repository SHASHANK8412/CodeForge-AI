"""
A small, deliberately vulnerable FastAPI app (sqlite3, standard library) used to verify the Security
Guardian end to end. Its own tests check normal behaviour only. write_sample(path) writes it.
(A module rather than files, so pytest never collects the sample's tests as AIForge tests.)

Planted issues: SQL injection in /api/users/search, password hashes returned by /api/users, an
unauthenticated DELETE route (other routes use an auth dependency), CORS any-origin with credentials,
a hardcoded signing key, MD5 password hashing. /api/admin/reset is properly protected (a false-positive check).
"""

from pathlib import Path

MAIN = '''import hashlib
import os
import sqlite3

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

DB_PATH = os.environ.get("DB_PATH", "users.db")
SECRET_KEY = "super-secret-signing-key-123"

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


def hash_password(password: str) -> str:
    return hashlib.md5(password.encode()).hexdigest()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, password_hash TEXT)")
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        for name in ("alice", "bob", "carol"):
            conn.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                         (name, f"{name}@example.com", hash_password(name + "-pw")))
    conn.commit()
    conn.close()


init_db()


def require_admin(x_api_key: str = Header(None)):
    if x_api_key != os.environ.get("ADMIN_KEY", "change-me"):
        raise HTTPException(status_code=401, detail="unauthorized")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/users/search")
def search_users(name: str):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(f"SELECT id, name, email FROM users WHERE name = '{name}'").fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "email": r[2]} for r in rows]


@app.get("/api/users")
def list_users():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT id, name, password_hash FROM users").fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "password_hash": r[2]} for r in rows]


@app.delete("/api/users/{user_id}")
def delete_user(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return {"deleted": user_id}


@app.post("/api/admin/reset", dependencies=[Depends(require_admin)])
def reset():
    return {"reset": True}
'''

TESTS = '''import os
import tempfile

os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402

client = TestClient(app)


def test_search_finds_a_user_by_name():
    body = client.get("/api/users/search", params={"name": "alice"}).json()
    assert [u["name"] for u in body] == ["alice"] and body[0]["email"] == "alice@example.com"


def test_search_without_match_is_empty():
    assert client.get("/api/users/search", params={"name": "nobody"}).json() == []


def test_list_users_has_names():
    assert sorted(u["name"] for u in client.get("/api/users").json()) == ["alice", "bob", "carol"]


def test_admin_reset_needs_the_key():
    assert client.post("/api/admin/reset").status_code == 401
'''

FILES = {"backend/main.py": MAIN, "requirements.txt": "fastapi\nhttpx\n", "tests/test_users.py": TESTS}


def write_sample(path) -> Path:
    root = Path(path)
    for rel, content in FILES.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return root
