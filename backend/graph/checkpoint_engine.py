"""
AIForge LangGraph State Checkpointing Engine
============================================
Persists workflow state snapshots across pipeline execution stages.
Enables multi-step agent workflows to resume from exact state after server restarts or failures.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

_logger = logging.getLogger("aiforge.graph.checkpoint_engine")

CHECKPOINTS_DIR = Path(__file__).resolve().parent.parent / "data" / "checkpoints"


class LangGraphCheckpointEngine:
    """
    State checkpointing engine for workflow state persistence and recovery.
    """

    def __init__(self):
        CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(self, session_id: str, stage_name: str, state_data: Dict[str, Any]) -> str:
        """
        Saves workflow state snapshot to disk.
        """
        ckpt_path = CHECKPOINTS_DIR / f"{session_id}_{stage_name}.json"
        try:
            with open(ckpt_path, "w", encoding="utf-8") as f:
                json.dump({
                    "session_id": session_id,
                    "stage": stage_name,
                    "state": state_data
                }, f, indent=2, default=str)
            _logger.info(f"LangGraphCheckpointEngine: Saved checkpoint '{ckpt_path.name}'")
            return str(ckpt_path)
        except Exception as e:
            _logger.error(f"LangGraphCheckpointEngine: Failed to save checkpoint: {e}")
            return ""

    def load_latest_checkpoint(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Loads the most recent state checkpoint for a session.
        """
        ckpts = sorted(CHECKPOINTS_DIR.glob(f"{session_id}_*.json"))
        if not ckpts:
            return None

        latest_ckpt = ckpts[-1]
        try:
            with open(latest_ckpt, "r", encoding="utf-8") as f:
                data = json.load(f)
            _logger.info(f"LangGraphCheckpointEngine: Loaded latest checkpoint '{latest_ckpt.name}'")
            return data.get("state")
        except Exception as e:
            _logger.error(f"LangGraphCheckpointEngine: Failed to load checkpoint: {e}")
            return None


global_checkpoint_engine = LangGraphCheckpointEngine()
