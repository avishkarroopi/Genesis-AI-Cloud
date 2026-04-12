"""
GENESIS Life Memory Engine — Phase 2.5
Stores structured life data: conversations, ideas, goals, decisions, meetings, research, relationships.
Provides contextual retrieval for life memory queries like "What did Ravi say about the startup?"
"""

import json
import os
import threading
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

LIFE_MEMORY_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "shared", "life_memory.json"
)

# Maximum number of life memory entries kept in RAM
MAX_ENTRIES = 10000

VALID_CATEGORIES = {
    "conversation", "idea", "goal", "decision",
    "meeting", "research", "file", "relationship"
}


class LifeMemoryEntry:
    """Single structured life memory record."""
    __slots__ = ("entry_id", "category", "content", "tags",
                 "people", "timestamp", "metadata")

    def __init__(self, entry_id: str, category: str, content: str,
                 tags: List[str] = None, people: List[str] = None,
                 timestamp: str = None, metadata: Dict = None):
        self.entry_id = entry_id
        self.category = category
        self.content = content
        self.tags = tags or []
        self.people = people or []
        self.timestamp = timestamp or datetime.now().isoformat()
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "category": self.category,
            "content": self.content,
            "tags": self.tags,
            "people": self.people,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


class LifeMemoryEngine:
    """
    Stores and retrieves structured life memory.
    Thread-safe, persisted to JSON.
    """

    def __init__(self):
        self._entries: List[LifeMemoryEntry] = []
        self._lock = threading.Lock()
        self._counter = 0
        self._load_from_disk()
        logger.info(f"[LIFE-MEMORY] Engine initialized ({len(self._entries)} entries loaded)")

    def store(self, category: str, content: str,
              tags: List[str] = None, people: List[str] = None,
              metadata: Dict = None) -> LifeMemoryEntry:
        """Store a new life memory entry."""
        if category not in VALID_CATEGORIES:
            logger.warning(f"[LIFE-MEMORY] Unknown category '{category}', using 'conversation'")
            category = "conversation"

        with self._lock:
            # Enforce memory limit
            if len(self._entries) >= MAX_ENTRIES:
                # Remove oldest 10% of entries 
                trim = int(MAX_ENTRIES * 0.1)
                self._entries = self._entries[trim:]
                logger.info(f"[LIFE-MEMORY] Trimmed {trim} old entries (limit={MAX_ENTRIES})")

            self._counter += 1
            entry_id = f"life_{self._counter}_{int(time.time())}"
            entry = LifeMemoryEntry(
                entry_id=entry_id,
                category=category,
                content=content,
                tags=tags or [],
                people=people or [],
                metadata=metadata or {},
            )
            self._entries.append(entry)

        self._save_to_disk()

        try:
            from core.event_bus import get_event_bus
            bus = get_event_bus()
            if bus:
                bus.publish_sync("LIFE_MEMORY_STORED", "life_memory_engine", entry.to_dict())
        except Exception:
            pass

        logger.info(f"[LIFE-MEMORY] Stored [{category}] {content[:60]}...")
        return entry

    def search(self, query: str, category: str = None,
               person: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search life memory by text, category, or person."""
        query_lower = query.lower()
        results = []

        with self._lock:
            for entry in reversed(self._entries):
                if category and entry.category != category:
                    continue
                if person and person.lower() not in [p.lower() for p in entry.people]:
                    continue
                if query_lower in entry.content.lower() or \
                   any(query_lower in t.lower() for t in entry.tags) or \
                   any(query_lower in p.lower() for p in entry.people):
                    results.append(entry.to_dict())
                    if len(results) >= limit:
                        break

        return results

    def get_recent(self, limit: int = 20, category: str = None) -> List[Dict[str, Any]]:
        """Return most recent entries, optionally filtered by category."""
        with self._lock:
            entries = list(reversed(self._entries))

        filtered = [e.to_dict() for e in entries
                    if not category or e.category == category]
        return filtered[:limit]

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            total = len(self._entries)
            by_cat = {}
            for e in self._entries:
                by_cat[e.category] = by_cat.get(e.category, 0) + 1
        return {"total_entries": total, "by_category": by_cat, "limit": MAX_ENTRIES}

    def _save_to_disk(self):
        try:
            os.makedirs(os.path.dirname(LIFE_MEMORY_FILE), exist_ok=True)
            with self._lock:
                data = [e.to_dict() for e in self._entries]
            with open(LIFE_MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"[LIFE-MEMORY] Save failed: {e}")

    def _load_from_disk(self):
        try:
            if not os.path.exists(LIFE_MEMORY_FILE):
                return
            with open(LIFE_MEMORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                entry = LifeMemoryEntry(**{
                    k: item.get(k) for k in LifeMemoryEntry.__slots__
                })
                self._entries.append(entry)
                self._counter = max(self._counter,
                                    int(entry.entry_id.split("_")[1]) if "_" in entry.entry_id else 0)
        except Exception as e:
            logger.error(f"[LIFE-MEMORY] Load failed: {e}")


# Singleton
_life_memory: Optional[LifeMemoryEngine] = None


def get_life_memory_engine() -> LifeMemoryEngine:
    global _life_memory
    if _life_memory is None:
        _life_memory = LifeMemoryEngine()
    return _life_memory


def store_life_memory(category: str, content: str, **kwargs) -> LifeMemoryEntry:
    return get_life_memory_engine().store(category, content, **kwargs)


def search_life_memory(query: str, **kwargs) -> List[Dict[str, Any]]:
    return get_life_memory_engine().search(query, **kwargs)
