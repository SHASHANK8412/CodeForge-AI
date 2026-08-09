"""
AIForge Communication Logger
============================
Logs inter-agent message exchanges and events to file `logs/communication.log` and maintains in-memory history.
"""

import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.communication.protocol import AgentMessage

_logger = logging.getLogger("aiforge.communication")


class CommunicationLogger:
    """
    Manages communication log files and history.
    """

    def __init__(self, log_file_path: Optional[str] = None) -> None:
        if log_file_path is None:
            log_dir = Path(__file__).resolve().parents[2] / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file_path = str(log_dir / "communication.log")

        self.log_file = Path(log_file_path)
        self.log_history: List[Dict[str, Any]] = []

    def log_message(self, message: AgentMessage) -> str:
        formatted_time = time.strftime("%H:%M:%S", time.localtime(message.timestamp))
        log_line = f"{formatted_time} {message.sender} → {message.receiver} [{message.type}:{message.priority}] {message.payload.get('summary', '')}"
        
        entry = {
            "time": formatted_time,
            "timestamp": message.timestamp,
            "sender": message.sender,
            "receiver": message.receiver,
            "type": message.type,
            "priority": message.priority,
            "log_line": log_line,
            "message_id": message.id
        }
        self.log_history.append(entry)

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_line + "\n")
        except Exception as e:
            _logger.error(f"Failed writing to communication.log: {e}")

        return log_line

    def get_logs(self, agent: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        results = self.log_history
        if agent:
            a_lower = agent.lower()
            results = [
                l for l in results
                if a_lower in l["sender"].lower() or a_lower in l["receiver"].lower()
            ]
        return results[-limit:]


global_communication_logger = CommunicationLogger()
