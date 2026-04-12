"""
Schedule Manager (Phase-2 User Intelligence)
Manages user calendar and routines in the Life OS.
"""

from core.event_bus import get_event_bus

def add_schedule_event(event_name: str, time_str: str):
    """Add new event to schedule."""
    bus = get_event_bus()
    bus.publish_sync("LIFE_OS_UPDATE", "life_os.schedule_manager", {"event": event_name, "time": time_str})
    return True
