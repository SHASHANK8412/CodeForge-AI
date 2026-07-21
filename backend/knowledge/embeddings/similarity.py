import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.knowledge")

class SimilarityMatcher:
    """
    Computes keyword matching overlaps and ranks similar past project architectures.
    """

    def __init__(self) -> None:
        pass

    def calculate_similarity_score(self, prompt: str, project: Dict[str, Any]) -> float:
        """
        Calculates similarity overlap score (0.0 to 1.0) between prompt and a past project metadata.
        """
        prompt_words = set(prompt.lower().split())
        
        # Build keywords list from the target past project
        project_keywords = set()
        
        name = project.get("name", "").lower()
        project_type = project.get("type", "").lower()
        frameworks = [f.lower() for f in project.get("frameworks", "").split(",") if f]

        project_keywords.add(name)
        project_keywords.add(project_type)
        for f in frameworks:
            project_keywords.add(f)

        # Count word overlaps
        overlap = len(prompt_words.intersection(project_keywords))
        if not prompt_words:
            return 0.0

        score = overlap / len(prompt_words)
        return min(1.0, score)

    def get_top_matches(
        self,
        query: str,
        projects: List[Dict[str, Any]],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Ranks project list based on similarity scores and appends reuse estimates.
        """
        matches = []
        for p in projects:
            score = self.calculate_similarity_score(query, p)
            if score > 0.0:
                # Estimate reuse percentage based on similarity score
                reuse_pct = int(score * 85.0 + 10.0)
                matches.append({
                    "project_name": p["name"],
                    "similarity_score": score,
                    "reusable_components": ["Authentication" if score > 0.4 else "Folder layout"],
                    "architecture_match": p["backend"],
                    "libraries": p["frameworks"],
                    "folder_structure": p["folder_structure"],
                    "estimated_reuse_pct": min(95, reuse_pct)
                })

        # Sort matches by score descending
        matches = sorted(matches, key=lambda x: x["similarity_score"], reverse=True)
        return matches[:limit]
