import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="module")
def engine():
    engine = create_engine("sqlite:///test.db")
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()

def test_create_tables(engine):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('users', 'tasks')"))
        tables = [row[0] for row in result]
        assert "users" in tables
        assert "tasks" in tables

def test_insert_user(session):
    session.execute(
        text("INSERT INTO users (username, password_hash) VALUES (:username, :password)"),
        {"username": "testuser", "password": "hashedpass"}
    )
    session.commit()

    result = session.execute(text("SELECT * FROM users WHERE username=:username"), {"username": "testuser"})
    user = result.fetchone()
    assert user is not None