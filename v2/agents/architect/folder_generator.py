"""
AIForge V2 – Target Folder Tree Generator
=========================================
Generates modular directory structures for target software projects.
"""

from typing import List


class FolderTreeGenerator:

    def generate_tree(self, project_name: str) -> List[str]:
        return [
            "backend/",
            "backend/api/",
            "backend/routes/",
            "backend/models/",
            "backend/services/",
            "backend/core/",
            "frontend/",
            "frontend/src/",
            "frontend/src/components/",
            "frontend/src/pages/",
            "frontend/src/services/",
            "agents/",
            "database/",
            "memory/",
            "vector_store/",
            "docker/",
            "scripts/",
            "tests/",
            "docs/"
        ]


global_folder_generator = FolderTreeGenerator()
