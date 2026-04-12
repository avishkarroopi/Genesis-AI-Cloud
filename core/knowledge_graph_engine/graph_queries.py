"""
GENESIS Phase-3 — Knowledge Graph: Advanced Query Engine
Provides pattern matching, path queries, and relationship reasoning.
"""

import logging
from typing import Dict, List, Any, Optional, Set
from core.knowledge_graph import KnowledgeGraph, NodeType, RelationType, Node

logger = logging.getLogger(__name__)


class GraphQueryEngine:
    """Advanced query capabilities over the KnowledgeGraph."""

    def __init__(self, graph: KnowledgeGraph = None):
        if graph is None:
            from core.knowledge_graph import get_knowledge_graph
            graph = get_knowledge_graph()
        self.graph = graph

    def find_related_entities(self, node_id: str, max_depth: int = 2) -> List[Dict[str, Any]]:
        """Find all entities related to a given node within max_depth hops."""
        visited = self.graph.bfs(node_id, max_depth)
        results = []
        for nid, depth in visited.items():
            if nid == node_id:
                continue
            node = self.graph.get_node(nid)
            if node:
                results.append({
                    "node_id": nid,
                    "label": node.label,
                    "type": node.node_type.value,
                    "depth": depth,
                })
        return results

    def find_by_type_and_property(self, node_type: NodeType,
                                  property_key: str, property_value: Any = None) -> List[Node]:
        """Query nodes by type AND property."""
        type_nodes = self.graph.query_by_type(node_type)
        results = []
        for node in type_nodes:
            if property_key in node.properties:
                if property_value is None or node.properties[property_key].value == property_value:
                    results.append(node)
        return results

    def get_relationship_chain(self, source_id: str, target_id: str) -> Optional[List[Dict]]:
        """Get the full chain of relationships between two nodes."""
        path = self.graph.get_path(source_id, target_id)
        if not path or len(path) < 2:
            return None

        chain = []
        for i in range(len(path) - 1):
            rel = self.graph.get_relationship(path[i], path[i + 1])
            if rel:
                chain.append({
                    "from": path[i],
                    "to": path[i + 1],
                    "relation": rel.relation_type.value,
                    "confidence": rel.confidence,
                })
        return chain

    def get_entity_context(self, node_id: str) -> Dict[str, Any]:
        """Get full context for an entity: properties, relationships, neighbors."""
        node = self.graph.get_node(node_id)
        if not node:
            return {}

        neighbors = self.graph.get_neighbors(node_id)
        inferred = self.graph.infer_properties(node_id)

        return {
            "node": node.to_dict(),
            "neighbors": [n.to_dict() for n in neighbors],
            "inferred_properties": {k: str(v) for k, v in inferred.items()},
        }

    def search_nodes(self, query: str, limit: int = 10) -> List[Node]:
        """Simple text search across node labels and properties."""
        query_lower = query.lower()
        results = []
        for node in self.graph.nodes.values():
            if query_lower in node.label.lower():
                results.append(node)
                continue
            for prop in node.properties.values():
                if isinstance(prop.value, str) and query_lower in prop.value.lower():
                    results.append(node)
                    break
            if len(results) >= limit:
                break
        return results
