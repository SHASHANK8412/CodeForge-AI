import pytest
import tempfile
import json
from pathlib import Path
from backend.knowledge.knowledge_manager import KnowledgeManager

def test_project_memory(tmp_path):
    db_file = tmp_path / "knowledge.db"
    manager = KnowledgeManager(db_path=str(db_file))
    
    # Save project metadata
    project = {
        "name": "E-Commerce App",
        "type": "Web Application",
        "frameworks": ["React", "FastAPI"],
        "frontend": "React",
        "backend": "FastAPI",
        "database": "SQLite",
        "auth": "JWT",
        "folder_structure": ["frontend", "backend"],
        "deployment": "Docker"
    }
    manager.memory.save_project(project)

    # Experience updates
    score = manager.memory.update_experience("React", points=5)
    assert score == 5

    # Retrieve score
    assert manager.memory.get_experience_score("React") == 5

def test_knowledge_graph_traversal(tmp_path):
    db_file = tmp_path / "knowledge.db"
    manager = KnowledgeManager(db_path=str(db_file))

    # Add stack edges
    manager.graph_builder.add_relationship("React", "FastAPI", "uses")
    manager.graph_builder.add_relationship("FastAPI", "SQLite", "uses")

    # Breadth-first Traversal
    bfs_path = manager.graph_query.traverse_graph("React")
    assert bfs_path == ["react", "fastapi", "sqlite"]

    # Shortest path route
    shortest = manager.graph_query.shortest_path("React", "SQLite")
    assert shortest == ["react", "fastapi", "sqlite"]

    # Dependency Lookup deep
    deps = manager.graph_query.get_dependencies_deep("React")
    assert deps == ["fastapi", "sqlite"]

    # Cycle prevention DAG verification
    added = manager.graph_builder.add_relationship("SQLite", "React", "uses")
    # Should prevent because React -> FastAPI -> SQLite already exists, creating a path SQLite -> React creates a cycle!
    assert added is False

def test_bug_memory_hash(tmp_path):
    db_file = tmp_path / "knowledge.db"
    manager = KnowledgeManager(db_path=str(db_file))

    bug = {
        "description": "SQL Injection vulnerability in auth router",
        "category": "Security",
        "root_cause": "Raw query string injection",
        "fix": "Use DB binding parameters",
        "severity": "Critical",
        "prevention": "Never interpolate raw strings"
    }
    
    # Save once
    manager.memory.save_bug(bug)
    
    # Save duplicate to test unique hashing constraints
    manager.memory.save_bug(bug)

    all_bugs = manager.memory.get_all_bugs()
    assert len(all_bugs) == 1
    assert all_bugs[0]["severity"] == "Critical"

def test_similarity_matchmaking(tmp_path):
    db_file = tmp_path / "knowledge.db"
    manager = KnowledgeManager(db_path=str(db_file))

    # Seed past project
    manager.memory.save_project({
        "name": "SocialApp",
        "type": "API Service",
        "frameworks": ["FastAPI", "PostgreSQL"],
        "frontend": "React",
        "backend": "FastAPI",
        "database": "PostgreSQL",
        "auth": "JWT",
        "folder_structure": ["backend"],
        "deployment": "Docker"
    })

    # Similarity search
    res = manager.query_prior_experience("Build a Social API using FastAPI and PostgreSQL")
    assert res["similar_projects_found"] is True
    assert res["similar_projects"][0]["project_name"] == "SocialApp"
    assert res["similar_projects"][0]["estimated_reuse_pct"] >= 30

def test_recommender(tmp_path):
    db_file = tmp_path / "knowledge.db"
    manager = KnowledgeManager(db_path=str(db_file))

    recs = manager.recommender.recommend_architecture("Build secure chat application with banking APIs")
    stack = recs["recommended_stack"]
    
    assert "PostgreSQL" in stack
    assert "JWT Stateless Authentication" in stack
    assert "WebSockets" in stack
