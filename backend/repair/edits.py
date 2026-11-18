"""
Search/replace edits: the model changes code by quoting the lines it replaces, instead of rewriting whole files.

A whole-file rewrite costs tokens for every unchanged line and can silently drop code the model did not mean to
touch. An edit names the exact lines it replaces, so it either applies precisely or fails loudly:

    backend/main.py
    <<<<<<< SEARCH
    def get_note(note_id: int):
        return NOTES.get(note_id, {})
    =======
    def get_note(note_id: int):
        if note_id not in NOTES:
            raise HTTPException(status_code=404)
        return NOTES[note_id]
    >>>>>>> REPLACE

``apply_edits`` requires each SEARCH text to occur exactly once in the current file, first verbatim, then ignoring
trailing whitespace, then ignoring a uniform indentation offset (the replacement is re-indented to match). Anything
else - not found, ambiguous, an unknown file - is reported with a reason the model can act on in a retry.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

INSTRUCTIONS = """Reply with search/replace edits, not whole files. For every change write the file path on its own line, then:

path/to/file.py
<<<<<<< SEARCH
the exact lines as they are now in the file (copy them character for character, including indentation;
include enough lines to match exactly one place)
=======
the lines that replace them
>>>>>>> REPLACE

Several blocks per file are fine. To create a new file, leave SEARCH empty. To delete lines, leave REPLACE empty.
Change only what the problem requires; do not repeat unchanged code outside the blocks."""

_SEARCH, _DIVIDER, _REPLACE = "<<<<<<< SEARCH", "=======", ">>>>>>> REPLACE"


@dataclass
class Edit:
    path: str
    search: str
    replace: str


@dataclass
class EditResult:
    changed: Dict[str, str] = field(default_factory=dict)     # path -> new full content (only files that changed)
    applied: int = 0
    errors: List[str] = field(default_factory=list)


def _clean_path(line: str) -> str:
    p = line.strip().strip("`*#:").strip()
    p = re.sub(r"^(file|path|filepath)\s*[:=]\s*", "", p, flags=re.I).strip("`'\" ")
    p = p.replace("\\", "/")
    return p[2:] if p.startswith("./") else p


def parse_edits(reply: str) -> List[Edit]:
    """Every SEARCH/REPLACE block in a model reply, with the file path named on the line before it (a code-fence
    line in between is skipped). Blocks without a path, or with an unterminated section, are ignored."""
    lines = (reply or "").replace("\r\n", "\n").split("\n")
    edits: List[Edit] = []
    i = 0
    while i < len(lines):
        if lines[i].strip() != _SEARCH:
            i += 1
            continue
        path = ""
        for back in range(i - 1, max(-1, i - 4), -1):
            cand = lines[back].strip()
            if not cand or cand.startswith("```"):
                continue
            path = _clean_path(cand)
            break
        try:
            mid = next(j for j in range(i + 1, len(lines)) if lines[j].strip() == _DIVIDER)
            end = next(j for j in range(mid + 1, len(lines)) if lines[j].strip() == _REPLACE)
        except StopIteration:
            break
        if path and " " not in path:
            edits.append(Edit(path=path, search="\n".join(lines[i + 1:mid]), replace="\n".join(lines[mid + 1:end])))
        i = end + 1
    return edits


def _indent(line: str) -> str:
    return line[: len(line) - len(line.lstrip())]


def _find(lines: List[str], search: List[str], key) -> List[int]:
    want = [key(s) for s in search]
    n = len(want)
    return [i for i in range(len(lines) - n + 1) if [key(x) for x in lines[i:i + n]] == want]


def _apply_one(content: str, search: str, replace: str) -> Tuple[Optional[str], str]:
    """(new content, "") or (None, reason)."""
    count = content.count(search)
    if count == 1:
        return content.replace(search, replace, 1), ""
    if count > 1:
        return None, f"the SEARCH text occurs {count} times; include more surrounding lines so it matches one place"
    lines = content.split("\n")
    s_lines = search.split("\n")
    while s_lines and not s_lines[-1].strip():
        s_lines.pop()
    while s_lines and not s_lines[0].strip():
        s_lines.pop(0)
    if not s_lines:
        return None, "the SEARCH section is blank"
    r_lines = replace.split("\n")
    hits = _find(lines, s_lines, str.rstrip)                    # 1) trailing whitespace ignored
    if len(hits) == 1:
        i = hits[0]
        return "\n".join(lines[:i] + r_lines + lines[i + len(s_lines):]), ""
    if len(hits) > 1:
        return None, f"the SEARCH text matches {len(hits)} places; include more surrounding lines"
    hits = _find(lines, s_lines, str.strip)                     # 2) a uniform indentation offset
    if len(hits) != 1:
        return None, ("the SEARCH text was not found in the file; copy the current lines exactly"
                      if not hits else f"the SEARCH text matches {len(hits)} places; include more surrounding lines")
    i = hits[0]
    first = next(k for k, s in enumerate(s_lines) if s.strip())
    have, had = _indent(lines[i + first]), _indent(s_lines[first])
    if not all((not s.strip()) or s.startswith(had) for s in s_lines) or not all(
            (not t.strip()) or t.startswith(had) or not had for t in r_lines):
        return None, "the SEARCH text matches only with different relative indentation; copy the lines exactly"
    shifted = [(have + t[len(had):]) if t.strip() else t for t in r_lines]
    return "\n".join(lines[:i] + shifted + lines[i + len(s_lines):]), ""


def apply_edits(files: Dict[str, str], edits: List[Edit]) -> EditResult:
    """Apply edits to an in-memory copy of `files`. A file is created only by an edit with an empty SEARCH; every
    edit that cannot be applied is reported and changes nothing."""
    work: Dict[str, str] = {}
    result = EditResult()
    for e in edits:
        current = work.get(e.path, files.get(e.path))
        if not e.search.strip():
            if current is None:
                work[e.path] = e.replace if e.replace.endswith("\n") else e.replace + "\n"
                result.applied += 1
            elif not current.strip():
                work[e.path] = e.replace
                result.applied += 1
            else:
                result.errors.append(f"{e.path}: an empty SEARCH only creates a new file, and this file exists")
            continue
        if current is None:
            result.errors.append(f"{e.path}: no such file in the project")
            continue
        new, reason = _apply_one(current, e.search, e.replace)
        if new is None:
            result.errors.append(f"{e.path}: {reason}")
            continue
        work[e.path] = new
        result.applied += 1
    result.changed = {p: c for p, c in work.items() if c != files.get(p)}
    return result


def feedback(result: EditResult) -> str:
    """What to tell the model when some of its edits did not apply."""
    return ("Some edits could not be applied:\n" + "\n".join(f"- {e}" for e in result.errors)
            + "\nResend ALL your edits (not only the failed ones), with SEARCH text copied exactly from the "
              "current file.")
