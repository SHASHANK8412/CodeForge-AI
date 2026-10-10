"""
Regression: a double-wrapped code block left '```python' as the first line of a generated
backend/main.py (seen in a real project), so the app could not even be imported.
"""
from backend.validation.code_extractor import _strip_stray_fences
from backend.validation.code_extractor import extract_files_from_agent_output as extract

CODE = "from fastapi import FastAPI\napp = FastAPI()"


def test_double_wrapped_block_has_no_fence_lines():
    out = "backend/main.py:\n```python\n```python\n" + CODE + "\n```\n```"
    assert extract(out, agent_name="backend") == {"backend/main.py": CODE}


def test_unclosed_raw_block_is_cleaned():
    assert extract("```python\n" + CODE + "\n", agent_name="backend") == {"backend/main.py": CODE}


def test_normal_blocks_are_unchanged():
    out = "### backend/main.py\n```python\n" + CODE + "\n```\n### backend/db.py\n```python\nDB = 1\n```"
    assert extract(out) == {"backend/main.py": CODE, "backend/db.py": "DB = 1"}


def test_markdown_files_keep_their_fences():
    readme = "```bash\nuvicorn main:app\n```"
    assert _strip_stray_fences("README.md", readme) == readme
    assert _strip_stray_fences("main.py", readme) == "uvicorn main:app"
    assert _strip_stray_fences("main.py", "x = 1\n\n") == "x = 1\n"
