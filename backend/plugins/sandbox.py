import time
import logging
from typing import Dict, Any, Callable
from backend.plugins.permissions import PermissionValidator

_logger = logging.getLogger("aiforge.plugins")

class SandboxException(Exception):
    pass

class PluginSandbox:
    """
    Executes plugin execution blocks under restricted execution timers and security constraints.
    """

    def __init__(self, allowed_permissions: list = None, timeout_seconds: float = 5.0) -> None:
        self.validator = PermissionValidator(allowed_permissions)
        self.timeout = timeout_seconds

    def execute_safely(
        self,
        func: Callable[..., Dict[str, Any]],
        context: Dict[str, Any],
        required_perms: list
    ) -> Dict[str, Any]:
        """
        Validates permission scope and executes within safety timeout constraints.
        """
        # 1. Gate permissions
        if not self.validator.verify_permissions(required_perms):
            raise SandboxException("Permission Denied: Plugin requested unauthorized resources.")

        # 2. Run execution timing constraints
        start_time = time.perf_counter()
        
        try:
            # Under simple sandbox simulation, we run python function directly.
            # Timeout checks can be validated via simple delta.
            result = func(context)
            
            elapsed = time.perf_counter() - start_time
            if elapsed > self.timeout:
                raise SandboxException(f"Execution Timeout: Plugin execution exceeded limit ({self.timeout}s)")
                
            return result
        except SandboxException as se:
            raise se
        except Exception as e:
            _logger.error(f"Plugin Sandbox execution crashed: {str(e)}")
            raise SandboxException(f"Sandbox crash error: {str(e)}")
