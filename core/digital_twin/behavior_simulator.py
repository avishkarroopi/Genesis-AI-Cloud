"""
Behavior Simulator (Phase-2 User Intelligence)
Simulates consequences of agent actions or user decisions.
Constraint 6: Digital Twin Execution Guard.
Must strictly trigger only via approved sources to avoid loops and overload.
"""

from core.event_bus import get_event_bus
import asyncio
import logging

logger = logging.getLogger(__name__)

ALLOWED_TRIGGERS = ["agent_planning", "prediction_event", "explicit_decision_analysis"]

async def run_simulation(trigger_source: str, context_data: dict):
    """
    Run simulation only if trigger is explicitly permitted.
    """
    if trigger_source not in ALLOWED_TRIGGERS:
        logger.warning(f"Digital Twin block: Simulation rejected for source '{trigger_source}'. Violation of Constraint 6.")
        return None
        
    logger.info(f"Digital Twin running simulation triggered by {trigger_source}")
    
    # Stub simulation logic
    outcome = {
        "simulated_action": context_data.get("proposed_action", "unknown"),
        "predicted_result": "favorable_outcome",
        "risk_level": "low"
    }
    
    event_bus = get_event_bus()
    await event_bus.publish(
        event_type="DIGITAL_TWIN_SIMULATION",
        source="digital_twin.behavior_simulator",
        data={"outcome": outcome, "trigger": trigger_source}
    )
    
    return outcome
