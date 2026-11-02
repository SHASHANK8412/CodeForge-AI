"""
Does the Reviewer agent catch real bugs?

Each case is a small FastAPI snippet with **one planted bug** whose ground
truth we know, plus clean controls with no bug. The reviewer sees the code
exactly as it would in the pipeline (``build_reviewer_prompt``).

Scoring
-------
* **detected**: some issue the reviewer reports mentions the bug, judged by
  case-insensitive keyword match against that issue's ``problem`` + ``fix``.
  Keyword matching is crude on purpose (cheap, deterministic, no judge model);
  every review is saved so a human can audit misses and false matches.
* **recall** = detected / buggy cases.
* **false-alarm rate** = clean controls where the reviewer raised a
  ``critical`` or ``major`` issue / clean controls.

    python -m benchmarks.reviewer_eval --model qwen2.5-coder:7b
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@dataclass(frozen=True)
class ReviewCase:
    id: str
    bug: Optional[str]          # None for clean controls
    keywords: List[str] = field(default_factory=list)
    code: str = ""


CASES: List[ReviewCase] = [
    ReviewCase("sql-injection", "SQL built with an f-string from user input",
               ["injection", "parameteri", "f-string", "sanitiz", "bind"],
               '''from fastapi import FastAPI
import sqlite3
app = FastAPI()
db = sqlite3.connect("app.db", check_same_thread=False)

@app.get("/users")
def find_user(name: str):
    rows = db.execute(f"SELECT id, name FROM users WHERE name = '{name}'").fetchall()
    return [{"id": r[0], "name": r[1]} for r in rows]
'''),
    ReviewCase("plaintext-password", "passwords stored and compared in plain text",
               ["plain", "hash", "bcrypt", "argon", "passlib"],
               '''from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
app = FastAPI()
USERS = {}

class Creds(BaseModel):
    username: str
    password: str

@app.post("/register")
def register(c: Creds):
    USERS[c.username] = {"password": c.password}
    return {"ok": True}

@app.post("/login")
def login(c: Creds):
    if USERS.get(c.username, {}).get("password") != c.password:
        raise HTTPException(401)
    return {"ok": True}
'''),
    ReviewCase("missing-auth", "destructive endpoint has no authentication",
               ["auth", "unauthori", "permission", "access control", "protect"],
               '''from fastapi import FastAPI, Depends, HTTPException
from auth import get_current_user
app = FastAPI()
POSTS = {1: {"id": 1, "author": "alice"}}

@app.get("/posts/{post_id}")
def read_post(post_id: int, user=Depends(get_current_user)):
    return POSTS[post_id]

@app.delete("/posts/{post_id}")
def delete_post(post_id: int):
    POSTS.pop(post_id, None)
    return {"deleted": post_id}
'''),
    ReviewCase("hardcoded-secret", "JWT signing key hard-coded in source",
               ["hardcod", "hard-cod", "environment", "env var", "secret"],
               '''from datetime import datetime, timedelta
import jwt
SECRET_KEY = "supersecret123"

def create_token(user_id: int) -> str:
    payload = {"sub": str(user_id), "exp": datetime.utcnow() + timedelta(hours=1)}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
'''),
    ReviewCase("pagination-off-by-one", "1-based page number used as 0-based offset (skips page 1)",
               ["off-by-one", "off by one", "page - 1", "page-1", "skip", "first page", "offset"],
               '''from fastapi import FastAPI
app = FastAPI()
ITEMS = list(range(100))

@app.get("/items")
def list_items(page: int = 1, limit: int = 10):
    start = page * limit
    return ITEMS[start:start + limit]
'''),
    ReviewCase("float-money", "money stored as float",
               ["decimal", "float", "precision", "rounding"],
               '''from fastapi import FastAPI
from pydantic import BaseModel
app = FastAPI()
BALANCES: dict[int, float] = {1: 100.0}

class Deposit(BaseModel):
    amount: float

@app.post("/accounts/{acc}/deposit")
def deposit(acc: int, d: Deposit):
    BALANCES[acc] = BALANCES.get(acc, 0.0) + d.amount
    return {"balance": BALANCES[acc]}
'''),
    ReviewCase("idor", "any user can read any other user's todo",
               ["owner", "user_id", "belong", "other user", "idor", "authoriz"],
               '''from fastapi import FastAPI, Depends, HTTPException
from auth import get_current_user
app = FastAPI()
TODOS = {1: {"id": 1, "owner_id": 7, "title": "secret plan"}}

@app.get("/todos/{todo_id}")
def get_todo(todo_id: int, user=Depends(get_current_user)):
    todo = TODOS.get(todo_id)
    if not todo:
        raise HTTPException(404)
    return todo
'''),
    ReviewCase("mutable-default", "mutable default argument shared across calls",
               ["mutable", "default argument", "default parameter", "shared"],
               '''def add_tag(tag: str, tags: list = []) -> list:
    tags.append(tag)
    return tags
'''),
    ReviewCase("missing-404", "unknown id raises KeyError -> HTTP 500 instead of 404",
               ["404", "keyerror", "not found", "500", "missing"],
               '''from fastapi import FastAPI
app = FastAPI()
NOTES = {1: "hello"}

@app.get("/notes/{note_id}")
def get_note(note_id: int):
    return {"id": note_id, "text": NOTES[note_id]}
'''),
    ReviewCase("jwt-no-verify", "JWT decoded without verifying the signature",
               ["signature", "verify", "forg"],
               '''import jwt
from fastapi import Header, HTTPException

def current_user_id(authorization: str = Header(...)) -> int:
    token = authorization.removeprefix("Bearer ")
    payload = jwt.decode(token, options={"verify_signature": False})
    return int(payload["sub"])
'''),
    ReviewCase("swallowed-exception", "bare except hides failures and returns success",
               ["bare except", "except:", "swallow", "broad", "silent", "hides"],
               '''from fastapi import FastAPI
app = FastAPI()

@app.post("/orders")
def create_order(order: dict):
    try:
        total = sum(i["price"] * i["qty"] for i in order["items"])
        save(order, total)
    except:
        pass
    return {"status": "created"}
'''),
    ReviewCase("overbooking-race", "capacity check and booking are not atomic (race condition)",
               ["race", "concurren", "atomic", "lock", "transaction"],
               '''import asyncio
from fastapi import FastAPI, HTTPException
app = FastAPI()
EVENTS = {1: {"capacity": 2, "booked": 0}}

@app.post("/events/{eid}/book")
async def book(eid: int):
    ev = EVENTS[eid]
    if ev["booked"] >= ev["capacity"]:
        raise HTTPException(409, "full")
    await asyncio.sleep(0.01)  # e.g. payment call
    ev["booked"] += 1
    return ev
'''),
    # ---- clean controls -------------------------------------------------
    ReviewCase("clean-param-sql", None, [], '''from fastapi import FastAPI
import sqlite3
app = FastAPI()
db = sqlite3.connect("app.db", check_same_thread=False)

@app.get("/users")
def find_user(name: str):
    rows = db.execute("SELECT id, name FROM users WHERE name = ?", (name,)).fetchall()
    return [{"id": r[0], "name": r[1]} for r in rows]
'''),
    ReviewCase("clean-404", None, [], '''from fastapi import FastAPI, HTTPException
app = FastAPI()
NOTES = {1: "hello"}

@app.get("/notes/{note_id}")
def get_note(note_id: int):
    if note_id not in NOTES:
        raise HTTPException(status_code=404, detail="note not found")
    return {"id": note_id, "text": NOTES[note_id]}
'''),
    ReviewCase("clean-pagination", None, [], '''from fastapi import FastAPI, Query
app = FastAPI()
ITEMS = list(range(100))

@app.get("/items")
def list_items(page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100)):
    start = (page - 1) * limit
    return ITEMS[start:start + limit]
'''),
]


def score_case(case: ReviewCase, review: Dict[str, Any]) -> Dict[str, Any]:
    issues = [i for i in (review.get("issues") or []) if isinstance(i, dict)]
    serious = [i for i in issues if str(i.get("severity", "")).lower() in {"critical", "major"}]
    if case.bug is None:
        return {"id": case.id, "clean": True, "false_alarm": bool(serious), "issues": len(issues)}
    hit = None
    for issue in issues:
        text = f"{issue.get('problem', '')} {issue.get('fix', '')}".lower()
        if any(k in text for k in case.keywords):
            hit = issue
            break
    return {"id": case.id, "clean": False, "detected": hit is not None, "issues": len(issues),
            "matched_severity": (hit or {}).get("severity")}


def summarize(scored: List[Dict[str, Any]]) -> Dict[str, Any]:
    buggy = [s for s in scored if not s["clean"]]
    clean = [s for s in scored if s["clean"]]
    detected = sum(1 for s in buggy if s["detected"])
    alarms = sum(1 for s in clean if s["false_alarm"])
    return {
        "buggy_cases": len(buggy), "detected": detected,
        "recall": round(detected / len(buggy), 4) if buggy else None,
        "clean_cases": len(clean), "false_alarms": alarms,
        "false_alarm_rate": round(alarms / len(clean), 4) if clean else None,
    }


ReviewFn = Callable[[str], Awaitable[str]]


async def _default_review(code: str) -> str:
    from backend.agents.reviewer_agent import ReviewerAgent
    from backend.services.prompt_builder import global_prompt_builder
    prompt = global_prompt_builder.build_reviewer_prompt(backend_code=code)
    return await ReviewerAgent().run_async(prompt)


async def run_reviewer_eval(review_fn: Optional[ReviewFn] = None, out_dir: Optional[Path] = None) -> Dict[str, Any]:
    from backend.agents.reviewer_agent import ReviewerAgent
    from backend.observability.tracing import global_trace

    review_fn = review_fn or _default_review
    parser = ReviewerAgent()
    os.environ["AIFORGE_DISABLE_LLM_CACHE"] = "1"
    global_trace.reset()
    rows = []
    for case in CASES:
        raw = await review_fn(case.code)
        parsed = parser.parse_review_json(raw)
        rows.append({**score_case(case, parsed), "bug": case.bug, "review": raw})
    tele = global_trace.summary()
    result = {
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "summary": summarize(rows),
        "llm_fallbacks": tele["llm_fallbacks"],
        "valid": tele["llm_fallbacks"] == 0,
        "cases": rows,
    }
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "reviewer_eval.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m benchmarks.reviewer_eval")
    ap.add_argument("--model", help="model for the reviewer, e.g. qwen2.5-coder:7b")
    ap.add_argument("--out", default=str(REPO_ROOT / "benchmarks" / "runs" / "reviewer"))
    args = ap.parse_args(argv)
    if args.model:
        os.environ["AIFORGE_CODING_MODEL"] = os.environ["AIFORGE_GENERAL_MODEL"] = args.model
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    res = asyncio.run(run_reviewer_eval(out_dir=Path(args.out) / stamp))
    s = res["summary"]
    print(f"recall {s['detected']}/{s['buggy_cases']} | false alarms {s['false_alarms']}/{s['clean_cases']}"
          f"{'' if res['valid'] else '  (INVALID: LLM fallbacks occurred)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
