import pytest
from backend.plugins.dependency import DependencyResolver

def test_semver_matching():
    resolver = DependencyResolver()
    
    # == matches
    assert resolver.matches_version("1.2.0", "==", "1.2.0") is True
    assert resolver.matches_version("1.2.0", "==", "1.2.1") is False

    # >= matches
    assert resolver.matches_version("2.1.0", ">=", "2.0.0") is True
    assert resolver.matches_version("1.5.2", ">=", "1.6.0") is False

    # <= matches
    assert resolver.matches_version("1.0.0", "<=", "1.1.0") is True
    assert resolver.matches_version("1.2.0", "<=", "1.0.0") is False
