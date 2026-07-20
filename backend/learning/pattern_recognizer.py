import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from backend.learning.learning_memory import LearningMemory

_logger = logging.getLogger("aiforge.learning")

class PatternRecognizer:
    """
    Analyzes historical project runs in learning memory to identify repeated bugs,
    common frameworks, build times, and exports summaries to patterns.json.
    """

    def __init__(self, memory: LearningMemory, patterns_dir: str = None) -> None:
        self.memory = memory
        if patterns_dir is None:
            patterns_dir = str(Path(__file__).parent / "patterns")
        self.patterns_dir = Path(patterns_dir)
        self.patterns_dir.mkdir(parents=True, exist_ok=True)

    def analyze_patterns(self) -> Dict[str, Any]:
        """
        Scans all summaries, compiles pattern stats, and saves patterns.json.
        """
        summaries = self.memory.get_all_summaries()
        if not summaries:
            # Return template defaults if no histories are built yet
            default_patterns = {
                "frequent_stacks": [
                    {
                        "stack": "React + FastAPI",
                        "average_score": 95.0,
                        "deployment_success_rate": 98.0,
                        "average_build_time_seconds": 42.0
                    }
                ],
                "repeated_mistakes": {},
                "common_technologies": []
            }
            self._save_patterns(default_patterns)
            return default_patterns

        stack_scores: Dict[str, List[float]] = {}
        stack_build_times: Dict[str, List[float]] = {}
        stack_success_count: Dict[str, int] = {}
        mistake_counters: Dict[str, int] = {}
        tech_counters: Dict[str, int] = {}

        for summary in summaries:
            techs = sorted(summary.get("technologies", []))
            stack_key = " + ".join(techs) if techs else "Generic Stack"

            score = summary.get("final_score", 90.0)
            build_time = summary.get("performance", {}).get("generation_time", 40.0)
            success = 1 if score >= 80.0 else 0

            # Accumulate
            if stack_key not in stack_scores:
                stack_scores[stack_key] = []
                stack_build_times[stack_key] = []
                stack_success_count[stack_key] = 0

            stack_scores[stack_key].append(score)
            stack_build_times[stack_key].append(build_time)
            stack_success_count[stack_key] += success

            # Track technologies
            for tech in techs:
                tech_counters[tech] = tech_counters.get(tech, 0) + 1

            # Track mistakes
            for mistake in summary.get("mistakes", []):
                mistake_counters[mistake] = mistake_counters.get(mistake, 0) + 1

        # Format frequent stacks
        frequent_stacks = []
        for stack, scores in stack_scores.items():
            avg_score = sum(scores) / len(scores)
            avg_build = sum(stack_build_times[stack]) / len(scores)
            success_rate = (stack_success_count[stack] / len(scores)) * 100.0
            
            frequent_stacks.append({
                "stack": stack,
                "average_score": round(avg_score, 1),
                "deployment_success_rate": round(success_rate, 1),
                "average_build_time_seconds": round(avg_build, 1)
            })

        # Sort technology counters
        common_technologies = sorted(tech_counters.keys(), key=lambda k: tech_counters[k], reverse=True)

        patterns = {
            "frequent_stacks": frequent_stacks,
            "repeated_mistakes": mistake_counters,
            "common_technologies": common_technologies
        }

        self._save_patterns(patterns)
        return patterns

    def _save_patterns(self, data: Dict[str, Any]) -> None:
        file_path = self.patterns_dir / "patterns.json"
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            _logger.error(f"Failed to save SRE patterns JSON: {str(e)}")
