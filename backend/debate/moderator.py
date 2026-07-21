import logging
from typing import List, Dict, Any

_logger = logging.getLogger("aiforge.debate")

class DebateModerator:
    """
    Moderates debate sessions, detects circular arguments, and summarizes round proposals.
    """

    def __init__(self) -> None:
        pass

    def summarize_round(self, round_num: int, round_opinions: Dict[str, Any]) -> str:
        """
        Summarizes agent proposals in a single round.
        """
        summary_lines = [f"--- SRE Moderator Round {round_num} Summary ---"]
        for agent, op in round_opinions.items():
            choice = op.get("choice", "N/A")
            conf = op.get("confidence", 90.0)
            summary_lines.append(f"* **{agent.capitalize()}**: Proposes '{choice}' (Confidence: {conf}%)")
        
        summary = "\n".join(summary_lines)
        _logger.info(summary)
        return summary

    def detect_circular_discussion(self, rounds_history: List[Dict[str, Any]]) -> bool:
        """
        Flags circular arguments if choices don't shift or alternate endlessly over 3+ rounds.
        """
        if len(rounds_history) < 3:
            return False

        # Extract sequential choices sequence
        sequential_votes = []
        for rd in rounds_history:
            votes = tuple(sorted((k, v.get("choice", "")) for k, v in rd.items()))
            sequential_votes.append(votes)

        # If identical votes pattern repeats consecutively
        if sequential_votes[-1] == sequential_votes[-2] == sequential_votes[-3]:
            _logger.warning("SRE Moderator: Circular/redundant arguments detected. Halting debates round.")
            return True

        return False
