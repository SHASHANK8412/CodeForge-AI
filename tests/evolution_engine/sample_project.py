"""
A small FastAPI + sqlite3 app with an N+1 endpoint, used to exercise the Evolution Engine end to end.
GET /api/authors runs one query per author (400 authors, 3 books each, every tenth author has none).
Its tests pin the exact response, including authors without books. write_sample(path) writes it.

CANDIDATES holds two fixed candidate answers (in place of the coding model in tests): a correct JOIN
and a batch version that silently drops authors without books (it must be rejected by the tests).
"""

from pathlib import Path

HEAD = '''import os
import sqlite3
import tempfile

from fastapi import FastAPI

DB_PATH = os.environ.get("DB_PATH") or os.path.join(tempfile.gettempdir(), "aiforge_library.db")

app = FastAPI()


def connect():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = connect()
    conn.execute("CREATE TABLE IF NOT EXISTS authors (id INTEGER PRIMARY KEY, name TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS books (id INTEGER PRIMARY KEY, author_id INTEGER, title TEXT)")
    if conn.execute("SELECT COUNT(*) FROM authors").fetchone()[0] == 0:
        for a in range(1, 401):
            conn.execute("INSERT INTO authors (id, name) VALUES (?, ?)", (a, f"author-{a}"))
            if a % 10 != 0:
                for b in range(3):
                    conn.execute("INSERT INTO books (author_id, title) VALUES (?, ?)", (a, f"book-{a}-{b}"))
    conn.commit()
    conn.close()


init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/authors/count")
def count_authors():
    conn = connect()
    n = conn.execute("SELECT COUNT(*) FROM authors").fetchone()[0]
    conn.close()
    return {"authors": n}


'''

N_PLUS_ONE = '''@app.get("/api/authors")
def list_authors():
    conn = connect()
    authors = conn.execute("SELECT id, name FROM authors ORDER BY id").fetchall()
    out = []
    for author_id, name in authors:
        books = conn.execute("SELECT title FROM books WHERE author_id = ? ORDER BY id", (author_id,)).fetchall()
        out.append({"id": author_id, "name": name, "books": [b[0] for b in books]})
    conn.close()
    return out
'''

JOIN = '''@app.get("/api/authors")
def list_authors():
    conn = connect()
    rows = conn.execute(
        "SELECT a.id, a.name, b.title FROM authors a LEFT JOIN books b ON b.author_id = a.id ORDER BY a.id, b.id"
    ).fetchall()
    conn.close()
    out, by_id = [], {}
    for author_id, name, title in rows:
        if author_id not in by_id:
            by_id[author_id] = {"id": author_id, "name": name, "books": []}
            out.append(by_id[author_id])
        if title is not None:
            by_id[author_id]["books"].append(title)
    return out
'''

DROPS_AUTHORS = '''@app.get("/api/authors")
def list_authors():
    conn = connect()
    names = dict(conn.execute("SELECT id, name FROM authors").fetchall())
    grouped = {}
    for author_id, title in conn.execute("SELECT author_id, title FROM books ORDER BY id").fetchall():
        grouped.setdefault(author_id, []).append(title)
    conn.close()
    return [{"id": a, "name": names[a], "books": titles} for a, titles in sorted(grouped.items())]
'''

TESTS = '''import os
import tempfile

os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402

client = TestClient(app)


def test_every_author_is_listed_in_order_with_books():
    body = client.get("/api/authors").json()
    assert [a["id"] for a in body] == list(range(1, 401))
    assert body[0] == {"id": 1, "name": "author-1", "books": ["book-1-0", "book-1-1", "book-1-2"]}


def test_authors_without_books_are_kept():
    body = {a["id"]: a for a in client.get("/api/authors").json()}
    assert body[10]["books"] == [] and body[400]["books"] == []


def test_count_and_health():
    assert client.get("/api/authors/count").json() == {"authors": 400}
    assert client.get("/health").json() == {"status": "ok"}
'''

MAIN = HEAD + N_PLUS_ONE
FILES = {"backend/main.py": MAIN, "requirements.txt": "fastapi\nhttpx\n", "tests/test_authors.py": TESTS}
CANDIDATES = {"join_query": HEAD + JOIN, "batch_in_query": HEAD + DROPS_AUTHORS}


def write_sample(path) -> Path:
    root = Path(path)
    for rel, content in FILES.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return root


def scripted_model(answers=None):
    """A generator standing in for the coding model: the answer for the strategy named in the request."""
    answers = answers or CANDIDATES

    def generate(system, prompt):
        for strategy, content in answers.items():
            if f"Strategy ({strategy})" in prompt:
                return f"### backend/main.py\n```python\n{content}```\n"
        return "no change"
    return generate
