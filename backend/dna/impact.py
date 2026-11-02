"""
AIForge Day 15 — Impact Analysis, Traceability & AI Explanation Engine
========================================================================
Performs:
- Transitive Impact Analysis (affected files, components, APIs, DB models, tests, features)
- Requirement Traceability Checks
- Dead Code Detection
- Circular Dependency Detection
- Risk Score Calculation (LOW, MEDIUM, HIGH, CRITICAL)
- Concise AI Explanations
"""

import logging
from typing import Dict, Any, List, Set, Optional, Tuple

from backend.dna.models import (
    EngineeringDNAGraph, GraphNode, GraphEdge, NodeKind,
    ImpactAnalysisResult, RequirementTraceResult, DeadCodeFinding,
    CircularDependencyFinding
)
from backend.dna.repository import global_graph_repository

_logger = logging.getLogger("aiforge.dna.impact")


class ImpactEngine:
    """
    Analyzes dependency graph impact, requirement tracing, dead code, and circular references.
    """

    def analyze_change_impact(
        self,
        project_id: str,
        node_id: str,
        change_type: str = "modify"
    ) -> ImpactAnalysisResult:
        graph = global_graph_repository.get_latest_graph(project_id)
        if not graph:
            return ImpactAnalysisResult(
                node_id=node_id,
                change_type=change_type,
                explanation="Engineering DNA graph unavailable for project."
            )

        start_node = next((n for n in graph.nodes if n.id == node_id or n.label == node_id), None)
        target_id = start_node.id if start_node else node_id

        affected_ids = global_graph_repository.find_affected_nodes(project_id, target_id)
        nodes_by_id = {n.id: n for n in graph.nodes}

        aff_files: Set[str] = set()
        aff_comps: Set[str] = set()
        aff_apis: Set[str] = set()
        aff_dbs: Set[str] = set()
        aff_tests: Set[str] = set()
        aff_feats: Set[str] = set()

        sec_critical = False

        for nid in affected_ids:
            n = nodes_by_id.get(nid)
            if not n:
                continue

            if n.security_critical:
                sec_critical = True

            if n.file_path:
                aff_files.add(n.file_path)

            if n.kind == NodeKind.COMPONENT:
                aff_comps.add(n.label)
            elif n.kind == NodeKind.API:
                aff_apis.add(n.label)
            elif n.kind in (NodeKind.DATABASE_MODEL, NodeKind.DATABASE_TABLE):
                aff_dbs.add(n.label)
            elif n.kind == NodeKind.TEST:
                aff_tests.add(n.label)
            elif n.kind == NodeKind.FEATURE:
                aff_feats.add(n.label)

        # Risk scoring
        sec_impact = "CRITICAL" if sec_critical else "LOW"
        total_affected = len(affected_ids)

        if sec_critical or total_affected >= 15:
            risk = "CRITICAL"
            rec = "Requires comprehensive regression testing and security review before deploying."
        elif total_affected >= 8:
            risk = "HIGH"
            rec = "High impact change. Verify API contracts and run full unit test suite."
        elif total_affected >= 3:
            risk = "MEDIUM"
            rec = "Moderate impact change. Run component unit tests."
        else:
            risk = "LOW"
            rec = "Low impact change. Safe to apply patch."

        expl = (
            f"Modifying '{start_node.label if start_node else node_id}' impacts {len(aff_files)} files, "
            f"{len(aff_apis)} APIs, {len(aff_dbs)} database models, and {len(aff_tests)} tests. "
            f"Security impact is {sec_impact}."
        )

        return ImpactAnalysisResult(
            node_id=target_id,
            change_type=change_type,
            affected_files=sorted(list(aff_files)),
            affected_components=sorted(list(aff_comps)),
            affected_apis=sorted(list(aff_apis)),
            affected_database_objects=sorted(list(aff_dbs)),
            affected_tests=sorted(list(aff_tests)),
            affected_features=sorted(list(aff_feats)),
            security_impact=sec_impact,
            risk_score=risk,
            confidence=0.95,
            recommendation=rec,
            explanation=expl
        )

    def trace_requirements(self, project_id: str) -> List[RequirementTraceResult]:
        graph = global_graph_repository.get_latest_graph(project_id)
        if not graph:
            return []

        req_nodes = [n for n in graph.nodes if n.kind == NodeKind.REQUIREMENT]
        results: List[RequirementTraceResult] = []

        for req in req_nodes:
            outgoing = [e.target for e in graph.edges if e.source == req.id]
            nodes_by_id = {n.id: n for n in graph.nodes}

            comps = [nodes_by_id[target].label for target in outgoing if target in nodes_by_id and nodes_by_id[target].kind == NodeKind.COMPONENT]
            apis = [nodes_by_id[target].label for target in outgoing if target in nodes_by_id and nodes_by_id[target].kind == NodeKind.API]
            dbs = [nodes_by_id[target].label for target in outgoing if target in nodes_by_id and nodes_by_id[target].kind in (NodeKind.DATABASE_MODEL, NodeKind.DATABASE_TABLE)]
            tests = [nodes_by_id[target].label for target in outgoing if target in nodes_by_id and nodes_by_id[target].kind == NodeKind.TEST]

            has_impl = len(comps) > 0 or len(apis) > 0 or len(dbs) > 0
            status = "IMPLEMENTED" if has_impl else "UNIMPLEMENTED"
            cov = 100.0 if has_impl else 0.0

            results.append(
                RequirementTraceResult(
                    requirement_id=req.id,
                    text=req.label,
                    status=status,
                    components=comps,
                    apis=apis,
                    database_tables=dbs,
                    tests=tests,
                    coverage_percent=cov
                )
            )

        return results

    def detect_dead_code(self, project_id: str) -> List[DeadCodeFinding]:
        graph = global_graph_repository.get_latest_graph(project_id)
        if not graph:
            return []

        # Target nodes called/used by other functions, classes, components, APIs or tests
        non_file_target_ids = {e.target for e in graph.edges if not e.source.startswith("file:")}
        dead_findings: List[DeadCodeFinding] = []

        for n in graph.nodes:
            if n.kind in (NodeKind.FUNCTION, NodeKind.CLASS) and n.id not in non_file_target_ids:
                if "main" not in n.label.lower() and "app" not in n.label.lower() and not n.label.startswith("test_"):
                    dead_findings.append(
                        DeadCodeFinding(
                            node_id=n.id,
                            kind=n.kind,
                            file_path=n.file_path or "unknown",
                            name=n.label,
                            reason="No incoming function calls or tests detected in codebase graph."
                        )
                    )

        return dead_findings

    def detect_circular_dependencies(self, project_id: str) -> List[CircularDependencyFinding]:
        graph = global_graph_repository.get_latest_graph(project_id)
        if not graph:
            return []

        adj: Dict[str, List[str]] = {}
        for e in graph.edges:
            if e.source not in adj:
                adj[e.source] = []
            adj[e.source].append(e.target)

        cycles: List[List[str]] = []
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def dfs(node: str, path: List[str]):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path)
                elif neighbor in rec_stack:
                    cycle_start_idx = path.index(neighbor)
                    cycle_path = path[cycle_start_idx:] + [neighbor]
                    if len(cycle_path) > 2 and cycle_path not in cycles:
                        cycles.append(cycle_path)

            path.pop()
            rec_stack.remove(node)

        for n in graph.nodes:
            if n.id not in visited:
                dfs(n.id, [])

        findings: List[CircularDependencyFinding] = []
        nodes_by_id = {n.id: n.label for n in graph.nodes}
        for cyc in cycles:
            clean_labels = [nodes_by_id.get(nid, nid) for nid in cyc]
            findings.append(CircularDependencyFinding(cycle=clean_labels))

        return findings

    def explain_node(self, project_id: str, node_id: str) -> str:
        graph = global_graph_repository.get_latest_graph(project_id)
        if not graph:
            return "Engineering DNA graph unavailable."

        node = next((n for n in graph.nodes if n.id == node_id or n.label == node_id), None)
        if not node:
            return f"Node '{node_id}' not found in project graph."

        deps = global_graph_repository.get_dependencies(project_id, node.id)
        rev_deps = global_graph_repository.get_dependents(project_id, node.id)

        dep_labels = [d.label for d in deps]
        rev_labels = [r.label for r in rev_deps]

        return (
            f"'{node.label}' ({node.kind}) in '{node.file_path or 'root'}'. "
            f"It depends on {len(deps)} components ({', '.join(dep_labels[:3]) or 'none'}) "
            f"and is used by {len(rev_deps)} callers ({', '.join(rev_labels[:3]) or 'none'}). "
            f"Security status: {'SECURITY CRITICAL' if node.security_critical else 'NORMAL'}."
        )


global_impact_engine = ImpactEngine()
