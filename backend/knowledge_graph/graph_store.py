"""
AIForge Phase 2: Knowledge Graph Engine & Storage Layer
======================================================
Stores and indexes relationship-aware entity nodes, directional edges,
provenance evidence, confidence scores, and multi-hop dependency paths.
"""

import time
import uuid
import json
import logging
from typing import Dict, Any, List, Optional, Set
from enum import Enum
from pydantic import BaseModel, Field
from pathlib import Path

_logger = logging.getLogger("aiforge.knowledge_graph.store")


class EntityType(str, Enum):
    PROJECT = "Project"
    TECHNOLOGY = "Technology"
    SERVICE = "Service"
    DATABASE = "Database"
    API = "API"
    SECURITY_POLICY = "SecurityPolicy"
    VULNERABILITY = "Vulnerability"
    PERSON = "Person"
    ORGANIZATION = "Organization"
    CONCEPT = "Concept"


class RelationType(str, Enum):
    USES = "USES"
    DEPENDS_ON = "DEPENDS_ON"
    CALLS = "CALLS"
    STORES = "STORES"
    AUTHORED_BY = "AUTHORED_BY"
    CONNECTS_TO = "CONNECTS_TO"
    VULNERABLE_TO = "VULNERABLE_TO"
    MITIGATES = "MITIGATES"
    EXPOSES = "EXPOSES"


class KnowledgeNode(BaseModel):
    id: str
    name: str
    entity_type: str = "Technology"
    description: str
    aliases: List[str] = Field(default_factory=list)
    project_id: str = "aiforge-fooddelivery-ai"
    user_id: str = "user_default"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.95
    created_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))


class KnowledgeEdge(BaseModel):
    id: str = Field(default_factory=lambda: f"edge_{uuid.uuid4().hex[:8]}")
    source_id: str
    target_id: str
    relation_type: str = "USES"
    description: Optional[str] = None
    confidence: float = 0.95
    evidence_document: Optional[str] = "RFC-104-Order-Pipeline.md"
    evidence_chunk_ref: Optional[str] = "RFC-104-Order-Pipeline.md:L12-L24"
    valid_from: Optional[str] = "2026-01-01"
    valid_until: Optional[str] = None
    created_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))


INITIAL_NODES = [
    {
        "id": "node_aiforge_app",
        "name": "FoodDelivery AI Engine",
        "entity_type": "Project",
        "description": "Production multi-tier food ordering & automated courier dispatch platform.",
        "aliases": ["FoodDelivery", "Order Engine"],
        "confidence": 1.0
    },
    {
        "id": "node_fastapi",
        "name": "FastAPI Gateway",
        "entity_type": "Service",
        "description": "Asynchronous REST API ingress routing orders, authentication, and payments.",
        "aliases": ["API Gateway", "Backend Server"],
        "confidence": 0.98
    },
    {
        "id": "node_redis_streams",
        "name": "Redis Streams",
        "entity_type": "Technology",
        "description": "High-throughput real-time message bus broadcasting courier GPS coordinate events.",
        "aliases": ["Redis", "Geolocation Stream"],
        "confidence": 0.95
    },
    {
        "id": "node_postgres_db",
        "name": "PostgreSQL Database",
        "entity_type": "Database",
        "description": "Primary transactional ACID relational datastore with serializable write ledger.",
        "aliases": ["Postgres", "SQL Store"],
        "confidence": 0.99
    },
    {
        "id": "node_jwt_auth",
        "name": "RS256 JWT Auth Provider",
        "entity_type": "SecurityPolicy",
        "description": "Decentralized cryptographic asymmetric token signer with customer/courier RBAC.",
        "aliases": ["JWT Auth", "Auth0 Service"],
        "confidence": 0.96
    },
    {
        "id": "node_kafka_event_bus",
        "name": "Apache Kafka",
        "entity_type": "Technology",
        "description": "Enterprise event broker handling topic 'orders.created' for idempotent order orchestration.",
        "aliases": ["Kafka", "Redpanda"],
        "confidence": 0.94
    },
    {
        "id": "node_react_frontend",
        "name": "React Vite Dashboard",
        "entity_type": "Project",
        "description": "Interactive real-time order tracking map with WebSocket live updates.",
        "aliases": ["Frontend UI", "Client App"],
        "confidence": 0.97
    }
]

