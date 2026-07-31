"""
AIForge Knowledge Extractor Service (Day 44)
============================================
Extracts structured technical assets (API patterns, DB schemas, UI components, folder trees, prompts, error fixes, testing strategies) from project artifacts.
"""

import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.services.knowledge_extractor")


class KnowledgeExtractor:
    """
    Service for extracting 7 core knowledge categories from generated software projects.
    """

    def extract_knowledge(
        self,
        project_files: Dict[str, str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        metadata = metadata or {}
        prompt = metadata.get("prompt", "")

        api_patterns = []
        db_schemas = []
        ui_components = []
        folder_structures = []
        prompts = [prompt] if prompt else []
        error_resolution_pairs = metadata.get("error_resolutions", [])
        testing_strategies = []

        # Analyze files
        for path, content in project_files.items():
            # 1. API Patterns
            if "main.py" in path or "routes" in path or "api" in path:
                if "@app." in content or "router" in content or "FastAPI" in content:
                    api_patterns.append({
                        "file": path,
                        "category": "API_PATTERN",
                        "summary": "FastAPI REST Endpoint Handler",
                        "snippet": content[:300]
                    })

            # 2. Database Schemas
            if "schema.sql" in path or "models.py" in path or "database" in path:
                if "CREATE TABLE" in content or "Base = declarative_base" in content or "Column" in content:
                    db_schemas.append({
                        "file": path,
                        "category": "DATABASE_SCHEMA",
                        "summary": "Database Schema Definition",
                        "snippet": content[:300]
                    })

            # 3. UI Components
            if path.endswith((".jsx", ".tsx")):
                if "export default" in content or "function" in content:
                    ui_components.append({
                        "file": path,
                        "category": "UI_COMPONENT",
                        "summary": f"React Component ({path.split('/')[-1]})",
                        "snippet": content[:300]
                    })

            # 4. Testing Strategies
            if "test_" in path or "_test." in path:
                testing_strategies.append({
                    "file": path,
                    "category": "TESTING_STRATEGY",
                    "summary": "Automated Unit/Integration Test Suite",
                    "snippet": content[:300]
                })

        # Folder structure hierarchy representation
        folder_structures = list(set(path.split("/")[0] for path in project_files.keys()))

        extracted = {
            "api_patterns": api_patterns,
            "database_schemas": db_schemas,
            "ui_components": ui_components,
            "folder_structures": folder_structures,
            "reusable_prompts": prompts,
            "error_resolution_pairs": error_resolution_pairs,
            "testing_strategies": testing_strategies
        }

        _logger.info(f"KnowledgeExtractor: Extracted {len(api_patterns)} APIs, {len(ui_components)} UIs, {len(db_schemas)} Schemas")
        return extracted


global_knowledge_extractor = KnowledgeExtractor()
