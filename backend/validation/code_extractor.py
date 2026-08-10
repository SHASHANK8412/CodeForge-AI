"""
AIForge Code Block Extractor
============================
Parses multi-file code blocks from LLM agent text outputs.
Supports formats:
```python
# filepath: backend/auth.py
...
```

```jsx
// filename: frontend/src/components/TodoList.jsx
...
```

```sql
-- filepath: database/schema.sql
...
```

Also handles unannotated single code blocks with fallbacks based on agent ownership.
"""
from __future__ import annotations

import re
from typing import Dict, Any


# ─────────────────────────────────────────────
# Agent Ownership Mapping
# ─────────────────────────────────────────────

AGENT_DEFAULT_PATHS = {
    "backend": "backend/main.py",
    "frontend": "frontend/src/App.jsx",
    "database": "database/schema.sql",
    "testing": "tests/test_main.py",
    "documentation": "README.md",
}


def extract_files_from_agent_output(text: str, agent_name: str = "", default_filename: str = "") -> Dict[str, str]:
    """Scans LLM output text for multi-file markdown code blocks with filepath annotations.

    If no annotations are found but code blocks exist, uses default_filename or agent's default path.
    Returns a dict mapping relative_filepath -> file_content.
    """
    files: Dict[str, str] = {}
    if not text or not text.strip():
        return files

    # Pattern 1: # filepath: path/to/file.ext \n ```language ... ```
    prefix_pattern = re.compile(
        r"(?:#|//|--|\*)\s*(?:filepath|filename|file|path):\s*([^\n\r]+)\s*\n\s*```[a-zA-Z0-9_\-]*\s*\n(.*?)(?:```)",
        re.DOTALL | re.IGNORECASE
    )

    for match in prefix_pattern.finditer(text):
        filepath = match.group(1).strip()
        content = match.group(2)
        filepath = re.sub(r"^[#/\-\*\s]+", "", filepath).strip()
        normalized_path = filepath.replace("\\", "/").strip("/")
        if normalized_path and content:
            files[normalized_path] = content

    # Pattern 2: ```language \n # filepath: path/to/file.ext \n ... ```
    annotated_pattern = re.compile(
        r"```[a-zA-Z0-9_\-]*\s*\n"
        r"(?:#|//|--|\*)\s*(?:filepath|filename|file|path):\s*([^\n\r]+)\s*\n"
        r"(.*?)"
        r"\n```",
        re.DOTALL | re.IGNORECASE
    )

    for match in annotated_pattern.finditer(text):
        filepath = match.group(1).strip()
        content = match.group(2)

        # Clean filepath string
        filepath = re.sub(r"^[#/\-\*\s]+", "", filepath).strip()
        normalized_path = filepath.replace("\\", "/").strip("/")

        if normalized_path and content:
            files[normalized_path] = content

    # If annotated blocks were found, return them
    if files:
        return files

    # Fallback 1: look for unannotated code blocks
    unannotated_pattern = re.compile(
        r"```[a-zA-Z0-9_\-]*\s*\n(.*?)\n```",
        re.DOTALL
    )

    blocks = unannotated_pattern.findall(text)
    default_path = default_filename or AGENT_DEFAULT_PATHS.get(agent_name.lower(), "")

    if blocks and default_path:
        longest_block = max(blocks, key=len)
        files[default_path] = longest_block.strip()
    elif not blocks and default_path and text.strip():
        # Fallback 2: raw code string without markdown fencing
        files[default_path] = text.strip()

    return files



def extract_all_agent_files(state: Dict[str, Any]) -> Dict[str, str]:
    """Combines extracted files across all specialized agent outputs in WorkflowState."""
    all_files: Dict[str, str] = {}

    agents = [
        ("frontend", state.get("frontend", "") or state.get("frontend_code", "")),
        ("backend", state.get("backend", "") or state.get("backend_code", "")),
        ("database", state.get("database", "") or state.get("database_code", "") or state.get("database_schema", "")),
        ("testing", state.get("tests", "") or state.get("testing_code", "")),
        ("documentation", state.get("documentation", "") or state.get("documentation_files", "")),
    ]

    for agent_name, output in agents:
        if isinstance(output, dict):
            # Already a path -> content map
            for path, content in output.items():
                clean = path.replace("\\", "/").lstrip("/")
                all_files[clean] = content
        elif isinstance(output, str) and output.strip():
            extracted = extract_files_from_agent_output(output, agent_name=agent_name)
            all_files.update(extracted)

    return all_files
