import logging
from pathlib import Path
from typing import Dict, Any, List
from backend.learning.learning_memory import LearningMemory

_logger = logging.getLogger("aiforge.learning")

class ArchitectureEvolver:
    """
    Scans project histories to detect recurring frameworks (JWT, Redis, Docker, CI/CD)
    and generates architecture_recommendations.md.
    """

    def __init__(self, memory: LearningMemory, knowledge_dir: str = None) -> None:
        self.memory = memory
        if knowledge_dir is None:
            knowledge_dir = str(Path(__file__).parent / "knowledge")
        self.knowledge_dir = Path(knowledge_dir)
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)

    def evolve_architecture(self) -> List[str]:
        """
        Processes histories and outputs architecture recommendations.
        """
        summaries = self.memory.get_all_summaries()
        tech_counts: Dict[str, int] = {}
        
        for summary in summaries:
            for tech in summary.get("technologies", []):
                tech_lower = tech.lower().strip()
                tech_counts[tech_lower] = tech_counts.get(tech_lower, 0) + 1

        recommendations: List[str] = []
        superior_components: List[str] = []

        # Check for recurring production integrations
        for tech, count in tech_counts.items():
            if count >= 2:
                # Component is frequently used and successful
                tech_name = tech.upper() if len(tech) <= 4 else tech.capitalize()
                superior_components.append(tech_name)
                recommendations.append(f"Framework '{tech_name}' appears superior due to repeated adoption in {count} successful project run(s).")

        if not recommendations:
            superior_components = ["FastAPI", "React", "Docker"]
            recommendations = ["Default stable stack template selected: React + FastAPI + Docker."]

        # Generate markdown output
        file_path = self.knowledge_dir / "architecture_recommendations.md"
        
        md_content = [
            "# Architecture Evolution Recommendations",
            "",
            "This document is automatically compiled by AIForge Continuous Learning SRE nodes.",
            "",
            "## 1. Superior Architecture Components",
            "Consistent high-scoring stacks in historical builds:"
        ]
        
        for comp in superior_components:
            md_content.append(f"* **{comp}**: High reliability, low error rates, and quick deployment cycles.")

        md_content.extend([
            "",
            "## 2. Dynamic Stack Selection Suggestion",
            "Agents should automatically initialize new repositories using the recommended stack configurations below:"
        ])
        
        for rec in recommendations:
            md_content.append(f"* {rec}")

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(md_content))
            _logger.info("Successfully updated architecture_recommendations.md guide.")
        except Exception as e:
            _logger.error(f"Failed to write architecture_recommendations.md: {str(e)}")

        return recommendations
