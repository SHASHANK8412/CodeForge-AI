import json
import pytest
from unittest.mock import patch
from backend.review.patch_generator import PatchGenerator


@pytest.mark.anyio
@patch("backend.review.patch_generator.generate_text_async")
async def test_patch_generator_minimal_changes(mock_gen):
    generator = PatchGenerator()

    # Mock response matching specifications
    mock_gen.return_value = json.dumps({
        "file": "backend/auth.py",
        "start_line": 12,
        "end_line": 12,
        "replacement": "    hashed = bcrypt.hashpw(password)"
    })

    file_content = """# Auth helper
def store_pass():
    password = request.password
    db.save(password)
"""

    patch_obj = await generator.generate_patch(
        file_path="backend/auth.py",
        file_content=file_content,
        proposed_fix="Use bcrypt.hashpw to store hashed passwords"
    )

    assert patch_obj is not None
    assert patch_obj["start_line"] == 12
    assert patch_obj["end_line"] == 12
    assert "bcrypt.hashpw(password)" in patch_obj["replacement"]
    # Verify that the entire file content is NOT returned as the replacement block
    assert "store_pass()" not in patch_obj["replacement"]
