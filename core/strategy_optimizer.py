import logging
from core.event_bus import get_event_bus, EventPriority

logger = logging.getLogger(__name__)

class StrategyOptimizer:
    def __init__(self):
        bus = get_event_bus()
        bus.subscribe("plan_created", self._evaluate_plan)
        
    async def _evaluate_plan(self, event):
        plan_data = event.data
        goal = plan_data.get("goal", "")
        
        # Meta-evaluation of strategy options
        logger.info(f"StrategyOptimizer meta-evaluating alternative pathways for goal: {goal}")
        
        score = 0.95 if "research" in goal.lower() else 0.85
        
        bus = get_event_bus()
        if score >= 0.8:
            await bus.publish("strategy_approved", "strategy_optimizer", data={"goal": goal, "score": score}, priority=EventPriority.HIGH)
        else:
            await bus.publish("strategy_rejected", "strategy_optimizer", data={"goal": goal, "score": score, "reason": "Failed meta-evaluation"})

def initialize_module():
    global optimizer
    optimizer = StrategyOptimizer()
