"""The final packaging step completes the assembled project instead of rebuilding a second copy."""
from backend.generators.project_generator import ProjectGenerator


def test_final_structure_keeps_repairs_and_uses_the_assembled_folder(tmp_path):
    assembled = tmp_path / "Notes_App"
    assembled.mkdir()
    state = {
        # Raw agent output still contains the bug the debug/patch loop fixed.
        "backend": "```python\n# filepath: backend/main.py\nraise SystemExit('bug')\n```",
        "files": {"backend/main.py": "app = 'patched'\n"},
    }

    project_dir, _ = ProjectGenerator().generate_project_structure("Notes App", state, project_dir=assembled)

    assert project_dir == assembled
    assert (assembled / "backend" / "main.py").read_text(encoding="utf-8") == "app = 'patched'\n"
    assert not (tmp_path / "Notes App").exists()