INITIAL_EDGES = [
    {
        "id": "edge_app_fastapi",
        "source_id": "node_aiforge_app",
        "target_id": "node_fastapi",
        "relation_type": "EXPOSES",
        "description": "FoodDelivery AI exposes public async endpoints via FastAPI Gateway.",
        "evidence_document": "RFC-104-Order-Pipeline.md",
        "evidence_chunk_ref": "RFC-104-Order-Pipeline.md:L12-L24"
    },
    {
        "id": "edge_fastapi_jwt",
        "source_id": "node_fastapi",
        "target_id": "node_jwt_auth",
        "relation_type": "DEPENDS_ON",
        "description": "FastAPI Gateway verifies every inbound request against RS256 JWT Auth Provider.",
        "evidence_document": "RFC-104-Order-Pipeline.md",
        "evidence_chunk_ref": "RFC-104-Order-Pipeline.md:L25-L38"
    },
    {
        "id": "edge_fastapi_kafka",
        "source_id": "node_fastapi",
        "target_id": "node_kafka_event_bus",
        "relation_type": "CONNECTS_TO",
        "description": "FastAPI dispatches order events to Kafka topic 'orders.created'.",
        "evidence_document": "RFC-104-Order-Pipeline.md",
        "evidence_chunk_ref": "RFC-104-Order-Pipeline.md:L40-L55"
    },
    {
        "id": "edge_kafka_redis",
        "source_id": "node_kafka_event_bus",
        "target_id": "node_redis_streams",
        "relation_type": "CALLS",
        "description": "Background dispatch worker consumes Kafka orders and streams to Redis Streams.",
        "evidence_document": "RFC-104-Order-Pipeline.md",
        "evidence_chunk_ref": "RFC-104-Order-Pipeline.md:L60-L75"
    },
    {
        "id": "edge_fastapi_postgres",
        "source_id": "node_fastapi",
        "target_id": "node_postgres_db",
        "relation_type": "STORES",
        "description": "FastAPI persists immutable order ledgers to PostgreSQL with ACID isolation.",
        "evidence_document": "RFC-104-Order-Pipeline.md",
        "evidence_chunk_ref": "RFC-104-Order-Pipeline.md:L80-L95"
    },
    {
        "id": "edge_react_fastapi",
        "source_id": "node_react_frontend",
        "target_id": "node_fastapi",
        "relation_type": "USES",
        "description": "React Frontend communicates with FastAPI via REST and WebSockets.",
        "evidence_document": "RFC-104-Order-Pipeline.md",
        "evidence_chunk_ref": "RFC-104-Order-Pipeline.md:L100-L115"
    }
]


