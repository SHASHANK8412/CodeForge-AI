import pytest
import json
from pathlib import Path
from backend.project_intelligence.intelligence_manager import ProjectIntelligenceManager

def test_intelligence_full_pipeline(tmp_path):
    # Setup temporary layout to scan
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    
    # Write Python file
    py_code = """
\"\"\"
User profile database model module.
\"\"\"
import os
from sqlalchemy import Column, Integer, ForeignKey
from fastapi import FastAPI

app = FastAPI()

class User:
    __tablename__ = "users"
    id = Column(Integer)

class Post:
    __tablename__ = "posts"
    user_id = Column(Integer, ForeignKey("users.id"))

@app.get("/api/users")
def get_users():
    return []
"""
    (workspace / "models.py").write_text(py_code, encoding="utf-8")

    # Write JS component file
    js_code = """
import React from 'react';
import Sidebar from './Sidebar';

function App() {
    fetch('/api/users');
    return <Sidebar />;
}
export default App;
"""
    (workspace / "App.jsx").write_text(js_code, encoding="utf-8")

    # Write Sidebar component file
    sidebar_code = """
function Sidebar() {
    return <div>Sidebar</div>;
}
export default Sidebar;
"""
    (workspace / "Sidebar.jsx").write_text(sidebar_code, encoding="utf-8")

    # Run Analyzer
    memory_path = tmp_path / "memory"
    manager = ProjectIntelligenceManager(workspace_path=str(workspace), memory_path=str(memory_path))
    results = manager.run_full_analysis()

    # Assert all 7 file outputs exist
    assert (memory_path / "project_graph.json").exists()
    assert (memory_path / "dependency_graph.json").exists()
    assert (memory_path / "component_tree.json").exists()
    assert (memory_path / "api_map.json").exists()
    assert (memory_path / "architecture.json").exists()
    assert (memory_path / "impact_analysis.json").exists()
    assert (memory_path / "dead_code_report.json").exists()

    # Verify component tree matches hierarchy
    with open(memory_path / "component_tree.json", "r") as f:
        data = json.load(f)
        assert "Sidebar" in data["component_hierarchy"]["App"]

    # Verify API matching resolved
    with open(memory_path / "api_map.json", "r") as f:
        data = json.load(f)
        assert len(data["resolved_mappings"]) > 0
        assert data["resolved_mappings"][0]["route_matched"] == "/api/users"
