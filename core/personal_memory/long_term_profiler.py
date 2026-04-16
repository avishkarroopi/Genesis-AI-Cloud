import logging
from core.event_bus import get_event_bus
from core.memory.memory_store import add_memory_safe

logger = logging.getLogger(__name__)

class LongTermProfiler:
    def __init__(self):
        bus = get_event_bus()
        bus.subscribe("life_event_occurred", self._cluster_event)

    async def _cluster_event(self, event):
        details = event.data.get("description", "")
        # Behavioral grouping
        category = "behavioral_pattern" if "habit" in details.lower() else "contextual_cluster"
        logger.info(f"LongTermProfiler clustering memory into {category}: {details}")
        
        # Insert contextual memory cluster back into memory store internally
        add_memory_safe(
            text=f"Profile update: {details}",
            metadata={"source": "long_term_profiler", "category": category},
            collection_name="genesis_personal_profile"
        )
        
def initialize_module():
    logger.info("Initializing Long-Term Profiler")
    profiler = LongTermProfiler()
