import logging
from pathlib import Path
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.learning")

class BestPracticesGenerator:
    """
    Extracts successful folder layouts, API structures, naming rules,
    and updates the master best_practices.md file.
    """

    def __init__(self, knowledge_dir: str = None) -> None:
        if knowledge_dir is None:
            knowledge_dir = str(Path(__file__).parent / "knowledge")
        self.knowledge_dir = Path(knowledge_dir)
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        self._initialize_defaults()

    def _initialize_defaults(self) -> None:
        file_path = self.knowledge_dir / "best_practices.md"
        if not file_path.exists():
            default_practices = """# AIForge Engineering Best Practices

Master guidelines compiled from successful project builds.

## 1. Folder Structure Conventions
* Organize components under `frontend/src/components/` and routing controllers in `backend/routes/`.
* Maintain a clean test suite under `tests/`.

## 2. API Design & Security
* Design asynchronous route endpoints using standard FastAPI views.
* Enforce JWT validation policies on all administrative interfaces.

## 3. Testing Strategy
* Run automated verification scans with pytest prior to compiling builds.
"""
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(default_practices)
            except Exception as e:
                _logger.error(f"Failed to create default best practices file: {str(e)}")

    def update_best_practices(self, project_summary: Dict[str, Any]) -> str:
        """
        Appends new insights from a successful run to best_practices.md.
        """
        file_path = self.knowledge_dir / "best_practices.md"
        
        # Simple extraction
        techs = project_summary.get("technologies", [])
        practices = project_summary.get("best_practices", {})
        
        folder_convention = practices.get("folder_structure", ["Standardized workspace layers"])
        sec_practices = practices.get("security_practices", ["Standard CORS restrictions"])
        api_design = practices.get("api_design", ["Asynchronous FastAPI controllers"])
        
        new_practices_block = f"""
## Project Insight: {project_summary.get('project', 'Generic Project')}
* **Framework Stack**: {", ".join(techs)}
* **Folder Layout**: {", ".join(folder_convention)}
* **Security Protocols**: {", ".join(sec_practices)}
* **API Schema**: {", ".join(api_design)}
* **Score**: {project_summary.get('final_score')}%
"""
        try:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(new_practices_block)
            _logger.info("Successfully updated global best_practices.md guide.")
            
            # Read and return full contents
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            _logger.error(f"Failed to update best_practices.md: {str(e)}")
            return ""
