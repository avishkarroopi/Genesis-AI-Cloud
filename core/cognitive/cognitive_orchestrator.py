import logging
from core.event_bus import get_event_bus
from core.planner.planner import create_steps

logger = logging.getLogger(__name__)

async def _on_perception(event):
    logger.info(f"Cognitive Orchestrator analyzing perception event: {event.data}")
    # Classify intention weight
    weight = 1.0 if event.data.get("urgent") else 0.5
    
    if event.data.get("requires_action"):
        goal = event.data.get("goal")
        if goal:
            logger.info(f"Generating task graph for goal: {goal} with weight {weight}")
            create_steps(goal)
            bus = get_event_bus()
            await bus.publish("plan_created", "cognitive_orchestrator", data={"goal": goal, "weight": weight})

async def _on_plan_created(event):
    logger.info(f"Cognitive Orchestrator dispatching plan to agent logic: {event.data}")
    # Send goal to agent worker queue
    from core.agents.goal_queue import get_goal_queue
    queue = get_goal_queue()
    queue.push(event.data.get("goal", "Empty Goal"))

async def _on_decision(event):
    logger.info(f"Cognitive Orchestrator handling decision routing: {event.data}")
    bus = get_event_bus()
    decision = event.data.get("decision")
    if decision:
        await bus.publish("decision_executed", "cognitive_orchestrator", data={"decision": decision})

def initialize_module():
    logger.info("Initializing Module 10A: Cognitive Orchestrator")
    bus = get_event_bus()
    bus.subscribe("perception_event", _on_perception)
    bus.subscribe("decision_event", _on_decision)
    bus.subscribe("plan_created", _on_plan_created)
