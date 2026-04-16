import logging
from core.event_bus import get_event_bus

logger = logging.getLogger(__name__)

class AgentCoordinator:
    def __init__(self):
        self.paused = False
        bus = get_event_bus()
        bus.subscribe("health_warning", self._on_health_warning)
        bus.subscribe("strategy_approved", self._on_strategy_approved)
        
    async def _on_health_warning(self, event):
        logger.warning(f"AgentCoordinator: Received health warning: {event.data}. Pausing non-essential queues.")
        self.paused = True
        
    async def _on_strategy_approved(self, event):
        if self.paused:
            logger.warning("AgentCoordinator: execution paused due to health limits. Postponing strategy.")
            return
        
        # Dispatch strategy if not paused
        goal = event.data.get("goal")
        logger.info(f"AgentCoordinator: Dispatching strategy for {goal}")
        
coordinator = AgentCoordinator()
