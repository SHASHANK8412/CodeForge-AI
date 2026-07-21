import pytest
from backend.plugins.permissions import PermissionValidator

def test_permissions_sandbox():
    # Only allow filesystem reading
    validator = PermissionValidator(allowed_permissions=["filesystem:read"])
    
    assert validator.has_permission("filesystem:read") is True
    assert validator.has_permission("network:outbound") is False

    assert validator.verify_permissions(["filesystem:read"]) is True
    assert validator.verify_permissions(["network:outbound"]) is False
