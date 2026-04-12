"""
GENESIS Phase-3 — Human Interaction Intelligence
Module 5: Emotion modeling, conversation personality, user preference learning,
and adaptive communication.

Subscribes to: EMOTION_UPDATE, COMMAND_RUN
Publishes: INTERACTION_INSIGHT
Extends (does NOT replace): emotion_engine.py, user_model.py
"""

import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)


class ConversationPersonality:
    """Manages adaptive tone and communication style."""

    def __init__(self):
        self.formality_level: float = 0.5  # 0=casual, 1=formal
        self.verbosity_level: float = 0.5  # 0=terse, 1=verbose
        self.humor_level: float = 0.3
        self.empathy_level: float = 0.7

    def get_style_hints(self) -> Dict[str, float]:
        return {
            "formality": self.formality_level,
            "verbosity": self.verbosity_level,
            "humor": self.humor_level,
            "empathy": self.empathy_level,
        }

    def adapt(self, feedback: str):
        """Adapt personality based on user feedback."""
        if "formal" in feedback.lower():
            self.formality_level = min(1.0, self.formality_level + 0.1)
        elif "casual" in feedback.lower():
            self.formality_level = max(0.0, self.formality_level - 0.1)
        if "brief" in feedback.lower() or "short" in feedback.lower():
            self.verbosity_level = max(0.0, self.verbosity_level - 0.1)
        elif "detail" in feedback.lower():
            self.verbosity_level = min(1.0, self.verbosity_level + 0.1)


class PreferenceLearner:
    """Track and learn user communication preferences over time."""

    def __init__(self):
        self.preferences: Dict[str, Any] = {}
        self.interaction_history: deque = deque(maxlen=500)

    def record_interaction(self, command: str, response_quality: str = "neutral"):
        self.interaction_history.append({
            "command": command,
            "quality": response_quality,
            "timestamp": datetime.now().isoformat(),
        })

    def get_preferred_topics(self) -> List[str]:
        """Identify frequently discussed topics."""
        topic_counts: Dict[str, int] = {}
        for interaction in self.interaction_history:
            words = interaction["command"].lower().split()
            for word in words:
                if len(word) > 4:
                    topic_counts[word] = topic_counts.get(word, 0) + 1
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        return [t[0] for t in sorted_topics[:10]]


class EmotionModeler:
    """Advanced emotion tracking extending the base emotion_engine."""

    def __init__(self):
        self.emotion_history: deque = deque(maxlen=100)
        self.current_valence: float = 0.0   # -1 negative, +1 positive
        self.current_arousal: float = 0.0   # 0 calm, 1 excited
        self._emotion_map = {
            "happy": (0.8, 0.6),
            "alert": (0.1, 0.8),
            "thinking": (0.2, 0.4),
            "listening": (0.3, 0.3),
            "talking": (0.4, 0.5),
            "error": (-0.5, 0.7),
            "sleep": (0.0, 0.0),
            "idle": (0.1, 0.1),
        }

    def update_from_event(self, emotion: str):
        """Update emotional state from emotion engine events."""
        valence, arousal = self._emotion_map.get(emotion, (0.0, 0.0))
        # Smooth transition
        self.current_valence = 0.7 * self.current_valence + 0.3 * valence
        self.current_arousal = 0.7 * self.current_arousal + 0.3 * arousal

        self.emotion_history.append({
            "emotion": emotion,
            "valence": self.current_valence,
            "arousal": self.current_arousal,
            "timestamp": datetime.now().isoformat(),
        })

    def get_emotional_context(self) -> Dict[str, Any]:
        return {
            "valence": round(self.current_valence, 3),
            "arousal": round(self.current_arousal, 3),
            "trend": self._get_trend(),
        }

    def _get_trend(self) -> str:
        if len(self.emotion_history) < 3:
            return "stable"
        recent = list(self.emotion_history)[-3:]
        valences = [e["valence"] for e in recent]
        if all(v > valences[0] for v in valences[1:]):
            return "improving"
        elif all(v < valences[0] for v in valences[1:]):
            return "declining"
        return "stable"


class HumanInteractionIntelligence:
    """
    Master controller for human interaction intelligence.
    Combines personality, preferences, and emotion modeling.
    """

    def __init__(self):
        self.personality = ConversationPersonality()
        self.preferences = PreferenceLearner()
        self.emotion_model = EmotionModeler()
        self._bus = None
        logger.info("[INTERACTION] Human Interaction Intelligence initialized")

    def bind_event_bus(self):
        try:
            from core.event_bus import get_event_bus
            self._bus = get_event_bus()
            if self._bus:
                self._bus.subscribe("EMOTION_UPDATE", self._on_emotion_update)
                self._bus.subscribe("COMMAND_RUN", self._on_command)
                logger.info("[INTERACTION] Event bus bound")
        except Exception as e:
            logger.warning(f"[INTERACTION] Event bus binding failed: {e}")

    def _on_emotion_update(self, event):
        try:
            data = event.data if hasattr(event, 'data') else event
            emotion = data.get("emotion", "idle")
            self.emotion_model.update_from_event(emotion)
        except Exception as e:
            logger.error(f"[INTERACTION] Emotion handler error: {e}")

    def _on_command(self, event):
        try:
            data = event.data if hasattr(event, 'data') else event
            command = data.get("command", "")
            self.preferences.record_interaction(command)

            # Publish interaction insight
            if self._bus:
                insight = self.get_interaction_context()
                self._bus.publish_sync("INTERACTION_INSIGHT", "human_interaction", insight)
        except Exception as e:
            logger.error(f"[INTERACTION] Command handler error: {e}")

    def get_interaction_context(self) -> Dict[str, Any]:
        """Get full interaction context for brain enrichment."""
        return {
            "personality": self.personality.get_style_hints(),
            "emotion": self.emotion_model.get_emotional_context(),
            "preferred_topics": self.preferences.get_preferred_topics()[:5],
            "interaction_count": len(self.preferences.interaction_history),
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "interactions": len(self.preferences.interaction_history),
            "emotion_valence": round(self.emotion_model.current_valence, 3),
            "emotion_arousal": round(self.emotion_model.current_arousal, 3),
        }


_hii = None


def get_human_interaction() -> HumanInteractionIntelligence:
    global _hii
    if _hii is None:
        _hii = HumanInteractionIntelligence()
    return _hii


def start_human_interaction():
    hii = get_human_interaction()
    hii.bind_event_bus()
    print("[INTERACTION] Human Interaction Intelligence started", flush=True)
    return hii
