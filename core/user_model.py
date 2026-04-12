"""
GENESIS User Model — Phase 6 Intelligence Integration.
Lightweight behavioral modeling: habit tracking, preference learning, activity prediction.
Does NOT modify owner_system.py authentication logic.
"""

import json
import os
import time
import threading
import logging
from typing import Dict, List, Any, Optional
from collections import Counter, defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)

MODEL_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "shared", "user_model.json")


class UserModel:
    """Tracks user interaction patterns for personalization."""

    def __init__(self):
        self._lock = threading.Lock()

        # Interaction log (rolling buffer)
        self._interactions: List[Dict[str, Any]] = []
        self._max_interactions = 2000

        # Aggregated statistics
        self._topic_counts: Counter = Counter()
        self._hour_counts: Counter = Counter()  # hour of day → count
        self._command_counts: Counter = Counter()

        self._load_from_disk()
        logger.info("[USER_MODEL] User model initialized")

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def record_interaction(self, command: str, topic: str = "",
                           result: str = "", success: bool = True):
        """Record a user interaction for pattern learning."""
        now = datetime.now()
        entry = {
            "command": command[:200],
            "topic": topic or self._extract_topic(command),
            "result_summary": result[:100],
            "success": success,
            "hour": now.hour,
            "day_of_week": now.strftime("%A"),
            "timestamp": now.isoformat(),
        }

        with self._lock:
            self._interactions.append(entry)
            if len(self._interactions) > self._max_interactions:
                self._interactions = self._interactions[-self._max_interactions:]

            # Update aggregates
            self._topic_counts[entry["topic"]] += 1
            self._hour_counts[entry["hour"]] += 1
            self._command_counts[command.split()[0].lower() if command.strip() else "empty"] += 1
            self._save_to_disk()

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_habits(self) -> Dict[str, Any]:
        """Return user habit summary: peak hours, frequent topics, patterns."""
        with self._lock:
            total = len(self._interactions)
            if total == 0:
                return {"total_interactions": 0, "message": "No data yet."}

            peak_hours = self._hour_counts.most_common(3)
            top_topics = self._topic_counts.most_common(5)
            top_commands = self._command_counts.most_common(5)

            return {
                "total_interactions": total,
                "peak_hours": [{"hour": h, "count": c} for h, c in peak_hours],
                "top_topics": [{"topic": t, "count": c} for t, c in top_topics],
                "top_commands": [{"command": cmd, "count": c} for cmd, c in top_commands],
            }

    def get_preferences(self) -> Dict[str, Any]:
        """Infer user preferences from interaction history."""
        with self._lock:
            if not self._interactions:
                return {"message": "No preference data yet."}

            # Topic preferences (most discussed)
            top = self._topic_counts.most_common(10)

            # Time preferences
            morning = sum(self._hour_counts[h] for h in range(6, 12))
            afternoon = sum(self._hour_counts[h] for h in range(12, 18))
            evening = sum(self._hour_counts[h] for h in range(18, 24))
            night = sum(self._hour_counts[h] for h in range(0, 6))

            time_pref = max(
                [("morning", morning), ("afternoon", afternoon),
                 ("evening", evening), ("night", night)],
                key=lambda x: x[1]
            )

            return {
                "preferred_topics": [t for t, _ in top[:5]],
                "preferred_time_of_day": time_pref[0],
                "time_distribution": {
                    "morning": morning, "afternoon": afternoon,
                    "evening": evening, "night": night,
                },
            }

    def predict_activity(self) -> Dict[str, Any]:
        """Predict likely next activity based on current time and patterns."""
        now = datetime.now()
        current_hour = now.hour
        current_day = now.strftime("%A")

        with self._lock:
            # Find interactions at similar times
            similar_time = [
                i for i in self._interactions
                if abs(i.get("hour", -1) - current_hour) <= 1
            ]

            if not similar_time:
                return {"prediction": "No pattern data for this time of day."}

            # Most common topic at this hour
            topics_at_hour = Counter(i.get("topic", "") for i in similar_time if i.get("topic"))
            predicted_topic = topics_at_hour.most_common(1)[0][0] if topics_at_hour else "general"

            return {
                "current_hour": current_hour,
                "current_day": current_day,
                "predicted_topic": predicted_topic,
                "confidence": min(len(similar_time) / 10.0, 1.0),
                "sample_size": len(similar_time),
            }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_topic(command: str) -> str:
        """Extract a rough topic from a command string."""
        if not command:
            return "general"
        cmd = command.lower()
        topic_keywords = {
            "music": ["music", "song", "play", "listen", "piano", "guitar"],
            "search": ["search", "find", "look up", "google", "research"],
            "automation": ["automate", "workflow", "webhook", "schedule"],
            "file": ["file", "open", "save", "folder", "directory"],
            "system": ["status", "health", "monitor", "restart", "shutdown"],
            "memory": ["remember", "recall", "forget", "memory"],
            "time": ["time", "date", "calendar", "schedule"],
            "weather": ["weather", "temperature", "forecast"],
        }
        for topic, keywords in topic_keywords.items():
            if any(kw in cmd for kw in keywords):
                return topic
        return "general"

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _save_to_disk(self):
        """Save model to JSON (called under lock)."""
        try:
            data = {
                "interactions": self._interactions[-500:],  # Keep last 500 on disk
                "topic_counts": dict(self._topic_counts),
                "hour_counts": {str(k): v for k, v in self._hour_counts.items()},
                "command_counts": dict(self._command_counts),
            }
            os.makedirs(os.path.dirname(MODEL_FILE), exist_ok=True)
            with open(MODEL_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"[USER_MODEL] Failed to save: {e}")

    def _load_from_disk(self):
        """Load model from JSON."""
        try:
            if os.path.exists(MODEL_FILE):
                with open(MODEL_FILE, "r") as f:
                    data = json.load(f)
                self._interactions = data.get("interactions", [])
                self._topic_counts = Counter(data.get("topic_counts", {}))
                self._hour_counts = Counter({int(k): v for k, v in data.get("hour_counts", {}).items()})
                self._command_counts = Counter(data.get("command_counts", {}))
                logger.info(f"[USER_MODEL] Loaded {len(self._interactions)} interactions from disk")
        except Exception as e:
            logger.error(f"[USER_MODEL] Failed to load: {e}")


# --------------- Module-level singleton ---------------
_user_model: Optional[UserModel] = None


def get_user_model() -> UserModel:
    global _user_model
    if _user_model is None:
        _user_model = UserModel()
    return _user_model
