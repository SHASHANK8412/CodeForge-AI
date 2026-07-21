import re
import logging

_logger = logging.getLogger("aiforge.tools")

class CommandValidator:
    """
    Security validation layer gating whitelisted and blacklisted terminal commands.
    """

    def __init__(self) -> None:
        self.blacklist = [
            r'rm\s+-rf', r'sudo\s+rm', r'mkfs', r'shutdown', r'reboot', r'poweroff',
            r'del\s+/f', r'format\s+[a-zA-Z]:', r'chmod\s+777', r':\(\)\{\s*:\s*\|\s*:\s*&\s*\}\s*;'
        ]

    def validate_command(self, cmd_str: str) -> bool:
        c = cmd_str.strip()
        
        # 1. Blacklist check
        for pattern in self.blacklist:
            if re.search(pattern, c, re.IGNORECASE):
                _logger.warning(f"Security Warning: Command blacklisted -> '{c}'")
                return False

        # 2. Command injection checks (avoid chaining operators unless explicitly structured)
        if ";" in c or "&&" in c or "||" in c or "|" in c:
            # Simple allow whitelisted chains (like pytest -v | grep or git add && git commit)
            whitelisted_chains = ["git", "pytest", "npm", "pip", "python"]
            if not any(word in c for word in whitelisted_chains):
                _logger.warning(f"Security Warning: Command contains potential injection operators -> '{c}'")
                return False

        return True
