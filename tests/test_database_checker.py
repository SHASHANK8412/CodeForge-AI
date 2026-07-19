import pytest
from pathlib import Path
from backend.validation.database_checker import DatabaseChecker


def test_database_checker_valid_model(tmp_path):
    checker = DatabaseChecker()
    (tmp_path / "backend").mkdir()

    # Valid SQLAlchemy model
    (tmp_path / "backend/models.py").write_text("""
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
""")

    res = checker.validate(tmp_path)
    assert res.score == 100.0
    assert len(res.errors) == 0
    assert res.metadata["models_scanned"] == 1


def test_database_checker_broken_model(tmp_path):
    checker = DatabaseChecker()
    (tmp_path / "backend").mkdir()

    # Model without primary key
    (tmp_path / "backend/models.py").write_text("""
class User(Base):
    __tablename__ = "users"
    name = Column(String)
""")

    res = checker.validate(tmp_path)
    assert any("no primary_key defined" in err for err in res.errors)
