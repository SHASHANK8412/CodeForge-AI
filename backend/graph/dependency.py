import logging
from typing import Dict, List, Set

logger = logging.getLogger("aiforge.graph.dependency")


class DependencyGraph:
    """
    DependencyGraph manages agent execution order and dependencies:
    - Sequential: Planner -> Architect
    - Parallel: Architect -> [Frontend, Backend, Database]
    - Sequential Merge: [Frontend, Backend, Database] -> Reviewer -> Testing -> Documentation -> Export
    """

    DEPENDENCIES: Dict[str, List[str]] = {
        "planner": [],
        "architect": ["planner"],
        "frontend": ["architect"],
        "backend": ["architect"],
        "database": ["architect"],
        "reviewer": ["frontend", "backend", "database"],
        "testing": ["reviewer"],
        "documentation": ["testing"],
        "export": ["documentation"]
    }

    PARALLEL_NODES: List[str] = ["frontend", "backend", "database"]

    @classmethod
    def get_dependencies(cls, agent_name: str) -> List[str]:
        return cls.DEPENDENCIES.get(agent_name, [])

    @classmethod
    def is_ready(cls, agent_name: str, completed_agents: Set[str]) -> bool:
        deps = cls.get_dependencies(agent_name)
        return all(d in completed_agents for d in deps)

    @classmethod
    def get_next_agents(cls, completed_agents: Set[str]) -> List[str]:
        ready = []
        for agent, deps in cls.DEPENDENCIES.items():
            if agent not in completed_agents and all(d in completed_agents for d in deps):
                ready.append(agent)
        return ready
