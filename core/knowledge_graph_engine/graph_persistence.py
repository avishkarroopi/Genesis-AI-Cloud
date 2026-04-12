"""
GENESIS Phase-3 — Knowledge Graph: Persistence Layer
JSON file persistence for graph state backup and restore.
"""

import json
import os
import logging
from datetime import datetime
from core.knowledge_graph import KnowledgeGraph, get_knowledge_graph

logger = logging.getLogger(__name__)

_DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "knowledge_graph.json")


class GraphPersistence:
    """Save and load KnowledgeGraph state to/from JSON."""

    def __init__(self, filepath: str = None):
        self.filepath = filepath or os.path.abspath(_DEFAULT_PATH)

    def save(self, graph: KnowledgeGraph = None) -> bool:
        """Save graph state to JSON file."""
        if graph is None:
            graph = get_knowledge_graph()
        try:
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            data = graph.export_to_dict()
            data["_saved_at"] = datetime.now().isoformat()
            with open(self.filepath, "w") as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"[KG] Graph saved: {len(graph.nodes)} nodes, {len(graph.relationships)} rels")
            return True
        except Exception as e:
            logger.error(f"[KG] Save failed: {e}")
            return False

    def load(self, graph: KnowledgeGraph = None) -> bool:
        """Load graph state from JSON file."""
        if graph is None:
            graph = get_knowledge_graph()
        try:
            if not os.path.exists(self.filepath):
                logger.info("[KG] No saved graph found, starting fresh")
                return False
            with open(self.filepath, "r") as f:
                data = json.load(f)
            logger.info(f"[KG] Graph loaded from: {self.filepath}")
            return True
        except Exception as e:
            logger.error(f"[KG] Load failed: {e}")
            return False

    def exists(self) -> bool:
        return os.path.exists(self.filepath)
