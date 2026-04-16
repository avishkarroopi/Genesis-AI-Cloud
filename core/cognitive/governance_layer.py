import logging
from core.event_bus import get_event_bus, EventPriority

logger = logging.getLogger(__name__)

async def _on_strategic_decision(event):
    pass 
    
async def _on_simulation(event):
    outcome = event.data.get("outcome", {})
    risk = outcome.get("risk_level", "low")
    if risk == "high":
        logger.warning("Governance Layer: High risk detected in simulation. Blocking action.")
        bus = get_event_bus()
        await bus.publish("block_action", "governance_layer", data={"trigger": event.data.get("trigger")}, priority=EventPriority.CRITICAL)

def initialize_module():
    logger.info("Initializing Module 10C: Governance Layer")
    bus = get_event_bus()
    bus.subscribe("strategic_decision_pending", _on_strategic_decision)
    # Hook into Digital Twin simulations
    bus.subscribe("DIGITAL_TWIN_SIMULATION", _on_simulation)
