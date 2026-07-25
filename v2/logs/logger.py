"""
AIForge V2 – Enterprise Logging Engine
=====================================
Structured, audit-compliant agent logger capturing:
Timestamp, Agent, Input, Output, Execution Time, Errors, Token Usage, Cost, Retries.
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional

LOG_DIR = Path(__file__).resolve().parent
LOG_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_LOG_FILE = LOG_DIR / "agent_audit.jsonl"

_logger = logging.getLogger("aiforge.v2")
_logger.setLevel(logging.INFO)

if not _logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")
    ch.setFormatter(formatter)
    _logger.addHandler(ch)


class EnterpriseAgentLogger:
    """
    Enterprise Structured Logger for AIForge V2 Agent Actions.
    """

    def __init__(self, log_file: Path = AUDIT_LOG_FILE):
        self.log_file = log_file

    def log_agent_action(
        self,
        agent_name: str,
        input_text: str,
        output_text: str,
        execution_time_ms: float,
        errors: Optional[str] = None,
        tokens_used: int = 0,
        cost_usd: float = 0.0,
        retries: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        record = {
            "timestamp": time.time(),
            "datetime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "agent": agent_name,
            "input_preview": input_text[:200] if input_text else "",
            "output_preview": output_text[:200] if output_text else "",
            "execution_time_ms": round(execution_time_ms, 2),
            "errors": errors or None,
            "tokens_used": tokens_used,
            "cost_usd": round(cost_usd, 6),
            "retries": retries,
            "metadata": metadata or {}
        }

        _logger.info(
            f"AGENT action agent={agent_name} time={record['execution_time_ms']}ms "
            f"tokens={tokens_used} status={'ERROR' if errors else 'SUCCESS'}"
        )

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as exc:
            _logger.error(f"Failed to write agent audit log: {exc}")

        return record


global_v2_logger = EnterpriseAgentLogger()
