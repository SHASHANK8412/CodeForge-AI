import pytest
from pathlib import Path
from backend.review.patch_applier import PatchApplier


def test_patch_applier_valid_and_invalid(tmp_path):
    applier = PatchApplier()

    code_file = tmp_path / "app.py"
    code_file.write_text("""# Auth service
def login():
    status = 500
    return status
""")

    # 1. Valid patch test
    valid_patch = {
        "file": "app.py",
        "start_line": 3,
        "end_line": 3,
        "replacement": "    status = 200"
    }

    res_valid = applier.apply_patch(tmp_path, valid_patch)
    assert res_valid is True
    
    content = code_file.read_text()
    assert "status = 200" in content
    assert "status = 500" not in content

    # 2. Invalid patch test (Syntax error)
    invalid_patch = {
        "file": "app.py",
        "start_line": 3,
        "end_line": 3,
        "replacement": "    status = === invalid syntax ==="
    }

    res_invalid = applier.apply_patch(tmp_path, invalid_patch)
    assert res_invalid is False

    # Verify rollback was successful and restored the valid state
    content_restored = code_file.read_text()
    assert "status = 200" in content_restored
    assert "invalid syntax" not in content_restored
