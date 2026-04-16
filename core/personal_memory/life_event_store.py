# GENESIS Phase-3 Cognitive Module

import logging
from core.memory.memory_store import add_memory_safe
from core.event_bus import get_event_bus

logger = logging.getLogger(__name__)

class LifeEventStore:
    def __init__(self):
        self.bus = get_event_bus()
        self.bus.subscribe("life_event_occurred", self._on_life_event)
        
    async def _on_life_event(self, event):
        data = event.data
        if "description" in data:
            success = add_memory_safe(
                text=data["description"], 
                metadata={"source": "life_event", "type": data.get("type", "general")},
                collection_name="genesis_life_events"
            )
            if success:
                logger.info("Life event stored in personal memory DB securely.")
            else:
                logger.warning("Life event storage failed (likely DB unavailable).")

    def evaluate(self, decision=None, *args, **kwargs):
        return decision
        
    def process(self, data=None, *args, **kwargs):
        return data

# Initialize singleton pattern
store = LifeEventStore()
