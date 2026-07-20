import logging
from typing import Dict, Any, List, Tuple
from backend.learning.learning_memory import LearningMemory

_logger = logging.getLogger("aiforge.learning")

class ExperienceDatabase:
    """
    Searchable experience database indexing past projects metadata to enable structure,
    schema, and config reusability.
    """

    def __init__(self, memory: LearningMemory) -> None:
        self.memory = memory

    def search_similar_projects(self, user_prompt: str, threshold: float = 0.25) -> List[Tuple[Dict[str, Any], float]]:
        """
        Searches historical project summaries matching prompt tags.
        Returns a list of tuples: (project_summary, match_score).
        """
        prompt_words = set(user_prompt.lower().replace("-", " ").split())
        summaries = self.memory.get_all_summaries()
        matches: List[Tuple[Dict[str, Any], float]] = []

        for summary in summaries:
            score = 0.0
            project_name = summary.get("project", "").lower()
            technologies = [t.lower() for t in summary.get("technologies", [])]
            
            # Calculate match based on keywords overlap
            matches_count = 0
            
            # Check project name matching
            for word in prompt_words:
                if word in project_name:
                    matches_count += 2  # high weight for name matches
                for tech in technologies:
                    if word in tech:
                        matches_count += 1

            if matches_count > 0:
                # Basic match percentage
                score = matches_count / (len(prompt_words) + 1.0)
                if score >= threshold:
                    matches.append((summary, score))

        # Sort by match score descending
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches

    def get_reuse_recommendation(self, user_prompt: str) -> Dict[str, Any]:
        """
        Retrieves reuse specifications (structure, API, authentication) if a match is found.
        """
        matches = self.search_similar_projects(user_prompt)
        if not matches:
            return {"similar_project_found": False}

        best_match, score = matches[0]
        _logger.info(f"Experience match found for prompt '{user_prompt}': {best_match.get('project')} (Score: {score:.2f})")
        
        return {
            "similar_project_found": True,
            "match_score": score,
            "project_name": best_match.get("project"),
            "technologies": best_match.get("technologies"),
            "suggested_folder_structure": best_match.get("best_practices", {}).get("folder_structure", [
                "src/components/", "src/pages/", "backend/routes/", "backend/models/"
            ]),
            "suggested_api_patterns": best_match.get("best_practices", {}).get("api_design", [
                "FastAPI asynchronous views", "Standardized REST endpoints", "GZip compression enabled"
            ]),
            "suggested_auth_schema": best_match.get("best_practices", {}).get("security_practices", [
                "JWT Token validation", "CORS policy restriction"
            ]),
            "suggested_database_schema": best_match.get("best_practices", {}).get("database_schema", "Standardized relational tables"),
            "suggested_deployment_pipeline": best_match.get("deployment_notes", "Docker Hub registries deploy")
        }
