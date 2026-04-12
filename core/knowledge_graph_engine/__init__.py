"""
GENESIS Phase-3 — Knowledge Graph Engine Wrapper
Module 2: Extends the existing knowledge_graph.py with advanced queries and persistence.
Does NOT modify the original knowledge_graph.py.
"""

from core.knowledge_graph import (
    KnowledgeGraph, get_knowledge_graph, set_knowledge_graph,
    NodeType, RelationType, Node, Relationship
)
from .graph_queries import GraphQueryEngine
from .graph_persistence import GraphPersistence

__all__ = [
    "KnowledgeGraph", "get_knowledge_graph", "set_knowledge_graph",
    "NodeType", "RelationType", "Node", "Relationship",
    "GraphQueryEngine", "GraphPersistence",
]
