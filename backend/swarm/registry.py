"""
Agent capability registry and the Mission Controller's task graph.

Agents are chosen by capability and task kind (never by name). A task no registered agent supports makes
the mission's plan invalid ("unsupported"), as does an unknown dependency or a cycle.
"""

from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from backend.swarm.models import Contract, Task


class AgentSpec(BaseModel):
    id: str
    title: str
    capabilities: List[str]
    task_kinds: List[str]
    inputs: List[str] = Field(default_factory=list)          # artifact kinds it reads
    outputs: List[str] = Field(default_factory=list)         # artifact kinds it produces
    resources: List[str] = Field(default_factory=list)
    limits: Dict[str, str] = Field(default_factory=dict)
    tools: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)


REGISTRY: List[AgentSpec] = [
    AgentSpec(id="mission_controller", title="Mission Controller", capabilities=["planning", "contract_validation"],
              task_kinds=["contract"], inputs=["objective", "contract"], outputs=["contract"],
              tools=["contract schema validation"], limitations=["validates the contract it is given; it does not invent one"]),
    AgentSpec(id="backend_agent", title="Backend Agent", capabilities=["python", "fastapi", "api_implementation"],
              task_kinds=["backend"], inputs=["contract"], outputs=["source_files", "route_inventory"],
              resources=["local coding model"], limits={"files": "backend/** only", "attempts": "2"},
              tools=["coding model (secret lines hidden)", "AST route extraction"],
              limitations=["FastAPI only", "request bodies are read from Pydantic models in the same file"]),
    AgentSpec(id="frontend_agent", title="Frontend Agent", capabilities=["javascript", "api_client"],
              task_kinds=["frontend_client"], inputs=["contract"], outputs=["source_files", "client_calls"],
              resources=["local coding model"], limits={"files": "frontend/src/api/** only", "attempts": "2"},
              tools=["coding model", "fetch-call extraction"],
              limitations=["calls are read from fetch(...) with literal or template URLs"]),
    AgentSpec(id="critical_reviewer", title="Critical Reviewer", capabilities=["review", "requirements_coverage"],
              task_kinds=["review"], inputs=["contract", "route_inventory", "client_calls", "source_files"],
              outputs=["review"], tools=["contract coverage rules", "Security Guardian static analysis"],
              limitations=["rule-based: it does not judge business logic", "an optional model critique is opinion"]),
    AgentSpec(id="integration_agent", title="Integration Agent", capabilities=["integration", "conflict_detection"],
              task_kinds=["integration"], inputs=["source_files", "route_inventory", "client_calls", "contract"],
              outputs=["integration_report"], tools=["isolated workspace", "patch engine", "interface matching"],
              limitations=["matches method, path and request fields; response shapes are not checked yet"]),
    AgentSpec(id="testing_agent", title="Testing Agent", capabilities=["testing", "verification"],
              task_kinds=["verification"], inputs=["integration_report"], outputs=["test_report"],
              resources=["Docker sandbox"], tools=["project tests", "generated contract test", "Security Guardian"],
              limitations=["Performance and Chaos gates are not selected for API-contract missions yet"]),
]
CAPABILITY_OF = {"contract": "contract_validation", "backend": "api_implementation", "frontend_client": "api_client",
                 "review": "review", "integration": "integration", "verification": "verification"}


def assign(task: Task, registry: Optional[List[AgentSpec]] = None) -> Optional[str]:
    for spec in registry or REGISTRY:
        if task.kind in spec.task_kinds and task.capability in spec.capabilities:
            return spec.id
    return None


def validate_graph(tasks: List[Task]) -> List[str]:
    """Unknown dependencies, unassignable tasks and cycles make a plan invalid."""
    errors = []
    ids = {t.id for t in tasks}
    if len(ids) != len(tasks):
        errors.append("duplicate task ids")
    for t in tasks:
        missing = [d for d in t.depends_on if d not in ids]
        if missing:
            errors.append(f"{t.id} depends on unknown task(s) {missing}")
        if t.agent is None:
            errors.append(f"{t.id} ({t.kind}) is unsupported: no registered agent has capability '{t.capability}'")
    graph = {t.id: [d for d in t.depends_on if d in ids] for t in tasks}
    state: Dict[str, int] = {}

    def visit(n: str, path: List[str]) -> Optional[List[str]]:
        state[n] = 1
        for d in graph[n]:
            if state.get(d) == 1:
                return path + [n, d]
            if state.get(d) is None:
                cyc = visit(d, path + [n])
                if cyc:
                    return cyc
        state[n] = 2
        return None
    for n in graph:
        if state.get(n) is None:
            cyc = visit(n, [])
            if cyc:
                errors.append("circular dependency: " + " -> ".join(cyc))
                break
    return errors


def mission_plan(contract: Optional[Contract], include_frontend: bool = True) -> Tuple[List[Task], List[str]]:
    """The Mission Controller's task graph for an API feature: contract, then backend and frontend client in
    parallel, then review, integration and verification."""
    tasks = [
        Task(id="t1", objective="validate the shared API contract", kind="contract", capability="contract_validation",
             inputs=["contract"], outputs=["contract"], acceptance=["every endpoint has a method and a path",
                                                                    "paths start with /", "no duplicate operations"]),
        Task(id="t2", objective="implement the contract's endpoints in FastAPI", kind="backend",
             capability="api_implementation", inputs=["contract"], outputs=["source_files", "route_inventory"],
             depends_on=["t1"], owned_paths=["backend/"], retry_limit=1,
             acceptance=["every contract endpoint is implemented", "the project's tests still pass"],
             required_tests=["project tests"]),
    ]
    if include_frontend:
        tasks.append(Task(id="t3", objective="write the frontend API client for the contract", kind="frontend_client",
                          capability="api_client", inputs=["contract"], outputs=["source_files", "client_calls"],
                          depends_on=["t1"], owned_paths=["frontend/src/api/"], retry_limit=1,
                          acceptance=["one client function per contract endpoint", "no calls outside the contract"]))
    impl = ["t2", "t3"] if include_frontend else ["t2"]
    tasks += [
        Task(id="t4", objective="independently review the contract coverage, assumptions and security", kind="review",
             capability="review", inputs=["contract", "route_inventory", "client_calls", "source_files"],
             outputs=["review"], depends_on=impl, acceptance=["each finding cites the artifact it is based on"]),
        Task(id="t5", objective="integrate the components and resolve interface conflicts", kind="integration",
             capability="integration", inputs=["source_files", "route_inventory", "client_calls", "contract"],
             outputs=["integration_report"], depends_on=impl + ["t4"],
             acceptance=["no file is written by two tasks", "every client call matches a backend route"]),
        Task(id="t6", objective="verify the integrated application", kind="verification", capability="verification",
             inputs=["integration_report"], outputs=["test_report"], depends_on=["t5"],
             acceptance=["project tests pass in the Docker sandbox", "the contract test passes",
                         "no new critical/high security finding"], required_tests=["project tests", "contract test"],
             retry_limit=0),    # a failed mandatory gate is never retried into a pass
    ]
    for t in tasks:
        t.agent = assign(t)
    errors = validate_graph(tasks)
    if contract is None or not contract.endpoints:
        errors.append("the mission needs an API contract with at least one endpoint")
    return tasks, errors
