"""
Production-grade knowledge graph for GENESIS + JARVIS.
Stores entities, relationships, and properties for spatial reasoning.
Requirements: 3, 14, 23, 27 (owner profiles, memory, learning, world model).
"""

import json
import logging
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
from collections import defaultdict


class NodeType(Enum):
    ENTITY = "entity"
    OWNER_PROFILE = "owner_profile"
    PERSON = "person"
    OBJECT = "object"
    LOCATION = "location"
    EVENT = "event"
    CONCEPT = "concept"
    MEMORY = "memory"
    SKILL = "skill"
    PREFERENCE = "preference"


class RelationType(Enum):
    LOCATED_AT = "located_at"
    OWNS = "owns"
    SEES = "sees"
    INTERACTS_WITH = "interacts_with"
    KNOWS = "knows"
    HAS_PROPERTY = "has_property"
    INSTANCE_OF = "instance_of"
    PART_OF = "part_of"
    RELATED_TO = "related_to"
    EXPERIENCED = "experienced"
    ACHIEVED = "achieved"
    PREFERS = "prefers"


@dataclass
class Property:
    """Key-value property with confidence score."""
    key: str
    value: Any
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "system"


@dataclass
class Node:
    """Knowledge graph node representing an entity."""
    node_id: str
    node_type: NodeType
    label: str
    properties: Dict[str, Property] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_property(self, key: str, value: Any, confidence: float = 1.0, source: str = "system"):
        """Add or update a property."""
        self.properties[key] = Property(key, value, confidence, datetime.now(), source)
        self.updated_at = datetime.now()
    
    def get_property(self, key: str, default: Any = None) -> Any:
        """Get a property value."""
        if key in self.properties:
            return self.properties[key].value
        return default
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "label": self.label,
            "properties": {k: asdict(v) for k, v in self.properties.items()},
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class Relationship:
    """Relationship between two nodes."""
    relation_id: str
    source_id: str
    target_id: str
    relation_type: RelationType
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "relation_id": self.relation_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type.value,
            "properties": self.properties,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat()
        }


