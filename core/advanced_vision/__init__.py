"""
GENESIS Phase-3 — Advanced Visual Intelligence Engine
Module 6: Object tracking, activity recognition, spatial reasoning, scene analysis.

Subscribes to: VISION_DETECTED, VISION_SCENE_CHANGED
Publishes: ACTIVITY_DETECTED, SPATIAL_UPDATE
Builds on existing yolo_detector.py and scene_memory.py (does NOT modify them).
"""

import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)


class ObjectTracker:
    """Persistent object tracking across vision frames."""

    def __init__(self):
        self.tracked_objects: Dict[str, Dict[str, Any]] = {}
        self._history: deque = deque(maxlen=1000)

    def update(self, detections: List[Dict[str, Any]]):
        """Update tracked objects from new detection frame."""
        current_ids = set()
        for det in detections:
            obj_id = det.get("label", "unknown") + "_" + str(det.get("id", 0))
            current_ids.add(obj_id)

            if obj_id in self.tracked_objects:
                prev = self.tracked_objects[obj_id]
                prev["last_seen"] = datetime.now().isoformat()
                prev["frame_count"] = prev.get("frame_count", 0) + 1
                prev["bbox"] = det.get("bbox", prev.get("bbox"))
                prev["confidence"] = det.get("confidence", prev.get("confidence", 0))
            else:
                self.tracked_objects[obj_id] = {
                    "label": det.get("label", "unknown"),
                    "first_seen": datetime.now().isoformat(),
                    "last_seen": datetime.now().isoformat(),
                    "frame_count": 1,
                    "bbox": det.get("bbox"),
                    "confidence": det.get("confidence", 0),
                }

            self._history.append({"obj_id": obj_id, "time": time.time(), "det": det})

        # Mark disappeared objects
        for obj_id in list(self.tracked_objects.keys()):
            if obj_id not in current_ids:
                self.tracked_objects[obj_id]["status"] = "disappeared"

    def get_persistent_objects(self, min_frames: int = 5) -> List[Dict]:
        """Get objects that have persisted for multiple frames."""
        return [
            obj for obj in self.tracked_objects.values()
            if obj.get("frame_count", 0) >= min_frames
        ]


class ActivityRecognizer:
    """Recognize human activities from detection patterns."""

    def __init__(self):
        self._activity_patterns = {
            "sitting": ["chair", "desk", "couch"],
            "eating": ["fork", "spoon", "bowl", "cup"],
            "working": ["laptop", "keyboard", "monitor"],
            "exercising": ["sports ball", "bicycle"],
            "reading": ["book"],
        }

    def recognize(self, detected_labels: List[str], person_present: bool) -> Optional[str]:
        """Infer activity from co-occurring objects."""
        if not person_present:
            return None

        label_set = set(l.lower() for l in detected_labels)
        for activity, indicators in self._activity_patterns.items():
            if any(ind in label_set for ind in indicators):
                return activity
        return "present" if person_present else None


class SpatialReasoner:
    """Infer spatial relationships between detected objects."""

    def infer_relationships(self, objects: List[Dict]) -> List[Dict]:
        """Determine spatial relationships from bounding boxes."""
        relationships = []
        for i, obj_a in enumerate(objects):
            for j, obj_b in enumerate(objects):
                if i >= j:
                    continue
                bbox_a = obj_a.get("bbox", [0, 0, 0, 0])
                bbox_b = obj_b.get("bbox", [0, 0, 0, 0])

                if len(bbox_a) >= 4 and len(bbox_b) >= 4:
                    rel = self._determine_relation(bbox_a, bbox_b)
                    if rel:
                        relationships.append({
                            "object_a": obj_a.get("label", "?"),
                            "object_b": obj_b.get("label", "?"),
                            "relation": rel,
                        })
        return relationships

    def _determine_relation(self, bbox_a, bbox_b) -> Optional[str]:
        """Determine spatial relation between two bounding boxes."""
        cx_a = (bbox_a[0] + bbox_a[2]) / 2
        cy_a = (bbox_a[1] + bbox_a[3]) / 2
        cx_b = (bbox_b[0] + bbox_b[2]) / 2
        cy_b = (bbox_b[1] + bbox_b[3]) / 2

        dx = cx_b - cx_a
        dy = cy_b - cy_a

        if abs(dx) > abs(dy):
            return "right_of" if dx > 0 else "left_of"
        else:
            return "below" if dy > 0 else "above"


class AdvancedVisionEngine:
    """Master controller for advanced visual intelligence."""

    def __init__(self):
        self.tracker = ObjectTracker()
        self.activity = ActivityRecognizer()
        self.spatial = SpatialReasoner()
        self._bus = None
        logger.info("[ADV_VISION] Engine initialized")

    def bind_event_bus(self):
        try:
            from core.event_bus import get_event_bus
            self._bus = get_event_bus()
            if self._bus:
                self._bus.subscribe("VISION_DETECTED", self._on_vision)
                self._bus.subscribe("VISION_SCENE_CHANGED", self._on_scene_change)
                logger.info("[ADV_VISION] Event bus bound")
        except Exception as e:
            logger.warning(f"[ADV_VISION] Event bus binding failed: {e}")

    def _on_vision(self, event):
        try:
            data = event.data if hasattr(event, 'data') else event
            detections = data.get("detections", [])
            if isinstance(data, dict) and "label" in data:
                detections = [data]

            self.tracker.update(detections)

            labels = [d.get("label", "") for d in detections]
            person_present = any("person" in l.lower() for l in labels)
            activity = self.activity.recognize(labels, person_present)

            if activity and self._bus:
                self._bus.publish_sync("ACTIVITY_DETECTED", "advanced_vision", {
                    "activity": activity,
                    "objects": labels,
                })

            # Spatial reasoning
            rels = self.spatial.infer_relationships(detections)
            if rels and self._bus:
                self._bus.publish_sync("SPATIAL_UPDATE", "advanced_vision", {
                    "relationships": rels,
                })
        except Exception as e:
            logger.error(f"[ADV_VISION] Vision handler error: {e}")

    def _on_scene_change(self, event):
        try:
            data = event.data if hasattr(event, 'data') else event
            logger.info(f"[ADV_VISION] Scene change: {data}")
        except Exception as e:
            logger.error(f"[ADV_VISION] Scene change handler error: {e}")

    def get_status(self) -> Dict[str, Any]:
        return {
            "tracked_objects": len(self.tracker.tracked_objects),
            "persistent_objects": len(self.tracker.get_persistent_objects()),
        }


_adv_vision = None


def get_advanced_vision() -> AdvancedVisionEngine:
    global _adv_vision
    if _adv_vision is None:
        _adv_vision = AdvancedVisionEngine()
    return _adv_vision


def start_advanced_vision():
    engine = get_advanced_vision()
    engine.bind_event_bus()
    print("[ADV_VISION] Advanced Visual Intelligence started", flush=True)
    return engine
