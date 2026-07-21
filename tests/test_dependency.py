import pytest
from backend.plugins.dependency import DependencyResolver, DependencyException

def test_circular_dependency_detection():
    resolver = DependencyResolver()
    
    # 1. Circular path
    graph_cycle = {
        "A": ["B"],
        "B": ["C"],
        "C": ["A"]
    }
    with pytest.raises(DependencyException, match="Circular Dependency"):
        resolver.check_circular_dependencies(graph_cycle)

    # 2. Standard path
    graph_clean = {
        "A": ["B"],
        "B": ["C"],
        "C": []
    }
    resolving_order = resolver.check_circular_dependencies(graph_clean)
    assert resolving_order == ["C", "B", "A"]
