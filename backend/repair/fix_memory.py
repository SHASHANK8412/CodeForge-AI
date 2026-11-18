"""
Memory of verified fixes: when a repair is proven by the checks that follow it, the error and the change that fixed it
are kept; when a similar error appears later, those fixes are offered to the model as hints.

* Only **verified** fixes are recorded: the Execution Guardian saw the failure disappear with no new failure, or the
  project's tests passed after the debug loop's patch. A fix that was rolled back or did not help is never stored.
* Errors are matched by a **signature**: the exception type and its message with paths, numbers and quoted literals
  normalised (``FileNotFoundError: [Errno N] No such file or directory: S``). Same type and the same signature is an
  exact match; otherwise token overlap ranks similar ones.
* Fixes contain the user's code, so memory is **per user**: one user's fixes are never shown for another user's
  project. A repair whose owner is unknown is not recorded.
* A hint is a suggestion: the model is told to check that it applies, and the result is verified like any repair.
"""

from __future__ import annotations

import difflib
import json
import re
import threading
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "fix_memory.json"
MAX_PER_USER = 500
MAX_DIFF_CHARS = 1500

_EXC_LINE = re.compile(r"^\s*(?:E\s+)?([A-Za-z_][\w.]*(?:Error|Exception|Exit|Interrupt|Warning)|AssertionError)\s*:?\s*(.*)$",
                       re.M)


def error_signature(text: str) -> Dict[str, str]:
    """{"type", "message", "signature"} of the most specific error line in a failure text."""
    hits = _EXC_LINE.findall(text or "")
    if hits:
        exc_type, msg = hits[-1]
    else:
        first = next((ln.strip() for ln in (text or "").splitlines() if ln.strip()), "")
        exc_type, msg = "Failure", first
    exc_type = exc_type.rsplit(".", 1)[-1]
    norm = msg.strip()
    norm = re.sub(r"(['\"])(?:(?!\1).){0,200}?\1", "S", norm)                  # quoted literals
    norm = re.sub(r"(?:[A-Za-z]:)?[\\/][\w.\\/ -]+", "P", norm)                  # paths
    norm = re.sub(r"0x[0-9a-fA-F]+", "H", norm)
    norm = re.sub(r"\d+(\.\d+)?", "N", norm)
    norm = re.sub(r"\s+", " ", norm)[:200]
    return {"type": exc_type, "message": msg.strip()[:300], "signature": f"{exc_type}: {norm}"}


def _tokens(s: str) -> set:
    return set(re.findall(r"[a-z_]{3,}", s.lower()))


def make_diff(before: Dict[str, Optional[str]], after: Dict[str, Optional[str]]) -> str:
    out: List[str] = []
    for path in sorted(after):
        a, b = (before.get(path) or "").splitlines(), (after.get(path) or "").splitlines()
        out += list(difflib.unified_diff(a, b, fromfile=f"a/{path}", tofile=f"b/{path}", lineterm="", n=2))
    text = "\n".join(out)
    return text if len(text) <= MAX_DIFF_CHARS else text[:MAX_DIFF_CHARS] + "\n... (diff truncated)"


class FixMemory:
    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path) if path else DEFAULT_PATH
        self._lock = threading.Lock()

    def _load(self) -> List[dict]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8")) if self.path.is_file() else []
        except (OSError, ValueError):
            return []

    def _save(self, records: List[dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(records, indent=1), encoding="utf-8")
        tmp.replace(self.path)

    def record(self, user_id: Optional[str], project_id: str, error_text: str, strategy: str,
               before: Dict[str, Optional[str]], after: Dict[str, Optional[str]], source: str) -> Optional[str]:
        """Store a verified fix; returns its id (None when there is no owner or nothing changed)."""
        if not user_id or user_id in ("workflow", "default", "anonymous"):
            return None
        from backend.evolution.autopilot.redact import redact
        diff = make_diff(before, after)
        if not diff.strip():
            return None
        # stored diffs and messages reach later model prompts: secrets are removed before anything is kept
        diff = redact(diff)
        sig = error_signature(redact(error_text))
        rec = {"id": "fix_" + uuid.uuid4().hex[:10], "user_id": user_id, "project_id": project_id,
               "type": sig["type"], "message": sig["message"], "signature": sig["signature"],
               "strategy": strategy, "files": sorted(after), "diff": diff, "source": source,
               "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "times_suggested": 0}
        with self._lock:
            records = self._load()
            records.append(rec)
            mine = [r for r in records if r["user_id"] == user_id]
            if len(mine) > MAX_PER_USER:                       # oldest of this user's records go first
                drop = {r["id"] for r in mine[: len(mine) - MAX_PER_USER]}
                records = [r for r in records if r["id"] not in drop]
            self._save(records)
        return rec["id"]

    def lookup(self, user_id: Optional[str], error_text: str, limit: int = 3, min_similarity: float = 0.5) -> List[dict]:
        """This user's verified fixes for the same or a similar error, best first, each with a `match` score."""
        if not user_id:
            return []
        sig = error_signature(error_text)
        want = _tokens(sig["signature"])
        scored = []
        for r in self._load():
            if r.get("user_id") != user_id or r.get("type") != sig["type"]:
                continue
            if r.get("signature") == sig["signature"]:
                score = 1.0
            else:
                have = _tokens(r.get("signature", ""))
                score = len(want & have) / len(want | have) if (want | have) else 0.0
            if score >= min_similarity:
                scored.append((score, r.get("created_at", ""), r))
        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return [{**r, "match": round(s, 2)} for s, _, r in scored[:limit]]

    def mark_suggested(self, ids: List[str]) -> None:
        if not ids:
            return
        with self._lock:
            records = self._load()
            for r in records:
                if r["id"] in ids:
                    r["times_suggested"] = r.get("times_suggested", 0) + 1
            self._save(records)


def hint_text(matches: List[dict]) -> str:
    """The hint section of a repair prompt (empty when there are no matches)."""
    if not matches:
        return ""
    parts = ["Fixes that resolved the same or a similar error in this user's earlier projects (verified by tests "
             "there). Use one only if it applies to this code:"]
    for m in matches:
        parts.append(f"- {m['signature']}  (match {m['match']}, {m['strategy']})\n```diff\n{m['diff']}\n```")
    return "\n".join(parts)


global_fix_memory = FixMemory()
