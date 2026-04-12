"""
Habit Engine (Phase-2 User Intelligence)
Tracks and builds user habits in the Life OS.
"""

from core.event_bus import get_event_bus

def record_habit_completion(habit_name: str):
    """Mark habit complete for the day."""
    bus = get_event_bus()
    bus.publish_sync("LIFE_OS_UPDATE", "life_os.habit_engine", {"habit": habit_name, "status": "completed"})
    return True