class KnowledgeGraphStore:
    def __init__(self, storage_dir: Optional[str] = None):
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            self.storage_dir = Path(__file__).resolve().parent.parent / "data" / "knowledge_graph"

        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.nodes_file = self.storage_dir / "graph_nodes.json"
        self.edges_file = self.storage_dir / "graph_edges.json"
        self._nodes: Dict[str, KnowledgeNode] = {}
        self._edges: Dict[str, KnowledgeEdge] = {}
        self._load()

    def _load(self):
        try:
            if self.nodes_file.exists() and self.edges_file.exists():
                with open(self.nodes_file, "r", encoding="utf-8") as f:
                    ndata = json.load(f)
                    for n in ndata:
                        node = KnowledgeNode(**n)
                        self._nodes[node.id] = node
                with open(self.edges_file, "r", encoding="utf-8") as f:
                    edata = json.load(f)
                    for e in edata:
                        edge = KnowledgeEdge(**e)
                        self._edges[edge.id] = edge
            else:
                for n in INITIAL_NODES:
                    node = KnowledgeNode(**n)
                    self._nodes[node.id] = node
                for e in INITIAL_EDGES:
                    edge = KnowledgeEdge(**e)
                    self._edges[edge.id] = edge
                self._save()
        except Exception as e:
            _logger.error(f"Error loading Knowledge Graph: {e}")
            for n in INITIAL_NODES:
                node = KnowledgeNode(**n)
                self._nodes[node.id] = node
            for e in INITIAL_EDGES:
                edge = KnowledgeEdge(**e)
                self._edges[edge.id] = edge

    def _save(self):
        try:
            with open(self.nodes_file, "w", encoding="utf-8") as f:
                json.dump([n.model_dump() for n in self._nodes.values()], f, indent=2)
            with open(self.edges_file, "w", encoding="utf-8") as f:
                json.dump([e.model_dump() for e in self._edges.values()], f, indent=2)
        except Exception as e:
            _logger.error(f"Error saving Knowledge Graph: {e}")

    def create_node(self, name: str, entity_type: str = "Technology", description: str = "", aliases: Optional[List[str]] = None, project_id: str = "aiforge-fooddelivery-ai") -> KnowledgeNode:
        # Check alias / entity resolution
        norm_name = name.strip()
        for node in self._nodes.values():
            if node.name.lower() == norm_name.lower() or norm_name.lower() in [a.lower() for a in node.aliases]:
                return node

        node_id = f"node_{uuid.uuid4().hex[:8]}"
        node = KnowledgeNode(
            id=node_id,
            name=norm_name,
            entity_type=entity_type,
            description=description,
            aliases=aliases or [],
            project_id=project_id
        )
        self._nodes[node.id] = node
        self._save()
        return node

    def create_edge(self, source_id: str, target_id: str, relation_type: str = "USES", description: Optional[str] = None, evidence_doc: Optional[str] = None, evidence_ref: Optional[str] = None) -> KnowledgeEdge:
        edge = KnowledgeEdge(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            description=description,
            evidence_document=evidence_doc or "RFC-104-Order-Pipeline.md",
            evidence_chunk_ref=evidence_ref or "RFC-104-Order-Pipeline.md:L12-L24"
        )
        self._edges[edge.id] = edge
        self._save()
        return edge

    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        return self._nodes.get(node_id)

    def get_neighbors(self, node_id: str) -> Dict[str, Any]:
        node = self.get_node(node_id)
        if not node:
            return {"node": None, "incoming": [], "outgoing": []}

        outgoing = []
        incoming = []
        for edge in self._edges.values():
            if edge.source_id == node_id:
                target = self._nodes.get(edge.target_id)
                outgoing.append({"edge": edge, "target_node": target})
            elif edge.target_id == node_id:
                source = self._nodes.get(edge.source_id)
                incoming.append({"edge": edge, "source_node": source})

        return {"node": node, "outgoing": outgoing, "incoming": incoming}

    def find_path(self, start_id: str, end_id: str, max_depth: int = 3) -> List[List[str]]:
        """Breadth-first search for multi-hop relationship paths."""
        if start_id not in self._nodes or end_id not in self._nodes:
            return []

        queue = [[start_id]]
        paths = []
        visited_paths = set()

        while queue:
            current_path = queue.pop(0)
            current_node = current_path[-1]

            if len(current_path) - 1 > max_depth:
                continue

            if current_node == end_id:
                paths.append(current_path)
                continue

            for edge in self._edges.values():
                if edge.source_id == current_node and edge.target_id not in current_path:
                    new_path = list(current_path)
                    new_path.append(edge.target_id)
                    path_key = "->".join(new_path)
                    if path_key not in visited_paths:
                        visited_paths.add(path_key)
                        queue.append(new_path)

        return paths

    def traverse_dependency_tree(self, root_id: str, depth: int = 2) -> Dict[str, Any]:
        """Traverse downstream dependencies up to depth N."""
        root = self.get_node(root_id)
        if not root:
            return {}

        visited: Set[str] = set([root_id])
        levels = {0: [root.model_dump()]}

        current_nodes = [root_id]
        for d in range(1, depth + 1):
            next_nodes = []
            levels[d] = []
            for n_id in current_nodes:
                for edge in self._edges.values():
                    if edge.source_id == n_id and edge.target_id not in visited:
                        target = self._nodes.get(edge.target_id)
                        if target:
                            visited.add(edge.target_id)
                            next_nodes.append(edge.target_id)
                            levels[d].append({
                                "node": target.model_dump(),
                                "via_edge": edge.model_dump()
                            })
            current_nodes = next_nodes

        return {"root": root.model_dump(), "depth": depth, "levels": levels}

    def get_full_graph(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        nodes = list(self._nodes.values())
        edges = list(self._edges.values())
        if project_id:
            nodes = [n for n in nodes if n.project_id == project_id]
            node_ids = set(n.id for n in nodes)
            edges = [e for e in edges if e.source_id in node_ids and e.target_id in node_ids]

        return {
            "nodes": [n.model_dump() for n in nodes],
            "edges": [e.model_dump() for e in edges],
            "nodes_count": len(nodes),
            "edges_count": len(edges)
        }


global_graph_store = KnowledgeGraphStore()
