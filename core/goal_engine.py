"""
GENESIS Goal Engine — Phase 6 Intelligence Integration.
Lightweight persistent goal tracking with planner integration.
Does NOT replace the existing planner — extends it with long-term goal awareness.
"""

import json
import os
import time
import threading
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from core.event_bus import get_event_bus

logger = logging.getLogger(__name__)

# Replaced local file storage with PostgreSQL for cloud statelessness
from core.db_pool import get_connection, release_connection


class Goal:
    """A single tracked goal."""

    def __init__(self, goal_id: str, description: str, priority: int = 5,
                 status: str = "pending", steps: List[str] = None,
                 created_at: str = None, updated_at: str = None,
                 progress: float = 0.0, metadata: Dict[str, Any] = None):
        self.goal_id = goal_id
        self.description = description
        self.priority = priority  # 1 (highest) to 10 (lowest)
        self.status = status  # pending, active, completed, failed, cancelled
        self.steps = steps or []
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()
        self.progress = progress  # 0.0 to 1.0
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "description": self.description,
            "priority": self.priority,
            "status": self.status,
            "steps": self.steps,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "progress": self.progress,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Goal":
        return cls(**data)


class GoalEngine:
    """Manages long-term goals with persistence and planner integration."""

    def __init__(self):
        self._goals: Dict[str, Goal] = {}
        self._lock = threading.Lock()
        self._counter = 0
        self._load_from_disk()
        logger.info("[GOAL] Goal engine initialized")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_goal(self, description: str, priority: int = 5,
                    metadata: Dict[str, Any] = None) -> Goal:
        """Create and persist a new goal."""
        with self._lock:
            self._counter += 1
            goal_id = f"goal_{self._counter}_{int(time.time())}"
            goal = Goal(goal_id=goal_id, description=description,
                        priority=priority, metadata=metadata)
            self._goals[goal_id] = goal
            self._save_to_db(goal)

        bus = get_event_bus()
        if bus:
            try:
                bus.publish_sync("GOAL_CREATED", "goal_engine", goal.to_dict())
            except Exception as e:
                logger.error(f"[GOAL] Event publish error: {e}")

        logger.info(f"[GOAL] Created: {goal_id} — {description}")
        return goal

    def update_goal_status(self, goal_id: str, status: str,
                           progress: float = None) -> Optional[Goal]:
        """Update goal status and optionally progress."""
        with self._lock:
            goal = self._goals.get(goal_id)
            if not goal:
                logger.warning(f"[GOAL] Goal not found: {goal_id}")
                return None
            goal.status = status
            if progress is not None:
                goal.progress = max(0.0, min(1.0, progress))
            goal.updated_at = datetime.now().isoformat()
            self._save_to_db(goal)

        bus = get_event_bus()
        if bus:
            try:
                # Determine event type based on status
                event_type = "GOAL_COMPLETED" if status == "completed" else "GOAL_UPDATED"
                bus.publish_sync(event_type, "goal_engine", goal.to_dict())
            except Exception as e:
                logger.error(f"[GOAL] Event publish error: {e}")

        logger.info(f"[GOAL] Updated {goal_id}: status={status}, progress={goal.progress}")
        return goal

    def schedule_goal_tasks(self, goal_id: str) -> Optional[Dict]:
        """Generate a plan for the goal using the existing planner."""
        with self._lock:
            goal = self._goals.get(goal_id)
        if not goal:
            return None

        try:
            from core.planner.planner import create_plan
            plan = create_plan(goal.description)
            steps = [s.get("description", str(s)) for s in plan.get("steps", [])]

            with self._lock:
                goal.steps = steps
                goal.status = "active"
                goal.updated_at = datetime.now().isoformat()
                self._save_to_db(goal)

            logger.info(f"[GOAL] Scheduled {len(steps)} tasks for {goal_id}")
            return plan
        except Exception as e:
            logger.error(f"[GOAL] Failed to schedule tasks: {e}")
            return None

    def evaluate_goal_progress(self, goal_id: str) -> Optional[Dict[str, Any]]:
        """Evaluate current progress of a goal."""
        with self._lock:
            goal = self._goals.get(goal_id)
        if not goal:
            return None

        total = len(goal.steps)
        report = {
            "goal_id": goal_id,
            "description": goal.description,
            "status": goal.status,
            "total_steps": total,
            "progress": goal.progress,
            "created_at": goal.created_at,
            "updated_at": goal.updated_at,
        }
        return report

    def get_active_goals(self) -> List[Dict[str, Any]]:
        """Return all active goals sorted by priority."""
        with self._lock:
            active = [g.to_dict() for g in self._goals.values()
                      if g.status in ("pending", "active")]
        active.sort(key=lambda g: g["priority"])
        return active

    def get_all_goals(self) -> List[Dict[str, Any]]:
        """Return all goals."""
        with self._lock:
            return [g.to_dict() for g in self._goals.values()]

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _save_to_db(self, goal: Goal):
        """Save a single goal to PostgreSQL (called under lock)."""
        conn = get_connection()
        if not conn:
            return
            
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS goals (
                        goal_id VARCHAR(255) PRIMARY KEY,
                        data JSONB NOT NULL
                    )
                """)
                cur.execute("""
                    INSERT INTO goals (goal_id, data)
                    VALUES (%s, %s)
                    ON CONFLICT (goal_id)
                    DO UPDATE SET data = %s
                """, (goal.goal_id, json.dumps(goal.to_dict()), json.dumps(goal.to_dict())))
            conn.commit()
        except Exception as e:
            logger.error(f"[GOAL] Failed to save goal to DB: {e}")
        finally:
            release_connection(conn)

    def _load_from_disk(self):
        """Migrated: Load goals from PostgreSQL upon boot."""
        conn = get_connection()
        if not conn:
            return
            
        try:
            with conn.cursor() as cur:
                # Ensure table exists first so we don't crash on select
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS goals (
                        goal_id VARCHAR(255) PRIMARY KEY,
                        data JSONB NOT NULL
                    )
                """)
                cur.execute("SELECT goal_id, data FROM goals")
                rows = cur.fetchall()
                
                for row in rows:
                    goal_id, gdata = row
                    self._goals[goal_id] = Goal.from_dict(gdata)
                    self._counter = max(self._counter, int(goal_id.split("_")[1]) if "_" in goal_id else 0)
                
                logger.info(f"[GOAL] Loaded {len(self._goals)} goals from DB")
        except Exception as e:
            logger.error(f"[GOAL] Failed to load goals from DB: {e}")
        finally:
            release_connection(conn)


# --------------- Module-level singleton ---------------
_goal_engine: Optional[GoalEngine] = None


def get_goal_engine() -> GoalEngine:
    global _goal_engine
    if _goal_engine is None:
        _goal_engine = GoalEngine()
    return _goal_engine
