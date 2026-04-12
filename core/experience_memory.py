"""
GENESIS Experience Memory - Self-Learning System.
Phase 11 Requirement.
Stores action → result → context triples for experiential learning.
"""

import json
import os
import time
import atexit
import threading
from typing import Dict, List, Any, Optional
from collections import deque
from datetime import datetime
from core.event_bus import get_event_bus

logger = __import__('logging').getLogger(__name__)

PERSIST_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "shared", "experience_memory.json")


class Experience:
    """A single experience record: action taken, result observed, context."""

    __slots__ = ("timestamp", "action", "result", "success", "context", "emotion", "source")

    def __init__(self, action: str, result: str, success: bool,
                 context: str = "", emotion: str = "neutral", source: str = "system"):
        self.timestamp = datetime.now().isoformat()
        self.action = action
        self.result = result
        self.success = success
        self.context = context
        self.emotion = emotion
        self.source = source

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "action": self.action,
            "result": self.result,
            "success": self.success,
            "context": self.context,
            "emotion": self.emotion,
            "source": self.source,
        }


class ExperienceMemory:
    """
    Persistent experience store.
    Keeps a rolling buffer of recent experiences and allows recall by action pattern.
    """

    MAX_EXPERIENCES = 5000

    def __init__(self):
        self._store: deque = deque(maxlen=self.MAX_EXPERIENCES)
        self._action_index: Dict[str, List[int]] = {}
        self._lock = threading.Lock()
        self._success_count = 0
        self._fail_count = 0
        self._load_from_disk()
        atexit.register(self.save_to_disk)

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def record(self, action: str, result: str, success: bool,
               context: str = "", emotion: str = "neutral", source: str = "system") -> Experience:
        """Record a new experience."""
        exp = Experience(action, result, success, context, emotion, source)
        with self._lock:
            idx = len(self._store)
            self._store.append(exp)
            key = action.lower().strip()
            self._action_index.setdefault(key, []).append(idx)
            if success:
                self._success_count += 1
            else:
                self._fail_count += 1

        # Publish event
        bus = get_event_bus()
        if bus:
            bus.publish_sync("EXPERIENCE_RECORDED", "experience_memory", exp.to_dict())

        return exp

    def recall(self, action_pattern: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Recall experiences matching an action pattern (substring match)."""
        pattern = action_pattern.lower().strip()
        results: List[Dict[str, Any]] = []
        with self._lock:
            for exp in reversed(self._store):
                if pattern in exp.action.lower():
                    results.append(exp.to_dict())
                    if len(results) >= limit:
                        break
        return results

    def recall_recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return the most recent experiences."""
        with self._lock:
            return [e.to_dict() for e in list(self._store)[-limit:]]

    def success_rate(self, action_pattern: str = "") -> float:
        """Calculate success rate, optionally filtered by action pattern."""
        with self._lock:
            if not action_pattern:
                total = self._success_count + self._fail_count
                return (self._success_count / total) if total > 0 else 0.0
            matches = [e for e in self._store if action_pattern.lower() in e.action.lower()]
            if not matches:
                return 0.0
            successes = sum(1 for e in matches if e.success)
            return successes / len(matches)

    def get_stats(self) -> Dict[str, Any]:
        """Return memory statistics."""
        return {
            "total_experiences": len(self._store),
            "successes": self._success_count,
            "failures": self._fail_count,
            "success_rate": self.success_rate(),
            "unique_actions": len(self._action_index),
        }

    def export_json(self, filepath: str = "experience_memory.json"):
        """Export all experiences to JSON."""
        with self._lock:
            data = [e.to_dict() for e in self._store]
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        return filepath

    def save_to_disk(self):
        """Persist experiences to JSON file."""
        try:
            with self._lock:
                data = {
                    "experiences": [e.to_dict() for e in self._store],
                    "success_count": self._success_count,
                    "fail_count": self._fail_count,
                }
            os.makedirs(os.path.dirname(PERSIST_FILE), exist_ok=True)
            with open(PERSIST_FILE, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"[EXPERIENCE] Saved {len(self._store)} experiences to disk")
        except Exception as e:
            logger.error(f"[EXPERIENCE] Failed to save to disk: {e}")

    def _load_from_disk(self):
        """Load experiences from JSON file."""
        try:
            if not os.path.exists(PERSIST_FILE):
                return
            with open(PERSIST_FILE, "r") as f:
                data = json.load(f)
            experiences = data.get("experiences", [])
            for edata in experiences:
                exp = Experience(
                    action=edata.get("action", ""),
                    result=edata.get("result", ""),
                    success=edata.get("success", False),
                    context=edata.get("context", ""),
                    emotion=edata.get("emotion", "neutral"),
                    source=edata.get("source", "disk"),
                )
                exp.timestamp = edata.get("timestamp", exp.timestamp)
                self._store.append(exp)
            self._success_count = data.get("success_count", 0)
            self._fail_count = data.get("fail_count", 0)
            logger.info(f"[EXPERIENCE] Loaded {len(self._store)} experiences from disk")
        except Exception as e:
            logger.error(f"[EXPERIENCE] Failed to load from disk: {e}")


# --------------- Module-level singleton ---------------
_experience_memory: Optional[ExperienceMemory] = None


def get_experience_memory() -> ExperienceMemory:
    global _experience_memory
    if _experience_memory is None:
        _experience_memory = ExperienceMemory()
    return _experience_memory


def record_experience(action: str, result: str, success: bool, **kwargs) -> Experience:
    return get_experience_memory().record(action, result, success, **kwargs)


def recall_experience(pattern: str, limit: int = 10) -> List[Dict]:
    return get_experience_memory().recall(pattern, limit)
