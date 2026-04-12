"""
GENESIS Phase-3 — Executive Control Layer (Mission Manager)
Module 1: High-level goal supervision, mission prioritization,
agent coordination, and long-term objective management.

Subscribes to: GOAL_CREATED, GOAL_PROGRESS_UPDATED, TASK_COMPLETE, TASK_FAILED, PREDICTION_GENERATED
Publishes: MISSION_UPDATE, AGENT_DIRECTIVE
"""

import threading
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class MissionPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class MissionStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Mission:
    """A high-level mission representing a long-term objective."""
    mission_id: str
    title: str
    description: str
    priority: MissionPriority = MissionPriority.MEDIUM
    status: MissionStatus = MissionStatus.PENDING
    goals: List[str] = field(default_factory=list)
    progress: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "mission_id": self.mission_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status.value,
            "goals": self.goals,
            "progress": self.progress,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }


class MissionManager:
    """
    Executive control layer that supervises missions, coordinates agents,
    and converts prediction signals into actionable goals.
    """

    def __init__(self):
        self.missions: Dict[str, Mission] = {}
        self._lock = threading.Lock()
        self._bus = None
        logger.info("[EXECUTIVE] Mission Manager initialized")

    def bind_event_bus(self):
        """Subscribe to relevant events."""
        try:
            from core.event_bus import get_event_bus
            self._bus = get_event_bus()
            if self._bus:
                self._bus.subscribe("GOAL_CREATED", self._on_goal_created)
                self._bus.subscribe("GOAL_PROGRESS_UPDATED", self._on_goal_progress)
                self._bus.subscribe("TASK_COMPLETE", self._on_task_complete)
                self._bus.subscribe("TASK_FAILED", self._on_task_failed)
                self._bus.subscribe("PREDICTION_GENERATED", self._on_prediction)
                logger.info("[EXECUTIVE] Event bus bound — listening for goals, tasks, predictions")
        except Exception as e:
            logger.warning(f"[EXECUTIVE] Event bus binding failed: {e}")

    # ── Event Handlers ──

    def _on_goal_created(self, event):
        """When a new goal is created, evaluate whether it belongs to an existing mission."""
        try:
            data = event.data if hasattr(event, 'data') else event
            goal_id = data.get("goal_id", "unknown")
            description = data.get("description", "")
            logger.info(f"[EXECUTIVE] Goal created: {goal_id} — {description}")

            # Auto-assign to active mission if one exists
            with self._lock:
                for mission in self.missions.values():
                    if mission.status == MissionStatus.ACTIVE:
                        if goal_id not in mission.goals:
                            mission.goals.append(goal_id)
                            mission.updated_at = datetime.now()
                            self._publish_update(mission)
                        break
        except Exception as e:
            logger.error(f"[EXECUTIVE] Goal handler error: {e}")

    def _on_goal_progress(self, event):
        """Update mission progress based on goal progress."""
        try:
            data = event.data if hasattr(event, 'data') else event
            goal_id = data.get("goal_id", "")
            progress = data.get("progress", 0)

            with self._lock:
                for mission in self.missions.values():
                    if goal_id in mission.goals and mission.status == MissionStatus.ACTIVE:
                        # Recalculate mission progress as average of goal progress
                        total_goals = len(mission.goals)
                        if total_goals > 0:
                            mission.progress = min(1.0, mission.progress + (progress / total_goals))
                        mission.updated_at = datetime.now()

                        if mission.progress >= 1.0:
                            mission.status = MissionStatus.COMPLETED
                            logger.info(f"[EXECUTIVE] Mission COMPLETED: {mission.title}")

                        self._publish_update(mission)
                        break
        except Exception as e:
            logger.error(f"[EXECUTIVE] Progress handler error: {e}")

    def _on_task_complete(self, event):
        """Log task completion for mission tracking."""
        try:
            data = event.data if hasattr(event, 'data') else event
            logger.info(f"[EXECUTIVE] Task completed: {data}")
        except Exception as e:
            logger.error(f"[EXECUTIVE] Task complete handler error: {e}")

    def _on_task_failed(self, event):
        """Handle task failure — may require mission replanning."""
        try:
            data = event.data if hasattr(event, 'data') else event
            logger.warning(f"[EXECUTIVE] Task FAILED: {data}")
        except Exception as e:
            logger.error(f"[EXECUTIVE] Task failed handler error: {e}")

    def _on_prediction(self, event):
        """
        Convert prediction signals into potential missions.
        Flow: Prediction → Evaluate → Create/Update Mission
        """
        try:
            data = event.data if hasattr(event, 'data') else event
            prediction = data.get("prediction", {})
            analysis_type = prediction.get("analysis_type", "unknown")
            confidence = prediction.get("confidence", 0)

            logger.info(f"[EXECUTIVE] Prediction received: {analysis_type} (confidence={confidence})")

            # Only create missions from high-confidence predictions
            if confidence >= 0.7:
                mission_id = f"pred_{analysis_type}_{int(time.time())}"
                trend = prediction.get("predicted_trend", "unknown trend")
                self.create_mission(
                    mission_id=mission_id,
                    title=f"Prediction Response: {analysis_type}",
                    description=f"Auto-generated from prediction: {trend}",
                    priority=MissionPriority.MEDIUM,
                    metadata={"source": "prediction_engine", "prediction": prediction}
                )
        except Exception as e:
            logger.error(f"[EXECUTIVE] Prediction handler error: {e}")

    # ── Mission CRUD ──

    def create_mission(self, mission_id: str, title: str, description: str,
                       priority: MissionPriority = MissionPriority.MEDIUM,
                       metadata: Dict = None) -> Mission:
        """Create a new mission."""
        with self._lock:
            mission = Mission(
                mission_id=mission_id,
                title=title,
                description=description,
                priority=priority,
                metadata=metadata or {}
            )
            self.missions[mission_id] = mission
            logger.info(f"[EXECUTIVE] Mission created: {title} [{priority.value}]")
            self._publish_update(mission)
            return mission

    def activate_mission(self, mission_id: str) -> bool:
        """Activate a pending mission."""
        with self._lock:
            mission = self.missions.get(mission_id)
            if mission and mission.status == MissionStatus.PENDING:
                mission.status = MissionStatus.ACTIVE
                mission.updated_at = datetime.now()
                logger.info(f"[EXECUTIVE] Mission ACTIVATED: {mission.title}")
                self._publish_update(mission)
                return True
        return False

    def get_active_missions(self) -> List[Mission]:
        """Get all active missions."""
        with self._lock:
            return [m for m in self.missions.values() if m.status == MissionStatus.ACTIVE]

    def get_mission(self, mission_id: str) -> Optional[Mission]:
        """Get a specific mission."""
        return self.missions.get(mission_id)

    def get_status(self) -> Dict[str, Any]:
        """Get mission manager status."""
        with self._lock:
            return {
                "total_missions": len(self.missions),
                "active": len([m for m in self.missions.values() if m.status == MissionStatus.ACTIVE]),
                "completed": len([m for m in self.missions.values() if m.status == MissionStatus.COMPLETED]),
                "failed": len([m for m in self.missions.values() if m.status == MissionStatus.FAILED]),
            }

    def _publish_update(self, mission: Mission):
        """Publish mission update to event bus."""
        if self._bus:
            try:
                self._bus.publish_sync("MISSION_UPDATE", "executive_control", mission.to_dict())
            except Exception as e:
                logger.error(f"[EXECUTIVE] Publish error: {e}")


# ── Singleton ──

_mission_manager: Optional[MissionManager] = None
_mm_lock = threading.Lock()


def get_mission_manager() -> MissionManager:
    global _mission_manager
    if _mission_manager is None:
        with _mm_lock:
            if _mission_manager is None:
                _mission_manager = MissionManager()
    return _mission_manager


def start_executive_control():
    """Initialize and bind the mission manager."""
    mm = get_mission_manager()
    mm.bind_event_bus()
    print("[EXECUTIVE] Executive Control Layer started", flush=True)
    return mm
