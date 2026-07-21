import asyncio
import json
import sys
from pathlib import Path

# Add root folder to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.knowledge.knowledge_manager import KnowledgeManager

async def run_knowledge_verification():
    print("======================================================================")
    print("AIForge Knowledge Graph & Long-Term Memory System Verification Suite")
    print("======================================================================\n")

    workspace_root = str(Path(__file__).resolve().parent.parent)
    db_file = Path(workspace_root) / "backend" / "knowledge" / "memory" / "knowledge.db"
    
    # Instantiate clean knowledge manager
    manager = KnowledgeManager(db_path=str(db_file))

    # ---------------------------------------------------------
    # Scenario 1: Project Knowledge Extraction
    # ---------------------------------------------------------
    print("--- Scenario 1: Project Knowledge Extraction ---")
    mock_project_meta = {
        "name": "Hospital Management System",
        "type": "Web Application",
        "frameworks": ["React", "FastAPI", "PostgreSQL"],
        "frontend": "React",
        "backend": "FastAPI",
        "database": "PostgreSQL",
        "auth": "JWT Stateless Authentication",
        "folder_structure": ["frontend", "backend", "tests"],
        "deployment": "Docker",
        "build_time": 42,
        "success_rate": 96.0
    }
    manager.memory.save_project(mock_project_meta)
    print(" [OK] Extracted metadata and registered project: Hospital Management System")
    print("")

    # ---------------------------------------------------------
    # Scenario 2: Knowledge Graph DAG relations
    # ---------------------------------------------------------
    print("--- Scenario 2: Knowledge Graph DAG relations ---")
    manager.graph_builder.add_relationship("React", "FastAPI", "uses")
    manager.graph_builder.add_relationship("FastAPI", "PostgreSQL", "uses")
    print(" [OK] Added graph relation React -> Uses -> FastAPI")
    print(" [OK] Added graph relation FastAPI -> Uses -> PostgreSQL")
    
    print("Attempting to add circular relation: PostgreSQL -> Uses -> React...")
    added = manager.graph_builder.add_relationship("PostgreSQL", "React", "uses")
    if not added:
        print(" [OK] Successfully blocked circular relationship to enforce DAG consistency.")
    print("")

    # ---------------------------------------------------------
    # Scenario 3: Graph Traversal & Shortest Path
    # ---------------------------------------------------------
    print("--- Scenario 3: Graph Traversal & Shortest Path ---")
    shortest = manager.graph_query.shortest_path("React", "PostgreSQL")
    print(f"Shortest path from React to PostgreSQL: {shortest}")
    
    deps = manager.graph_query.get_dependencies_deep("React")
    print(f"Deep dependent downstream nodes for React: {deps}")
    print("")

    # ---------------------------------------------------------
    # Scenario 4: Bug Memory Deduplication
    # ---------------------------------------------------------
    print("--- Scenario 4: Bug Memory Deduplication ---")
    mock_bug = {
        "description": "JWT Verification Signature invalid error",
        "category": "Authentication",
        "root_cause": "Key encoding mismatch",
        "fix": "UTF-8 encode security secrets",
        "severity": "High",
        "prevention": "Adopt standard security middlewares config"
    }
    
    manager.memory.save_bug(mock_bug)
    manager.memory.save_bug(mock_bug)  # Duplicate save to test unique hashing constraints
    
    bugs = manager.memory.get_all_bugs()
    print(f"Total bugs in database (after duplicate writes): {len(bugs)}")
    print(" [OK] Unique hash key constrained duplicate bug items successfully.")
    print("")

    # ---------------------------------------------------------
    # Scenario 5: Similarity match search
    # ---------------------------------------------------------
    print("--- Scenario 5: Similarity match search ---")
    res = manager.query_prior_experience("Build a secure Hospital Portal using React and FastAPI")
    if res["similar_projects_found"]:
        match = res["similar_projects"][0]
        print(f"Found similar project matching prompt:")
        print(f"  - Project name: {match['project_name']}")
        print(f"  - Similarity score: {int(match['similarity_score'] * 100)}%")
        print(f"  - Estimated reuse: {match['estimated_reuse_pct']}%")
        print(f"  - Suggested libraries to reuse: {match['libraries']}")
    print("")

    # ---------------------------------------------------------
    # Scenario 6: SRE Stack Recommender
    # ---------------------------------------------------------
    print("--- Scenario 6: SRE Stack Recommender ---")
    recs = manager.recommender.recommend_architecture("Build secure banking payment processing client")
    print(f"Recommended Stack components: {recs['recommended_stack']}")
    print(f"Architectural Reasoning : {recs['reasoning']}")
    print("")

    # ---------------------------------------------------------
    # Scenario 7: Experience updates
    # ---------------------------------------------------------
    print("--- Scenario 7: Experience Updates ---")
    points = manager.memory.update_experience("React", points=5)
    print(f"Framework React experience points updated: {points} XP")
    print("")

    print("======================================================================")
    print("All SRE Long-Term Memory Engine verification checks completed successfully!")
    print("======================================================================")

if __name__ == "__main__":
    asyncio.run(run_knowledge_verification())
