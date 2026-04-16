"""
Behavior Simulator (Phase-2 User Intelligence)
Simulates consequences of agent actions or user decisions.
Constraint 6: Digital Twin Execution Guard.
Must strictly trigger only via approved sources to avoid loops and overload.
"""

from core.event_bus import get_event_bus
import asyncio
import logging
from core.memory.memory_store import add_memory_safe

logger = logging.getLogger(__name__)

ALLOWED_TRIGGERS = ["agent_planning", "prediction_event", "explicit_decision_analysis"]

async def run_simulation(trigger_source: str, context_data: dict):
    if trigger_source not in ALLOWED_TRIGGERS:
        logger.warning(f"Digital Twin block: Simulation rejected for source '{trigger_source}'. Violation of Constraint 6.")
        return None
        
    logger.info(f"Digital Twin running simulation triggered by {trigger_source}")
    
    proposed_action = context_data.get("proposed_action", "unknown")
    outcome = {
        "simulated_action": proposed_action,
        "predicted_result": "favorable_outcome",
        "risk_level": "low"
    }
    
    # Track decision simulated outcome
    add_memory_safe(
        text=f"Simulated behavior for {proposed_action} expecting favorable_outcome",
        metadata={"source": "digital_twin", "risk": outcome["risk_level"]}
    )
    
    event_bus = get_event_bus()
    await event_bus.publish(
        event_type="DIGITAL_TWIN_SIMULATION",
        source="digital_twin.behavior_simulator",
        data={"outcome": outcome, "trigger": trigger_source}
    )
    
    return outcome

def initialize_digital_twin():
    bus = get_event_bus()
    async def _on_decision_track(event):
        action = event.data.get("decision")
        if action:
            await run_simulation("explicit_decision_analysis", {"proposed_action": action})
    
    bus.subscribe("decision_executed", _on_decision_track)
    logger.info("Behavior Simulator hooked to decision_executed pipeline")
