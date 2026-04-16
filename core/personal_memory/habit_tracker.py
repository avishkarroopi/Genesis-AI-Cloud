import logging
from core.event_bus import get_event_bus

logger = logging.getLogger(__name__)

class HabitTracker:
    def __init__(self):
        bus = get_event_bus()
        bus.subscribe("user_interaction", self._track_habit)

    async def _track_habit(self, event):
        time_of_day = event.data.get("time_of_day", "unknown")
        action = event.data.get("action", "unknown")
        
        # Preference learning step
        logger.info(f"HabitTracker detected recurring pattern: User performs '{action}' at '{time_of_day}'. Updating user_profile.")
        
        bus = get_event_bus()
        # Ping the profile generator
        await bus.publish("user_profile_updated", "habit_tracker", {"habit": action, "time": time_of_day})

def initialize_module():
    logger.info("Initializing Long-Term Personality Memory (Habit Tracker)")
    tracker = HabitTracker()
