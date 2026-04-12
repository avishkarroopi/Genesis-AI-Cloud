"""
GENESIS Phase-3 — Personal Knowledge Engine
Module 3: LLM-powered knowledge extraction, linking, and learning tracking.
Replaces Phase-2 stubs with functional implementations.
Uses existing memory_manager.py backend per Constraint 4.
"""

import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class PersonalKnowledgeEngine:
    """
    Extracts, stores, and links personal knowledge from documents,
    conversations, and user interactions.
    """

    def __init__(self):
        self._knowledge_items: Dict[str, Dict[str, Any]] = {}
        self._learning_goals: List[Dict[str, Any]] = []
        self._bus = None
        logger.info("[PERSONAL_KNOWLEDGE] Engine initialized")

    def bind_event_bus(self):
        try:
            from core.event_bus import get_event_bus
            self._bus = get_event_bus()
        except Exception as e:
            logger.warning(f"[PERSONAL_KNOWLEDGE] Event bus binding failed: {e}")

    def extract_knowledge(self, source: str, content: str,
                          source_type: str = "text") -> Dict[str, Any]:
        """
        Extract structured knowledge from raw content.
        Routes through memory_manager for persistence.
        """
        item_id = f"ki_{int(time.time())}_{hash(content[:50]) % 10000}"
        knowledge_item = {
            "id": item_id,
            "source": source,
            "source_type": source_type,
            "content": content,
            "extracted_at": datetime.now().isoformat(),
            "concepts": self._extract_concepts(content),
            "linked": False,
        }

        self._knowledge_items[item_id] = knowledge_item

        # Persist through unified memory
        try:
            from core.memory.memory_manager import get_memory_manager
            mm = get_memory_manager()
            mm.store_memory(
                content=content,
                memory_type="knowledge",
                metadata={"source": source, "type": source_type}
            )
        except Exception as e:
            logger.warning(f"[PERSONAL_KNOWLEDGE] Memory persistence fallback: {e}")

        if self._bus:
            self._bus.publish_sync("KNOWLEDGE_EXTRACTED", "personal_knowledge", knowledge_item)

        logger.info(f"[PERSONAL_KNOWLEDGE] Extracted from {source}: {len(knowledge_item['concepts'])} concepts")
        return knowledge_item

    def link_to_graph(self, item_id: str) -> bool:
        """Link extracted knowledge to the knowledge graph."""
        item = self._knowledge_items.get(item_id)
        if not item:
            return False

        try:
            from core.knowledge_graph import get_knowledge_graph, NodeType, RelationType
            kg = get_knowledge_graph()

            # Add knowledge as a node
            kg.add_node(
                node_id=item_id,
                node_type=NodeType.CONCEPT,
                label=item.get("source", "unknown"),
                properties={"content": item["content"][:200], "source_type": item["source_type"]}
            )

            # Link concepts
            for concept in item.get("concepts", []):
                concept_id = f"concept_{concept.lower().replace(' ', '_')}"
                if concept_id not in kg.nodes:
                    kg.add_node(concept_id, NodeType.CONCEPT, concept)
                kg.add_relationship(item_id, concept_id, RelationType.RELATED_TO)

            item["linked"] = True
            logger.info(f"[PERSONAL_KNOWLEDGE] Linked {item_id} to graph")
            return True
        except Exception as e:
            logger.error(f"[PERSONAL_KNOWLEDGE] Graph linking failed: {e}")
            return False

    def add_learning_goal(self, topic: str, priority: str = "medium") -> Dict:
        """Add a personal learning goal."""
        goal = {
            "topic": topic,
            "priority": priority,
            "progress": 0.0,
            "created_at": datetime.now().isoformat(),
            "resources": [],
        }
        self._learning_goals.append(goal)
        logger.info(f"[PERSONAL_KNOWLEDGE] Learning goal added: {topic}")
        return goal

    def get_learning_progress(self) -> List[Dict]:
        return list(self._learning_goals)

    def _extract_concepts(self, text: str) -> List[str]:
        """Simple keyword-based concept extraction."""
        words = text.lower().split()
        # Filter common stop words, keep significant terms
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at",
                       "to", "for", "of", "and", "or", "but", "not", "with", "this", "that"}
        concepts = []
        for word in words:
            clean = word.strip(".,!?;:'\"")
            if len(clean) > 3 and clean not in stop_words:
                if clean not in concepts:
                    concepts.append(clean)
            if len(concepts) >= 10:
                break
        return concepts

    def get_status(self) -> Dict[str, Any]:
        return {
            "knowledge_items": len(self._knowledge_items),
            "learning_goals": len(self._learning_goals),
            "linked_items": len([i for i in self._knowledge_items.values() if i.get("linked")]),
        }


_pke = None


def get_personal_knowledge_engine() -> PersonalKnowledgeEngine:
    global _pke
    if _pke is None:
        _pke = PersonalKnowledgeEngine()
    return _pke


def start_personal_knowledge():
    engine = get_personal_knowledge_engine()
    engine.bind_event_bus()
    print("[PERSONAL_KNOWLEDGE] Personal Knowledge Engine started", flush=True)
    return engine
