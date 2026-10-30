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


def test_evolution_report(tmp_path):
    from backend.knowledge.memory.evolution_report import EvolutionReportGenerator
    db_file = tmp_path / "knowledge.db"
    
    # An empty memory reports nothing it does not have (these used to be the constants 20 and 96.2).
    data = EvolutionReportGenerator(db_path=str(db_file)).generate_report()
    assert data["total_projects"] == 0 and data["most_common_bugs"] == []
    assert data["average_review_score"] is None and data["test_pass_rate"] is None
    assert (tmp_path / "reports" / "self_evolution_report.md").exists()

    # With recorded projects and bugs, the report counts them.
    import sqlite3
    with sqlite3.connect(str(db_file)) as con:
        con.execute("CREATE TABLE projects (frontend TEXT, backend TEXT, database_name TEXT)")
        con.execute("CREATE TABLE bugs (category TEXT, description TEXT)")
        con.execute("CREATE TABLE lessons (worked TEXT, failed TEXT)")
        con.executemany("INSERT INTO projects VALUES (?, ?, ?)", [("React", "FastAPI", "SQLite")] * 2 + [("Vue", "Express", None)])
        con.executemany("INSERT INTO bugs VALUES (?, ?)", [("auth", "x"), ("auth", "y"), ("sql", "z")])
        con.execute("INSERT INTO lessons VALUES ('fast', 'skipped migrations')")
    data = EvolutionReportGenerator(db_path=str(db_file)).generate_report()
    assert data["total_projects"] == 3 and data["most_common_architecture"] == "React + FastAPI + SQLite"
    assert data["most_common_bugs"][0] == {"bug": "auth", "count": 2}
    assert data["recommendations"] == ["Avoid: skipped migrations"]
    assert "not recorded" in (tmp_path / "reports" / "self_evolution_report.md").read_text(encoding="utf-8")


def test_semantic_query(tmp_path):
    from backend.knowledge.graph.graph_query import GraphQuery
    db_file = tmp_path / "knowledge.db"
    manager = KnowledgeManager(db_path=str(db_file))
    
    # Insert mock nodes
    manager.graph.add_node("jwt", "library")
    manager.graph.add_node("auth_controller", "component")
    manager.graph.add_node("main.py", "file")
    manager.graph.add_edge("main.py", "jwt", "depends")

    query_engine = GraphQuery(manager.graph)
    results = query_engine.semantic_query("Where is authentication implemented?")
    assert len(results) > 0
    assert any(r["node"] in ("jwt", "auth_controller") for r in results)

    results_dep = query_engine.semantic_query("Which files depend on jwt.py?")
    assert len(results_dep) > 0
    assert results_dep[0]["node"] == "main.py"
