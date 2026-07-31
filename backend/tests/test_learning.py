"""
Unit tests for Day 44 LearningAgent and KnowledgeExtractor
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import unittest
from backend.agents.learning_agent import LearningAgent
from backend.services.knowledge_extractor import KnowledgeExtractor


class TestLearning(unittest.TestCase):

    def setUp(self):
        self.agent = LearningAgent()
        self.extractor = KnowledgeExtractor()

    def test_learning_agent_analysis(self):
        project = {
            "name": "E-Commerce App",
            "prompt": "Create an e-commerce platform",
            "project_files": {
                "frontend/src/App.jsx": "import React from 'react'; export default function App() {}",
                "backend/main.py": "from fastapi import FastAPI\napp = FastAPI()",
                "database/schema.sql": "CREATE TABLE products (id SERIAL PRIMARY KEY);"
            },
            "quality_score": 96.0
        }
        res = self.agent.analyze_completed_project(project)
        self.assertGreaterEqual(res["patterns_extracted"], 2)
        self.assertGreaterEqual(len(res["lessons_learned"]), 1)

    def test_knowledge_extraction(self):
        files = {
            "backend/main.py": "@app.get('/api/items')\ndef items(): pass",
            "frontend/src/Card.jsx": "export default function Card() {}",
            "database/schema.sql": "CREATE TABLE users (id INT);"
        }
        know = self.extractor.extract_knowledge(files)
        self.assertGreaterEqual(len(know["api_patterns"]), 1)
        self.assertGreaterEqual(len(know["ui_components"]), 1)
        self.assertGreaterEqual(len(know["database_schemas"]), 1)


if __name__ == "__main__":
    unittest.main()