class KnowledgeGraph:
    """
    In-memory knowledge graph with graph operations.
    Supports querying, reasoning, and learning.
    """
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.nodes: Dict[str, Node] = {}
        self.relationships: Dict[str, Relationship] = {}
        self._index: Dict[str, List[str]] = defaultdict(list)
        self._adjacency: Dict[str, Set[str]] = defaultdict(set)
        
    def add_node(self, node_id: str, node_type: NodeType, label: str,
                 properties: Dict[str, Any] = None, metadata: Dict[str, Any] = None) -> Node:
        """Add a node to the graph."""
        node = Node(
            node_id=node_id,
            node_type=node_type,
            label=label,
            metadata=metadata or {}
        )
        
        if properties:
            for key, value in properties.items():
                node.add_property(key, value)
        
        self.nodes[node_id] = node
        self._index[node_type.value].append(node_id)
        self.logger.debug(f"Added node: {node_id} ({node_type.value})")
        return node
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by ID."""
        return self.nodes.get(node_id)
    
    def add_relationship(self, source_id: str, target_id: str,
                        relation_type: RelationType, properties: Dict = None,
                        confidence: float = 1.0) -> Relationship:
        """Add a relationship between two nodes."""
        if source_id not in self.nodes or target_id not in self.nodes:
            raise ValueError(f"Source or target node not found")
        
        rel_id = f"{source_id}--{relation_type.value}--{target_id}"
        relationship = Relationship(
            relation_id=rel_id,
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            properties=properties or {},
            confidence=confidence
        )
        
        self.relationships[rel_id] = relationship
        self._adjacency[source_id].add(target_id)
        self.logger.debug(f"Added relationship: {rel_id}")
        return relationship
    
    def get_relationship(self, source_id: str, target_id: str,
                        relation_type: RelationType = None) -> Optional[Relationship]:
        """Get a relationship between two nodes."""
        if relation_type:
            rel_id = f"{source_id}--{relation_type.value}--{target_id}"
            return self.relationships.get(rel_id)
        
        for rel_id, rel in self.relationships.items():
            if rel.source_id == source_id and rel.target_id == target_id:
                return rel
        return None
    
    def get_neighbors(self, node_id: str, relation_type: RelationType = None) -> List[Node]:
        """Get all neighbors of a node."""
        neighbors = []
        for rel_id, rel in self.relationships.items():
            if rel.source_id == node_id:
                if relation_type is None or rel.relation_type == relation_type:
                    neighbor = self.get_node(rel.target_id)
                    if neighbor:
                        neighbors.append(neighbor)
        return neighbors
    
    def query_by_type(self, node_type: NodeType) -> List[Node]:
        """Query all nodes of a specific type."""
        node_ids = self._index.get(node_type.value, [])
        return [self.nodes[nid] for nid in node_ids if nid in self.nodes]
    
    def query_by_property(self, property_key: str, property_value: Any = None) -> List[Node]:
        """Query nodes by property."""
        results = []
        for node in self.nodes.values():
            if property_key in node.properties:
                prop = node.properties[property_key]
                if property_value is None or prop.value == property_value:
                    results.append(node)
        return results
    
    def bfs(self, start_node_id: str, max_depth: int = 3) -> Dict[str, int]:
        """Breadth-first search from a node."""
        visited = {start_node_id: 0}
        queue = [(start_node_id, 0)]
        
        while queue:
            node_id, depth = queue.pop(0)
            if depth < max_depth:
                for neighbor_id in self._adjacency.get(node_id, set()):
                    if neighbor_id not in visited:
                        visited[neighbor_id] = depth + 1
                        queue.append((neighbor_id, depth + 1))
        
        return visited
    
    def get_path(self, source_id: str, target_id: str) -> Optional[List[str]]:
        """Find a path between two nodes using BFS."""
        if source_id not in self.nodes or target_id not in self.nodes:
            return None
        
        queue = [(source_id, [source_id])]
        visited = {source_id}
        
        while queue:
            current, path = queue.pop(0)
            if current == target_id:
                return path
            
            for neighbor_id in self._adjacency.get(current, set()):
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [neighbor_id]))
        
        return None
    
    def infer_properties(self, node_id: str) -> Dict[str, Any]:
        """Infer properties through relationships."""
        node = self.get_node(node_id)
        if not node:
            return {}
        
        inferred = dict(node.properties)
        
        instance_of_rels = [
            rel for rel in self.relationships.values()
            if rel.source_id == node_id and rel.relation_type == RelationType.INSTANCE_OF
        ]
        
        for rel in instance_of_rels:
            parent = self.get_node(rel.target_id)
            if parent:
                for key, prop in parent.properties.items():
                    if key not in inferred:
                        inferred[key] = prop
        
        return inferred
    
    def export_to_dict(self) -> Dict:
        """Export entire graph to dictionary."""
        return {
            "nodes": {nid: node.to_dict() for nid, node in self.nodes.items()},
            "relationships": {rid: rel.to_dict() for rid, rel in self.relationships.items()}
        }
    
    def to_json(self, filepath: str = None) -> str:
        """Export graph to JSON."""
        data = self.export_to_dict()
        json_str = json.dumps(data, indent=2, default=str)
        
        if filepath:
            with open(filepath, 'w') as f:
                f.write(json_str)
        
        return json_str
    
    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics."""
        return {
            "total_nodes": len(self.nodes),
            "total_relationships": len(self.relationships),
            "node_types": {
                node_type.name: len(self._index.get(node_type.value, []))
                for node_type in NodeType
            },
            "relationship_types": {
                rel_type.name: len([
                    r for r in self.relationships.values()
                    if r.relation_type == rel_type
                ])
                for rel_type in RelationType
            }
        }


_global_knowledge_graph: KnowledgeGraph = None


def get_knowledge_graph() -> KnowledgeGraph:
    """Get or create the global knowledge graph."""
    global _global_knowledge_graph
    if _global_knowledge_graph is None:
        _global_knowledge_graph = KnowledgeGraph()
    return _global_knowledge_graph


def set_knowledge_graph(kg: KnowledgeGraph):
    """Set the global knowledge graph."""
    global _global_knowledge_graph
    _global_knowledge_graph = kg
