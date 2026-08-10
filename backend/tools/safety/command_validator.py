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

        # 2. Strict Command injection checks (block operators ; && || | ` $)
        injection_operators = [";", "&&", "||", "|", "`", "$("]
        for op in injection_operators:
            if op in c:
                _logger.warning(f"Security Warning: Command contains forbidden shell operator '{op}' -> '{c}'")
                return False

        return True
