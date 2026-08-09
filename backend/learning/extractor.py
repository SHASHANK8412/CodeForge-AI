import logging
from typing import Dict, Any, List

logger = logging.getLogger("aiforge.learning.extractor")


class LearningExtractor:
    """
    LearningExtractor extracts reusable architecture patterns, auth flows, database schemas,
    API layouts, and debugging fixes from completed software projects.
    """

    def extract_knowledge(self, project_name: str, project_files: Dict[str, str]) -> Dict[str, Any]:
        """Analyzes generated project files to extract reusable engineering knowledge."""
        extracted_patterns = []

        has_fastapi = any("FastAPI" in code for code in project_files.values())
        has_react = any("React" in code or "export default" in code for code in project_files.values())
        has_jwt = any("jwt" in code.lower() or "token" in code.lower() for code in project_files.values())

        if has_fastapi:
            extracted_patterns.append({
                "category": "Backend APIs",
                "name": f"{project_name} FastAPI Router Pattern",
                "description": "Standard FastAPI Async Router with Pydantic Schema Validation",
                "framework": "FastAPI",
                "tags": ["fastapi", "python", "pydantic", "backend"]
            })

        if has_react:
            extracted_patterns.append({
                "category": "Frontend Components",
                "name": f"{project_name} React Component Layout",
                "description": "Modular React Functional Component with Tailwind Styling",
                "framework": "React",
                "tags": ["react", "jsx", "tailwind", "frontend"]
            })

        if has_jwt:
            extracted_patterns.append({
                "category": "Authentication",
                "name": "JWT Auth Dependency Injection Flow",
                "description": "Secure Bearer Token Verification Middleware",
                "framework": "OAuth2 / JWT",
                "tags": ["jwt", "auth", "security"]
            })

        logger.info(f"LearningExtractor extracted {len(extracted_patterns)} patterns from '{project_name}'")
        return {
            "project_name": project_name,
            "extracted_count": len(extracted_patterns),
            "patterns": extracted_patterns
        }


# Global LearningExtractor Instance
global_learning_extractor = LearningExtractor()
