"""
GENESIS Phase-3 — Predictive Environmental Intelligence
Module 8: Environment change prediction, movement prediction,
event anticipation, risk detection.

Subscribes to: VISION_SCENE_CHANGED, PREDICTION_GENERATED
Publishes: ENVIRONMENT_PREDICTION
Analysis-only per Constraint 5 — never modifies world_model directly.
"""

import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)


class EnvironmentPredictor:
    """Predict environmental changes from scene history."""

    def __init__(self):
        self._scene_history: deque = deque(maxlen=200)
        self._predictions: deque = deque(maxlen=50)

    def record_scene(self, scene_data: Dict):
        self._scene_history.append({
            "data": scene_data,
            "timestamp": time.time(),
        })

    def predict_changes(self) -> Optional[Dict[str, Any]]:
        """Analyze scene history to predict environmental changes."""
        if len(self._scene_history) < 3:
            return None

        recent = list(self._scene_history)[-5:]
        object_counts = [s["data"].get("active_objects", 0) for s in recent]

        trend = "stable"
        if all(object_counts[i] <= object_counts[i+1] for i in range(len(object_counts)-1)):
            trend = "increasing_activity"
        elif all(object_counts[i] >= object_counts[i+1] for i in range(len(object_counts)-1)):
            trend = "decreasing_activity"

        prediction = {
            "type": "environment_change",
            "trend": trend,
            "confidence": 0.6 if trend != "stable" else 0.3,
            "sample_size": len(recent),
            "predicted_at": datetime.now().isoformat(),
        }
        self._predictions.append(prediction)
        return prediction


class MovementPredictor:
    """Predict object/person movement trajectories."""

    def __init__(self):
        self._trajectories: Dict[str, List[Dict]] = {}

    def update_position(self, obj_id: str, position: Dict):
        if obj_id not in self._trajectories:
            self._trajectories[obj_id] = []
        self._trajectories[obj_id].append({
            "position": position,
            "timestamp": time.time(),
        })
        # Keep last 50 positions per object
        if len(self._trajectories[obj_id]) > 50:
            self._trajectories[obj_id] = self._trajectories[obj_id][-50:]

    def predict_next_position(self, obj_id: str) -> Optional[Dict]:
        """Simple linear extrapolation of next position."""
        traj = self._trajectories.get(obj_id, [])
        if len(traj) < 2:
            return None

        last = traj[-1]["position"]
        prev = traj[-2]["position"]
        dx = last.get("x", 0) - prev.get("x", 0)
        dy = last.get("y", 0) - prev.get("y", 0)

        return {
            "predicted_x": last.get("x", 0) + dx,
            "predicted_y": last.get("y", 0) + dy,
            "confidence": 0.5,
        }


class EventAnticipator:
    """Anticipate events based on environmental patterns."""

    def __init__(self):
        self._pattern_log: deque = deque(maxlen=100)

    def log_event(self, event_type: str, context: Dict = None):
        self._pattern_log.append({
            "type": event_type,
            "context": context or {},
            "timestamp": time.time(),
        })

    def anticipate(self) -> List[Dict]:
        """Return anticipated events based on recent patterns."""
        if len(self._pattern_log) < 5:
            return []

        # Simple frequency analysis
        type_counts: Dict[str, int] = {}
        for entry in self._pattern_log:
            t = entry["type"]
            type_counts[t] = type_counts.get(t, 0) + 1

        anticipated = []
        for event_type, count in type_counts.items():
            if count >= 3:
                anticipated.append({
                    "anticipated_event": event_type,
                    "likelihood": min(0.9, count / len(self._pattern_log)),
                })
        return anticipated


class PredictiveEnvironmentEngine:
    """Master controller for predictive environmental intelligence."""

    def __init__(self):
        self.env_predictor = EnvironmentPredictor()
        self.movement = MovementPredictor()
        self.anticipator = EventAnticipator()
        self._bus = None
        logger.info("[ENV_PREDICT] Engine initialized")

    def bind_event_bus(self):
        try:
            from core.event_bus import get_event_bus
            self._bus = get_event_bus()
            if self._bus:
                self._bus.subscribe("VISION_SCENE_CHANGED", self._on_scene_change)
                self._bus.subscribe("PREDICTION_GENERATED", self._on_prediction)
                logger.info("[ENV_PREDICT] Event bus bound")
        except Exception as e:
            logger.warning(f"[ENV_PREDICT] Event bus binding failed: {e}")

    def _on_scene_change(self, event):
        try:
            data = event.data if hasattr(event, 'data') else event
            self.env_predictor.record_scene(data)

            prediction = self.env_predictor.predict_changes()
            if prediction and prediction["confidence"] > 0.5 and self._bus:
                self._bus.publish_sync("ENVIRONMENT_PREDICTION", "environment_prediction",
                                        prediction)
        except Exception as e:
            logger.error(f"[ENV_PREDICT] Scene change handler error: {e}")

    def _on_prediction(self, event):
        try:
            data = event.data if hasattr(event, 'data') else event
            self.anticipator.log_event("prediction", data)
        except Exception as e:
            logger.error(f"[ENV_PREDICT] Prediction handler error: {e}")

    def get_status(self) -> Dict[str, Any]:
        return {
            "scene_samples": len(self.env_predictor._scene_history),
            "tracked_trajectories": len(self.movement._trajectories),
            "predictions": len(self.env_predictor._predictions),
        }


_env_engine = None


def get_environment_prediction() -> PredictiveEnvironmentEngine:
    global _env_engine
    if _env_engine is None:
        _env_engine = PredictiveEnvironmentEngine()
    return _env_engine


def start_environment_prediction():
    engine = get_environment_prediction()
    engine.bind_event_bus()
    print("[ENV_PREDICT] Predictive Environmental Intelligence started", flush=True)
    return engine
