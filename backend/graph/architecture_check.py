"""
Architecture completeness check (restored from the Day 11 workflow).

The architect is asked for a fixed set of Markdown sections; this reports which are missing so
the architecture approval can show an incomplete design instead of passing it silently.
"""

import re
from typing import List, Tuple

REQUIRED_SECTIONS: List[str] = [
    "High-Level Architecture",
    "Database Schema",
    "API Specifications",
    "Folder Structure",
    "Development Roadmap",
    "Task Breakdown",
    "Dependency Graph",
    "Risk Analysis",
    "Testing Strategy",
    "Deployment Strategy",
]


def validate_architecture_sections(architecture: str) -> Tuple[bool, List[str]]:
    """(complete, missing section names), matching Markdown headings case-insensitively."""
    headings = {
        re.sub(r"^[\d.\s]+", "", m.group(1)).strip().lower()
        for m in re.finditer(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", architecture or "", re.M)
    }
    missing = [s for s in REQUIRED_SECTIONS if not any(s.lower() in h for h in headings)]
    return not missing, missing


def enforce_architecture_sections(architecture: str) -> str:
    """The architecture, with a quality-check note appended when sections are missing."""
    complete, missing = validate_architecture_sections(architecture)
    if complete:
        return architecture
    return (
        f"{architecture.rstrip()}\n\n## Architecture Quality Check\n"
        f"Status: Incomplete\nMissing sections:\n" + "\n".join(f"- {s}" for s in missing) + "\n"
    )
