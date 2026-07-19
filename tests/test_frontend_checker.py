import pytest
from pathlib import Path
from backend.validation.frontend_checker import FrontendChecker


def test_frontend_checker_valid_component(tmp_path):
    checker = FrontendChecker()
    (tmp_path / "frontend").mkdir()

    # Valid React JSX component
    (tmp_path / "frontend/Home.jsx").write_text("""import React from 'react';
function Home() {
    return <h1>Hello</h1>;
}
export default Home;
""")

    res = checker.validate(tmp_path)
    assert res.score == 100.0
    assert len(res.errors) == 0
    assert res.metadata["js_files_scanned"] == 1


def test_frontend_checker_broken_component(tmp_path):
    checker = FrontendChecker()
    (tmp_path / "frontend").mkdir()

    # React JSX component with multiple unbalanced tags (>5)
    (tmp_path / "frontend/Home.jsx").write_text("""import React from 'react';
function Home() {
    return (
        <div>
        <div>
        <div>
        <div>
        <div>
        <div>
        <h1>Hello
    );
}
export default Home;
""")

    res = checker.validate(tmp_path)
    assert any("malformed JSX structure" in err for err in res.errors)
