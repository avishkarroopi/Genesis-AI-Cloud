import logging
from core.event_bus import get_event_bus, EventPriority

logger = logging.getLogger(__name__)

async def _on_system_event(event):
    bus = get_event_bus()
    await bus.publish("system_metrics", "telemetry_collector", event.data, EventPriority.LOW)

async def _on_agent_event(event):
    bus = get_event_bus()
    await bus.publish("agent_metrics", "telemetry_collector", event.data, EventPriority.LOW)

async def _on_memory_event(event):
    bus = get_event_bus()
    await bus.publish("memory_metrics", "telemetry_collector", event.data, EventPriority.LOW)

def initialize_module():
    logger.info("Initializing Module 9: Observability & Debug Layer")
    bus = get_event_bus()
    bus.subscribe("system_event", _on_system_event)
    bus.subscribe("agent_event", _on_agent_event)
    bus.subscribe("memory_update", _on_memory_event)
