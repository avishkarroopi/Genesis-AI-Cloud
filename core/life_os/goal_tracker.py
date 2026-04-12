"""
Goal Tracker (Phase-2 User Intelligence)
Tracks personal goals in the Life OS.
"""

from core.event_bus import get_event_bus

def update_goal_progress(goal_id: str, progress: float):
    """Update goal and notify system."""
    bus = get_event_bus()
    bus.publish_sync("GOAL_PROGRESS_UPDATED", "life_os.goal_tracker", {"goal_id": goal_id, "progress": progress})
    bus.publish_sync("LIFE_OS_UPDATE", "life_os.goal_tracker", {"component": "goal_tracker", "status": "updated"})
    return True
