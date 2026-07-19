import json
import re
import logging
from pathlib import Path
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import List, Dict, Any

_logger = logging.getLogger("aiforge.performance")

class ReflectionService:
    """
    Manages persistent storage of reflection outputs, lesson merging, 
    prompt optimization, similarity searches, and trend metrics.
    """

    def __init__(self, memory_dir: Path = None) -> None:
        if memory_dir is None:
            # Default to backend/memory relative to file path
            self.memory_dir = Path(__file__).resolve().parents[1] / "memory"
        else:
            self.memory_dir = memory_dir
            
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.lessons_path = self.memory_dir / "lessons.json"
        self.history_path = self.memory_dir / "reflection_history.json"
        
        # Initialize files if missing or empty
        self._init_files()

    def _init_files(self) -> None:
        for p in [self.lessons_path, self.history_path]:
            if not p.exists() or p.stat().st_size == 0:
                with open(p, "w", encoding="utf-8") as f:
                    json.dump([], f)

    # --- File IO ---
    def load_lessons(self) -> List[Dict[str, Any]]:
        try:
            with open(self.lessons_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            _logger.error(f"Failed to load lessons.json: {exc}")
            return []

    def save_lessons(self, lessons: List[Dict[str, Any]]) -> None:
        try:
            with open(self.lessons_path, "w", encoding="utf-8") as f:
                json.dump(lessons, f, indent=2)
            _logger.info("Lessons loaded and updated successfully")
        except Exception as exc:
            _logger.error(f"Failed to save lessons: {exc}")

    def load_history(self) -> List[Dict[str, Any]]:
        try:
            with open(self.history_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            _logger.error(f"Failed to load reflection_history.json: {exc}")
            return []

    def save_history(self, history: List[Dict[str, Any]]) -> None:
        try:
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)
            _logger.info("Reflection history updated successfully")
        except Exception as exc:
            _logger.error(f"Failed to save reflection history: {exc}")

    # --- Lesson Merging & Similarity Search ---
    def compute_similarity(self, str_a: str, str_b: str) -> float:
        """
        Calculates string match ratio using SequenceMatcher for robust zero-dependency comparison.
        """
        return SequenceMatcher(None, str_a.lower(), str_b.lower()).ratio()

    def add_lessons(self, new_lessons: List[Dict[str, str]], threshold: float = 0.70) -> None:
        """
        Extracts and merges lessons permanently, tracking count frequencies and last-seen timestamps.
        """
        existing_lessons = self.load_lessons()
        now_str = datetime.now(timezone.utc).date().isoformat()
        
        for new_l in new_lessons:
            prob = new_l.get("problem", "").strip()
            less = new_l.get("lesson", "").strip()
            if not prob or not less:
                continue
                
            # Find best match based on problem similarity
            best_match = None
            max_sim = 0.0
            
            for item in existing_lessons:
                sim = self.compute_similarity(prob, item.get("problem", ""))
                if sim > max_sim:
                    max_sim = sim
                    best_match = item
                    
            if max_sim >= threshold and best_match:
                # Merge similar lessons, increase frequency count
                best_match["count"] = best_match.get("count", 1) + 1
                best_match["last_seen"] = now_str
                # Keep the longer, more informative lesson text
                if len(less) > len(best_match.get("lesson", "")):
                    best_match["lesson"] = less
                _logger.info(f"Merged lesson for issue similar to: {best_match['problem']}")
            else:
                # Create a new lesson entry
                existing_lessons.append({
                    "problem": prob,
                    "lesson": less,
                    "count": 1,
                    "last_seen": now_str
                })
                _logger.info(f"Registered new lesson: {prob}")
                
        self.save_lessons(existing_lessons)

    # --- History Logging ---
    def add_history_record(
        self,
        project_name: str,
        reflection_score: float,
        bugs_found: int,
        tests_passed: int,
        recommendations: List[str],
        execution_time: float
    ) -> None:
        history = self.load_history()
        history.append({
            "project_name": project_name,
            "reflection_score": reflection_score,
            "generation_date": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "bugs_found": bugs_found,
            "tests_passed": tests_passed,
            "recommendations": recommendations,
            "execution_time": round(execution_time, 4)
        })
        self.save_history(history)

    # --- Prompt Optimizer ---
    def optimize_prompt(self, original_prompt: str) -> str:
        """
        Enriches user prompts automatically with lessons matching keywords.
        """
        lessons = self.load_lessons()
        if not lessons:
            return original_prompt
            
        matching_directives = []
        prompt_words = set(re.findall(r"\b\w+\b", original_prompt.lower()))
        
        # Match keywords in the lessons
        for item in lessons:
            prob_text = item.get("problem", "").lower()
            less_text = item.get("lesson", "").lower()
            # check overlaps
            matched = False
            for word in prompt_words:
                if len(word) >= 3 and (word in prob_text or word in less_text):
                    matched = True
                    break
            
            if matched:
                matching_directives.append(item.get("lesson"))
                
        if matching_directives:
            _logger.info("Prompt optimized using matched memory lessons")
            directives_str = "\n".join(f"- {d}" for d in matching_directives[:5]) # limit to top 5 matches
            optimized = f"""{original_prompt}

=== Production Quality Best Practices (Learned from previous runs) ===
{directives_str}
"""
            return optimized
            
        return original_prompt

    # --- Dashboard Trend Metrics ---
    def get_dashboard_metrics(self) -> dict:
        """
        Tracks knowledge statistics, repeated mistakes, and score improvements.
        """
        history = self.load_history()
        lessons = self.load_lessons()
        
        total_projects = len(history)
        knowledge_size = len(lessons)
        
        if total_projects == 0:
            return {
                "projects_generated": 0,
                "reflection_score": 0.0,
                "knowledge_size": knowledge_size,
                "top_lessons": [],
                "common_bugs": [],
                "improvement_rate": 0.0,
                "average_test_score": 0.0
            }
            
        avg_score = round(sum(h.get("reflection_score", 85.0) for h in history) / total_projects, 1)
        avg_test_passed = round(sum(h.get("tests_passed", 0) for h in history) / total_projects, 1)
        
        # Calculate improvement rate (last 5 scores slope or first vs last)
        improvement_rate = 0.0
        if total_projects >= 2:
            improvement_rate = round(history[-1].get("reflection_score", 0.0) - history[0].get("reflection_score", 0.0), 1)

        # Get top lessons based on count
        sorted_lessons = sorted(lessons, key=lambda x: x.get("count", 1), reverse=True)
        top_lessons = [item.get("lesson") for item in sorted_lessons[:5]]
        common_bugs = [item.get("problem") for item in sorted_lessons[:5]]

        return {
            "projects_generated": total_projects,
            "reflection_score": avg_score,
            "knowledge_size": knowledge_size,
            "top_lessons": top_lessons,
            "common_bugs": common_bugs,
            "improvement_rate": improvement_rate,
            "average_test_score": avg_test_passed
        }
