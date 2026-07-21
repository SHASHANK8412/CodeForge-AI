import sqlite3
import logging
from pathlib import Path
from typing import Dict, Any, List

from backend.knowledge.memory.project_memory import ProjectMemory
from backend.knowledge.graph.knowledge_graph import KnowledgeGraph
from backend.knowledge.graph.graph_builder import GraphBuilder
from backend.knowledge.graph.graph_query import GraphQuery
from backend.knowledge.graph.graph_visualizer import GraphVisualizer
from backend.knowledge.extractor.project_extractor import ProjectExtractor
from backend.knowledge.extractor.api_extractor import APIExtractor
from backend.knowledge.extractor.pattern_extractor import PatternExtractor
from backend.knowledge.embeddings.similarity import SimilarityMatcher
from backend.knowledge.recommendation.recommender import Recommender

_logger = logging.getLogger("aiforge.knowledge")

class KnowledgeManager:
    """
    Coordinates all SRE Long-Term Memory, Graph Builder, and recommendation services.
    """

    def __init__(self, db_path: str = None) -> None:
        self.memory = ProjectMemory(db_path)
        self.graph = KnowledgeGraph(db_path)
        self.graph_builder = GraphBuilder(self.graph)
        self.graph_query = GraphQuery(self.graph)
        self.graph_visualizer = GraphVisualizer(self.graph)

        self.project_extractor = ProjectExtractor()
        self.api_extractor = APIExtractor()
        self.pattern_extractor = PatternExtractor()
        self.similarity_matcher = SimilarityMatcher()
        self.recommender = Recommender()

    def register_completed_project(self, workspace_path: str) -> Dict[str, Any]:
        """
        Extracts metadata, endpoints, and patterns from workspace, and updates SRE graph nodes.
        """
        _logger.info(f"Registering completed project workspace: {workspace_path}")
        
        # 1. Scrape metadata
        meta = self.project_extractor.extract_metadata(workspace_path)
        patterns = self.pattern_extractor.extract_patterns(workspace_path)
        
        # Merge patterns into frameworks keywords list for query index mapping
        meta["frameworks"] = ",".join(meta.get("frameworks", []) + patterns)
        
        # 2. Save project summary
        self.memory.save_project(meta)

        # 3. Graph additions
        frontend = meta.get("frontend", "")
        backend = meta.get("backend", "")
        db = meta.get("database", "")

        if frontend and backend:
            self.graph_builder.add_relationship(frontend, backend, "uses")
        if backend and db:
            self.graph_builder.add_relationship(backend, db, "uses")

        # 4. Experience additions
        for tech in meta.get("frameworks", "").split(","):
            if tech:
                self.memory.update_experience(tech, points=5)

        # 5. Export JSON visualization
        self.graph_visualizer.export_graph_json()

        return meta

    def query_prior_experience(self, prompt: str) -> Dict[str, Any]:
        """
        Similarity searches past projects, bugs, and architectures to pre-seed Planner templates.
        """
        _logger.info(f"Querying prior SRE experience database for: {prompt}")

        # Fetch projects list
        projects = []
        with self.memory._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects")
            for row in cursor.fetchall():
                p = dict(row)
                p["folder_structure"] = json.loads(p.get("folder_structure", "[]")) if p.get("folder_structure") else []
                projects.append(p)

        # TF-IDF keyword match
        matches = self.similarity_matcher.get_top_matches(prompt, projects, limit=3)
        
        # Recommendations
        recs = self.recommender.recommend_architecture(prompt)

        # Fetch matching bugs
        bugs = self.memory.get_all_bugs()

        return {
            "similar_projects_found": len(matches) > 0,
            "similar_projects": matches,
            "architecture_recommendations": recs,
            "frequent_bugs_warnings": bugs[:5]
        }

import json
